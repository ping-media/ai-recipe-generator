import pdfplumber
import PyPDF2
import re
from typing import List, Dict, Any, Optional
import logging
from .config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

class PDFRecipeProcessor:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise
    
    def parse_recipe_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse recipe information from extracted text using OpenAI"""
        try:
            prompt = f"""
            Extract recipe information from the following text and format it as JSON.
            If there are multiple recipes, return a JSON array. If there's only one recipe, return a JSON object.
            
            For multiple recipes, use this structure:
            [
                {{
                    "name": "Recipe name",
                    "ingredients": ["ingredient1", "ingredient2", ...],
                    "instructions": ["step1", "step2", ...],
                    "cuisine": "cuisine type",
                    "difficulty": "Easy/Medium/Hard",
                    "cooking_time": "time in minutes",
                    "servings": "number of servings",
                    "description": "brief description"
                }},
                ...
            ]
            
            For a single recipe, use this structure:
            {{
                "name": "Recipe name",
                "ingredients": ["ingredient1", "ingredient2", ...],
                "instructions": ["step1", "step2", ...],
                "cuisine": "cuisine type",
                "difficulty": "Easy/Medium/Hard",
                "cooking_time": "time in minutes",
                "servings": "number of servings",
                "description": "brief description"
            }}
            
            Text to parse:
            {text}
            
            Return only the JSON, no additional text.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a recipe parser. Extract recipe information and return it as JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content
            logger.info(f"Raw OpenAI response: {content}")
            
            # Try to find JSON in the response (both objects and arrays)
            json_match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
            if json_match:
                try:
                    import json
                    json_str = json_match.group()
                    parsed_data = json.loads(json_str)
                    
                    # Handle both single objects and arrays
                    if isinstance(parsed_data, list):
                        # If it's an array, return all items
                        if len(parsed_data) > 0:
                            return parsed_data
                        else:
                            raise ValueError("Empty array returned")
                    else:
                        # If it's a single object, return it as a list
                        return [parsed_data]
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    # Try to fix common JSON issues
                    fixed_json = json_match.group().replace('\n', ' ').replace('  ', ' ')
                    try:
                        parsed_data = json.loads(fixed_json)
                        if isinstance(parsed_data, list):
                            if len(parsed_data) > 0:
                                return parsed_data
                            else:
                                raise ValueError("Empty array returned")
                        else:
                            return [parsed_data]
                    except json.JSONDecodeError:
                        logger.error("Failed to fix JSON")
                        raise ValueError("Invalid JSON format in response")
            else:
                raise ValueError("Could not extract JSON from response")
                
        except Exception as e:
            logger.error(f"Error parsing recipe from text: {e}")
            raise
    
    def process_pdf_recipes(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Process PDF and extract multiple recipes"""
        try:
            text = self.extract_text_from_pdf(pdf_path)
            
            # Parse recipes from the entire text
            recipes = self.parse_recipe_from_text(text)
            
            # Add IDs to each recipe
            for i, recipe in enumerate(recipes):
                recipe["id"] = f"recipe_pdf_{i+1}"
            
            return recipes
            
        except Exception as e:
            logger.error(f"Error processing PDF recipes: {e}")
            raise
    
    def split_into_recipe_sections(self, text: str) -> List[str]:
        """Split text into individual recipe sections"""
        # Common recipe section indicators
        section_patterns = [
            r'(?i)(recipe|dish|meal).*?(?=\n\s*\n|\n\s*[A-Z]|\n\s*Recipe|\n\s*Dish|\n\s*Meal)',
            r'(?i)(ingredients|ingredient).*?(?=\n\s*\n|\n\s*[A-Z]|\n\s*Instructions|\n\s*Method)',
            r'(?i)(instructions|method|directions).*?(?=\n\s*\n|\n\s*[A-Z]|\n\s*Recipe|\n\s*Dish)'
        ]
        
        sections = []
        current_section = ""
        
        lines = text.split('\n')
        for line in lines:
            # Check if line indicates a new recipe
            if any(re.search(pattern, line) for pattern in section_patterns):
                if current_section.strip():
                    sections.append(current_section.strip())
                current_section = line
            else:
                current_section += "\n" + line
        
        # Add the last section
        if current_section.strip():
            sections.append(current_section.strip())
        
        # If no clear sections found, treat entire text as one recipe
        if not sections:
            sections = [text]
        
        return sections

# Create global processor instance
pdf_processor = PDFRecipeProcessor() 