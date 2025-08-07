from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status
from typing import List, Dict, Any
import logging
from ..models import RecipeResponse, ConversationHistoryResponse, ConversationSummaryResponse
from ..vector_store import vector_store
from ..pdf_processor import pdf_processor
from ..ai_service import ai_service
from ..database import mongodb
import tempfile
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recipe", tags=["recipes"])

#search recipes in vector store
@router.get("/search")
async def search_recipes(query: str, top_k: int = 5):
    """
    Search for recipes using semantic similarity
    """
    try:
        recipes = vector_store.search_similar_recipes(query, top_k)
        return {
            "query": query,
            "results": recipes,
            "total_found": len(recipes)
        }
    except Exception as e:
        logger.error(f"Error searching recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching recipes: {str(e)}")

#get all recipes from vector store
@router.get("/recipes")
async def get_all_recipes():
    """
    Get all recipes from Pinecone (limited to recent ones)
    """
    try:
        # This is a simplified version - in production you'd want pagination
        # For now, we'll search with a generic query to get some recipes
        recipes = vector_store.search_similar_recipes("recipe", 100)
        return {
            "recipes": recipes,
            "total": len(recipes)
        }
    except Exception as e:
        logger.error(f"Error getting recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving recipes: {str(e)}")

#generate recipe for user
@router.get("/{user_id}", response_model=RecipeResponse)
async def generate_recipe(user_id: str):
    """Generate personalized recipe for user"""
    try:
        # Step 1: Retrieve user profile from MongoDB
        user_profile = mongodb.get_user(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with student_id {user_id} not found"
            )
        
        # Step 2: Perform semantic search in Pinecone
        favorite_foods = user_profile.get('favorite_foods', [])
        if not favorite_foods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must have at least one favorite food specified"
            )
        
        # Search for similar recipes using the first favorite food (can be enhanced to use multiple)
        primary_favorite = favorite_foods[0]
        similar_recipes = vector_store.search_similar_recipes(primary_favorite, top_k=2)
        recipe_name = similar_recipes[0].get("name", "Unknown")

        # Log user's favorite recipe name (first favorite food)
        logger.info(f"User {user_id} favorite food name: {primary_favorite}")

        logger.info(f"Similar recipes found for user {user_id}: {recipe_name}")
        # return
        
        # Step 3: Generate personalized recipe using OpenAI
        recipe_data = ai_service.generate_recipe(user_profile, similar_recipes)
        logger.info(f"Recipe data keys: {list(recipe_data.keys())}")

        
        # Step 4: Store generated recipe in Pinecone vector database
        import time
        import uuid
        generated_recipe_id = f"generated_{user_id}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        # Prepare recipe data for vector storage - FIXED VERSION
        vector_recipe_data = {
            "name": recipe_data.get("recipe_name", "Generated Recipe"),
            "ingredients": recipe_data.get("ingredients", []),
            "instructions": recipe_data.get("instructions", []),
            "cuisine": "AI Generated",  # FIXED: Use string instead of list
            "difficulty": recipe_data.get("difficulty", "Medium"),
            "cooking_time": recipe_data.get("cooking_time", "30 minutes"),
            "servings": recipe_data.get("servings", 4),
            "description": f"AI-generated recipe for {user_id}",
            "generated_for_user": user_id,
            "generated_at": str(recipe_data.get("generated_at", "")),  # FIXED: Convert to string
            "conversation_id": recipe_data.get("conversation_id", ""),
            "dietary_tags": recipe_data.get("dietary_tags", []),  # ADDED: Include dietary tags
            "user_id": recipe_data.get("user_id", user_id)  # ADDED: Include user_id
        }
        
        # Store in vector database
        vector_store_success = vector_store.store_recipe(generated_recipe_id, vector_recipe_data)
        if vector_store_success:
            logger.info(f"Stored generated recipe {generated_recipe_id} in Pinecone")
        else:
            logger.warning(f"Failed to store generated recipe in Pinecone")
        
        # Step 5: Store conversation history in MongoDB
        conversation_id = mongodb.store_conversation_history(user_id, recipe_data)
        logger.info(f"Stored conversation with ID: {conversation_id}")
        
        # Step 6: Add conversation_id to response
        recipe_data["conversation_id"] = conversation_id
        
        # Step 7: Return structured response
        return RecipeResponse(**recipe_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recipe for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recipe"
        )

#get conversation history for user
@router.get("/{user_id}/history", response_model=List[ConversationHistoryResponse])
async def get_user_conversation_history(user_id: str, limit: int = 10):
    """Get conversation history for a user"""
    try:
        # Verify user exists
        user_profile = mongodb.get_user(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with student_id {user_id} not found"
            )
        
        # Get conversation history
        conversations = mongodb.get_conversation_history(user_id, limit)
        
        return conversations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation history for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )

#get conversation by id
@router.get("/conversation/{conversation_id}")
async def get_conversation_by_id(conversation_id: str):
    """Get a specific conversation by ID"""
    try:
        conversation = mongodb.get_conversation_by_id(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation with ID {conversation_id} not found"
            )
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )

#get summary of user's conversation history
@router.get("/{user_id}/summary", response_model=ConversationSummaryResponse)
async def get_user_conversations_summary(user_id: str):
    """Get summary of user's conversation history"""
    try:
        # Verify user exists
        user_profile = mongodb.get_user(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with student_id {user_id} not found"
            )
        
        # Get conversation summary
        summary = mongodb.get_user_conversations_summary(user_id)
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation summary for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation summary"
        )

#upload pdf recipes to vector store
@router.post("/upload-pdf-recipes")
async def upload_pdf_recipes(file: UploadFile = File(...)):
    """
    Upload recipes from a PDF file to Pinecone database
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Write uploaded file to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Process PDF and extract recipes
            recipes = pdf_processor.process_pdf_recipes(temp_file_path)
            
            if not recipes:
                raise HTTPException(status_code=400, detail="No recipes found in PDF")
            
            # Upload recipes to Pinecone
            uploaded_recipes = []
            for i, recipe in enumerate(recipes):
                # Generate unique ID for each recipe
                import time
                import uuid
                unique_id = f"recipe_pdf_{int(time.time())}_{i}_{str(uuid.uuid4())[:8]}"
                
                success = vector_store.store_recipe(unique_id, recipe)
                
                if success:
                    uploaded_recipes.append({
                        "id": unique_id,
                        "name": recipe.get("name", "Unknown"),
                        "status": "uploaded"
                    })
                else:
                    uploaded_recipes.append({
                        "id": unique_id,
                        "name": recipe.get("name", "Unknown"),
                        "status": "failed"
                    })
            
            return {
                "message": f"Processed {len(recipes)} recipes from PDF",
                "uploaded_recipes": uploaded_recipes,
                "total_uploaded": len([r for r in uploaded_recipes if r["status"] == "uploaded"])
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error uploading PDF recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}") 