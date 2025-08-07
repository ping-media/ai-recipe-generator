#!/usr/bin/env python3
"""
Debug script to test vector store functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.vector_store import vector_store
from app.ai_service import ai_service
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_vector_store():
    """Test vector store functionality"""
    try:
        # Test 1: Store a simple recipe
        print("=== Test 1: Store simple recipe ===")
        test_recipe = {
            "name": "Test Recipe",
            "ingredients": ["test ingredient"],
            "instructions": ["test instruction"],
            "cuisine": "Test Cuisine",
            "difficulty": "Easy",
            "cooking_time": "10 minutes"
        }
        
        success = vector_store.store_recipe("test_recipe_1", test_recipe)
        print(f"Store success: {success}")
        
        # Test 2: Store a recipe with problematic data (like the current issue)
        print("\n=== Test 2: Store recipe with problematic data ===")
        problematic_recipe = {
            "name": "Problematic Recipe",
            "ingredients": ["ingredient1", "ingredient2"],
            "instructions": ["step1", "step2"],
            "cuisine": ["vegetarian", "gluten-free"],  # This is a list - problematic!
            "difficulty": "Medium",
            "cooking_time": "30 minutes",
            "generated_at": "2025-08-03T16:52:33.265345"  # This is a string
        }
        
        success = vector_store.store_recipe("test_recipe_2", problematic_recipe)
        print(f"Store success: {success}")
        
        # Test 3: Search for recipes
        print("\n=== Test 3: Search for recipes ===")
        results = vector_store.search_similar_recipes("test", 5)
        print(f"Found {len(results)} recipes")
        for result in results:
            print(f"  - {result['metadata'].get('name', 'Unknown')} (score: {result['score']:.3f})")
            
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vector_store() 