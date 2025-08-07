from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserProfile(BaseModel):
    student_id: str = Field(..., description="Unique student identifier")
    name: str = Field(..., description="User's full name")
    favorite_foods: List[str] = Field(default=[], description="List of user's favorite foods/cuisines")
    dietary_preferences: List[str] = Field(default=[], description="List of dietary preferences/restrictions")

class UserProfileResponse(BaseModel):
    student_id: str
    name: str
    favorite_foods: List[str]
    dietary_preferences: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RecipeResponse(BaseModel):
    user_id: str
    recipe_name: str
    ingredients: List[str]
    instructions: List[str]
    cooking_time: str
    difficulty: str
    servings: int
    serving_size: str
    dietary_tags: List[str]
    nutritional_facts: dict
    image_prompt: str
    image_url: str
    conversation_id: str
    generated_at: datetime

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int

class UsersListResponse(BaseModel):
    users: List[UserProfileResponse]
    total_count: int

class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    user_id: str
    recipe_data: Dict[str, Any]
    timestamp: datetime
    type: str

class ConversationSummaryResponse(BaseModel):
    user_id: str
    total_conversations: int
    recent_conversations: List[Dict[str, Any]]
    popular_recipe_types: List[Dict[str, Any]] 