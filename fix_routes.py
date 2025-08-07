#!/usr/bin/env python3
"""
Script to fix the routes file by replacing the problematic vector_recipe_data section
"""

def fix_routes_file():
    """Fix the routes file by replacing the problematic vector_recipe_data section"""
    
    # Read the current routes file
    with open('app/routes/recipes.py', 'r') as f:
        content = f.read()
    
    # Define the problematic section to replace
    old_section = '''        # Prepare recipe data for vector storage
        vector_recipe_data = {
            "name": recipe_data.get("recipe_name", "Generated Recipe"),
            "ingredients": recipe_data.get("ingredients", []),
            "instructions": recipe_data.get("instructions", []),
            "cuisine": recipe_data.get("dietary_tags", []),  # Use dietary tags as cuisine hint
            "difficulty": recipe_data.get("difficulty", "Medium"),
            "cooking_time": recipe_data.get("cooking_time", "30 minutes"),
            "servings": recipe_data.get("servings", 4),
            "description": f"AI-generated recipe for {user_id}",
            "generated_for_user": user_id,
            "generated_at": recipe_data.get("generated_at", ""),
            "conversation_id": recipe_data.get("conversation_id", "")
        }'''
    
    # Define the fixed section
    new_section = '''        # Prepare recipe data for vector storage - FIXED VERSION
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
        }'''
    
    # Replace the old section with the new one
    if old_section in content:
        content = content.replace(old_section, new_section)
        print("✅ Fixed the vector_recipe_data section")
    else:
        print("❌ Could not find the problematic section to replace")
        return False
    
    # Write the fixed content back to the file
    with open('app/routes/recipes.py', 'w') as f:
        f.write(content)
    
    print("✅ Successfully updated app/routes/recipes.py")
    return True

if __name__ == "__main__":
    fix_routes_file() 