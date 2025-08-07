from openai import OpenAI
from typing import List, Dict, Any
from datetime import datetime
import logging
import random
from .config import settings

logger = logging.getLogger(__name__)

class AIService:
    #AI Service class for generating personalized recipes using OpenAI GPT.Handles recipe generation, parsing, and fallback mechanisms.
    
    def __init__(self):
        #Initialize the AI service with OpenAI client. Sets up the OpenAI client using API key from settings.

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_recipe(self, user_profile: Dict[str, Any], similar_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        #Generate a personalized recipe using OpenAI GPT based on user preferences and similar recipes.
        
        #Args: user_profile (Dict[str, Any]): User's profile containing preferences, dietary restrictions, etc.
        #similar_recipes (List[Dict[str, Any]]): List of similar recipes for inspiration
            
        #Returns: Dict[str, Any]: Generated recipe with all required fields including image_prompt
            
        #Raises: Exception: If recipe generation fails, returns fallback recipe
        
        try:
            # Create context from user profile and similar recipes
            context = self._create_context(user_profile, similar_recipes)
            
            # Log the final prompt being sent to OpenAI
            final_prompt = f"Generate a personalized recipe based on this context: {context}"
            logger.info(f"Final prompt sent to OpenAI: {final_prompt}")
            
            # Generate recipe using OpenAI GPT model
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional chef and recipe creator with extensive culinary expertise. Generate personalized recipes based on user preferences and similar recipes.

IMPORTANT: You must return a valid JSON object with ALL the following fields:
{
    "recipe_name": "Simple descriptive name",
    "ingredients": ["ingredient1", "ingredient2", ...],
    "instructions": ["step1", "step2", ...],
    "cooking_time": "X minutes",
    "difficulty": "Easy/Medium/Hard",
    "servings": 4,
    "serving_size": "1 cup/200g/1 piece",
    "dietary_tags": ["vegetarian", "gluten-free", etc.],
    "nutritional_facts": {
        "calories": 350,
        "protein": "15g",
        "carbohydrates": "45g",
        "fat": "12g",
        "fiber": "8g",
        "sugar": "5g",
        "sodium": "400mg"
    },
    "image_prompt": "Detailed visual description for generating recipe image - describe the final dish appearance, plating, colors, and presentation"
}

Guidelines for better recipe creation:
- Consider user's dietary preferences and restrictions
- Use ingredients that complement the user's favorite foods
- Create balanced, nutritious recipes with proper macro distribution
- Provide clear, step-by-step instructions
- Ensure cooking time is realistic
- Make the image_prompt detailed and appetizing
- Consider seasonal ingredients and cooking techniques
- Adapt recipes based on similar recipe inspirations provided
- Calculate accurate nutritional facts per serving
- Specify clear serving size (e.g., "1 cup", "200g", "1 piece")
- Ensure nutritional facts are realistic and balanced
- Consider dietary restrictions when calculating macros"""
                    },
                    {
                        "role": "user",
                        "content": f"Generate a personalized recipe based on this context: {context}"
                    }
                ],
                temperature=0.8,  # Slightly higher creativity for better recipe variety
                max_tokens=1500   # More tokens for detailed recipes and instructions
            )
            
            # Parse the response
            recipe_text = response.choices[0].message.content
            recipe_data = self._parse_recipe_response(recipe_text)
            
            # Generate image URL using the image prompt
            image_prompt = recipe_data.get("image_prompt", "")
            # image_url = self._generate_recipe_image(image_prompt)
            image_url = ""
            
            # Add the generated image URL only if it's not empty
            if image_url:
                recipe_data["image_url"] = image_url
            else:
                recipe_data["image_url"] = ""
            
            # Add metadata
            recipe_data["user_id"] = user_profile["student_id"]
            recipe_data["generated_at"] = datetime.utcnow()
            
            return recipe_data
            
        except Exception as e:
            return self._get_fallback_recipe(user_profile)
    
    def _create_context(self, user_profile: Dict[str, Any], similar_recipes: List[Dict[str, Any]]) -> str:
        """Create context string for recipe generation"""
        context_parts = []
        
        # User preferences - extract only one favorite food and dietary preferences
        favorite_foods = user_profile.get('favorite_foods', [])
        if favorite_foods:
            # Randomly select one favorite food item for recipe generation
            primary_food = random.choice(favorite_foods)
            context_parts.append(f"User's primary favorite food: {primary_food}")
        else:
            context_parts.append("User's favorite foods: Not specified")
        
        if user_profile.get('dietary_preferences'):
            context_parts.append(f"Dietary preferences: {', '.join(user_profile['dietary_preferences'])}")
        
        # Similar recipes for inspiration - only include highly relevant ones
        if similar_recipes:
            relevant_recipes = []
            for recipe in similar_recipes:
                score = recipe.get('score', 0)
                # Only include recipes with high similarity score (>0.8)
                if score > 0.8:
                    recipe_info = recipe.get('metadata', {})
                    relevant_recipes.append(f"{recipe_info.get('name', 'Unknown')} - {recipe_info.get('cuisine', 'Unknown cuisine')}")
            
            if relevant_recipes:
                context_parts.append("Similar recipes for inspiration:")
                # Only include the most relevant recipe
                context_parts.append(f"1. {relevant_recipes[0]}")
            else:
                context_parts.append("No highly relevant recipes found for inspiration.")
        
        return "\n".join(context_parts)
    
    def _generate_recipe_image(self, image_prompt: str) -> str:
        """
        Generate an image URL using OpenAI's DALL-E model based on the image prompt.
        
        Args:
            image_prompt (str): Detailed description of the dish to generate
            
        Returns:
            str: URL of the generated image, or empty string if generation fails
        """
        try:
            # Generate image using DALL-E
            response = self.client.images.generate(
                model="dall-e-3",  # Use DALL-E 3 for high quality images
                prompt=image_prompt,
                size="1024x1024",  # Standard size for recipe images
                quality="standard",
                n=1  # Generate one image
            )
            
            # Extract the image URL from the response
            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                return image_url
            else:
                return ""
            
        except Exception as e:
            return ""  # Return empty string if image generation fails
    
    def _parse_recipe_response(self, response_text: str) -> Dict[str, Any]:
        """Parse OpenAI response into structured recipe data"""
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Find JSON-like content
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                recipe_json = json.loads(json_match.group())
                
                # Ensure image_prompt is present
                if 'image_prompt' not in recipe_json:
                    recipe_name = recipe_json.get('recipe_name', 'Recipe')
                    recipe_json['image_prompt'] = f"A delicious {recipe_name.lower()} served on a plate with garnishes"
                
                # Ensure serving_size is present
                if 'serving_size' not in recipe_json:
                    recipe_json['serving_size'] = "1 serving"
                
                # Ensure nutritional_facts is present
                if 'nutritional_facts' not in recipe_json:
                    recipe_json['nutritional_facts'] = {
                        "calories": 300,
                        "protein": "10g",
                        "carbohydrates": "40g",
                        "fat": "10g",
                        "fiber": "5g",
                        "sugar": "3g",
                        "sodium": "300mg"
                    }
                
                return recipe_json
            else:
                # Fallback parsing
                return self._fallback_parse(response_text)
                
        except Exception as e:
            return self._get_default_recipe()
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON responses"""
        # Simple parsing for common patterns
        lines = text.split('\n')
        recipe_data = {
            "recipe_name": "Simple Recipe",
            "ingredients": [],
            "instructions": [],
            "cooking_time": "30 minutes",
            "difficulty": "Medium",
            "servings": 4,
            "serving_size": "1 serving",
            "dietary_tags": [],
            "nutritional_facts": {
                "calories": 300,
                "protein": "10g",
                "carbohydrates": "40g",
                "fat": "10g",
                "fiber": "5g",
                "sugar": "3g",
                "sodium": "300mg"
            },
            "image_prompt": "A delicious homemade dish served on a plate"
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith("Ingredients:"):
                # Parse ingredients
                pass
            elif line.startswith("Instructions:"):
                # Parse instructions
                pass
            elif "ingredients" in line.lower():
                # Extract ingredients
                pass
        
        return recipe_data
    
    def _get_fallback_recipe(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback recipe when AI generation fails"""
        # Generate fallback recipe structure
        favorite_foods = user_profile.get('favorite_foods', [])
        primary_food = random.choice(favorite_foods) if favorite_foods else 'Recipe'
        
        fallback_recipe = {
            "recipe_name": f"Simple {primary_food}",
            "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
            "instructions": [
                "Step 1: Prepare ingredients",
                "Step 2: Cook according to preference",
                "Step 3: Serve and enjoy"
            ],
            "cooking_time": "30 minutes",
            "difficulty": "Medium",
            "servings": 4,
            "serving_size": "1 serving",
            "dietary_tags": user_profile.get('dietary_preferences', []),
            "nutritional_facts": {
                "calories": 350,
                "protein": "12g",
                "carbohydrates": "45g",
                "fat": "12g",
                "fiber": "6g",
                "sugar": "4g",
                "sodium": "350mg"
            },
            "image_prompt": f"A delicious {primary_food} served on a plate",
            "user_id": user_profile["student_id"],
            "generated_at": datetime.utcnow()
        }
        
        # Try to generate image for fallback recipe
        try:
            image_url = self._generate_recipe_image(fallback_recipe["image_prompt"])
            fallback_recipe["image_url"] = image_url
        except Exception as e:
            fallback_recipe["image_url"] = ""
        
        return fallback_recipe
    
    def _get_default_recipe(self) -> Dict[str, Any]:
        """Get a default recipe structure"""
        # Generate default recipe structure
        default_recipe = {
            "recipe_name": "Simple Pasta",
            "ingredients": ["pasta", "olive oil", "garlic", "herbs", "salt"],
            "instructions": [
                "Boil pasta according to package instructions",
                "Heat olive oil in a pan",
                "Add garlic and herbs",
                "Combine with pasta and serve"
            ],
            "cooking_time": "20 minutes",
            "difficulty": "Easy",
            "servings": 2,
            "serving_size": "1 cup",
            "dietary_tags": ["vegetarian"],
            "nutritional_facts": {
                "calories": 320,
                "protein": "8g",
                "carbohydrates": "55g",
                "fat": "8g",
                "fiber": "3g",
                "sugar": "2g",
                "sodium": "250mg"
            },
            "image_prompt": "A simple pasta dish with olive oil, garlic, and herbs served on a white plate",
            "generated_at": datetime.utcnow()
        }
        
        # Try to generate image for default recipe
        try:
            image_url = self._generate_recipe_image(default_recipe["image_prompt"])
            default_recipe["image_url"] = image_url
        except Exception as e:
            default_recipe["image_url"] = ""
        
        return default_recipe

# Create global AI service instance
ai_service = AIService() 