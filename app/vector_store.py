from pinecone import Pinecone
from openai import OpenAI
from typing import List, Dict, Any, Optional
import json
import logging
from .config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.pc = None
        self.index = None
        self.openai_client = None
        self.connect()
    
    def connect(self):
        """Initialize Pinecone and OpenAI clients"""
        try:
            # Initialize Pinecone with new API
            if not settings.PINECONE_API_KEY:
                raise ValueError("PINECONE_API_KEY not configured")
            
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Get or create index
            try:
                self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
                logger.info(f"Connected to existing Pinecone index: {settings.PINECONE_INDEX_NAME}")
            except Exception:
                # Index doesn't exist, create it
                self.pc.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine"
                )
                logger.info(f"Created Pinecone index: {settings.PINECONE_INDEX_NAME}")
                self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
            
            # Initialize OpenAI client
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            logger.info("Successfully connected to Pinecone and OpenAI")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def store_recipe(self, recipe_id: str, recipe_data: Dict[str, Any]) -> bool:
        """Store recipe in Pinecone with embeddings"""
        try:
            # Create text representation of recipe
            recipe_text = f"{recipe_data.get('name', '')} {recipe_data.get('ingredients', [])} {recipe_data.get('instructions', [])}"
            
            # Generate embedding
            embedding = self.get_embedding(recipe_text)
            
            # Generate unique ID to avoid conflicts
            import time
            import uuid
            unique_id = f"{recipe_id}_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            
            # Store in Pinecone using new API
            self.index.upsert(
                vectors=[{
                    "id": unique_id,
                    "values": embedding,
                    "metadata": recipe_data
                }]
            )
            
            logger.info(f"Stored recipe {unique_id} in Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Error storing recipe {recipe_id}: {e}")
            return False
    
    def search_similar_recipes(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Search for similar recipes using semantic similarity"""
        try:
            # Generate embedding for query
            query_embedding = self.get_embedding(query)
            
            # Search in Pinecone using new API
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Extract and return results
            recipes = []
            for match in results.matches:
                recipes.append({
                    "id": match.id,
                    "score": match.score,
                    "name": match.metadata.get('name', 'Unknown'),
                    "metadata": match.metadata
                })
            
            # logger.info(f"Found {len(recipes)} similar recipes for query: {query}")
            return recipes
            
        except Exception as e:
            logger.error(f"Error searching recipes: {e}")
            return []
    
    def delete_recipes_by_name(self, recipe_name: str) -> int:
        """Delete all recipes with the specified name from Pinecone"""
        try:
            # First, we need to find all recipes with this name
            # Since Pinecone doesn't support direct metadata filtering in queries,
            # we'll use a semantic search with the recipe name to find matches
            query_embedding = self.get_embedding(recipe_name)
            
            # Search for recipes with a high top_k to get more results
            results = self.index.query(
                vector=query_embedding,
                top_k=100,  # High number to get all potential matches
                include_metadata=True
            )
            
            # Filter results to find exact name matches
            recipes_to_delete = []
            for match in results.matches:
                if match.metadata.get('name', '').lower() == recipe_name.lower():
                    recipes_to_delete.append(match.id)
            
            if not recipes_to_delete:
                logger.info(f"No recipes found with name: {recipe_name}")
                return 0
            
            # Delete the recipes from Pinecone
            self.index.delete(ids=recipes_to_delete)
            
            logger.info(f"Deleted {len(recipes_to_delete)} recipes with name: {recipe_name}")
            return len(recipes_to_delete)
            
        except Exception as e:
            logger.error(f"Error deleting recipes with name {recipe_name}: {e}")
            return 0
    
    def initialize_sample_data(self):
        """Initialize Pinecone with sample recipe data"""
        sample_recipes = [
            {
                "id": "recipe_1",
                "name": "Spaghetti Carbonara",
                "ingredients": ["spaghetti", "eggs", "pecorino cheese", "guanciale", "black pepper"],
                "instructions": ["Boil pasta", "Cook guanciale", "Mix with eggs and cheese"],
                "cuisine": "Italian",
                "difficulty": "Medium",
                "cooking_time": "20 minutes"
            },
            {
                "id": "recipe_2", 
                "name": "Chicken Tikka Masala",
                "ingredients": ["chicken", "yogurt", "spices", "tomato sauce", "cream"],
                "instructions": ["Marinate chicken", "Grill chicken", "Make sauce", "Combine"],
                "cuisine": "Indian",
                "difficulty": "Medium",
                "cooking_time": "45 minutes"
            },
            {
                "id": "recipe_3",
                "name": "Caesar Salad",
                "ingredients": ["romaine lettuce", "parmesan cheese", "croutons", "caesar dressing"],
                "instructions": ["Wash lettuce", "Make dressing", "Toss ingredients"],
                "cuisine": "American",
                "difficulty": "Easy",
                "cooking_time": "10 minutes"
            }
        ]
        
        for recipe in sample_recipes:
            self.store_recipe(recipe["id"], recipe)
        
        logger.info("Initialized Pinecone with sample recipe data")

# Create global vector store instance
vector_store = VectorStore() 