from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from ..models import UserProfile, UserProfileResponse, UsersListResponse
from ..database import mongodb
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["users"])

@router.get("/", response_model=UsersListResponse)
async def get_all_users():
    """Get all user profiles"""
    try:
        users = mongodb.get_all_users()
        
        # Convert to UserProfileResponse objects with migration handling
        user_responses = []
        for user in users:
            # Handle migration from favorite_food to favorite_foods
            if 'favorite_food' in user and 'favorite_foods' not in user:
                user['favorite_foods'] = [user['favorite_food']]
                del user['favorite_food']
                # Update the user in database
                mongodb.create_or_update_user(user)
            
            # Ensure favorite_foods exists
            if 'favorite_foods' not in user:
                user['favorite_foods'] = []
            
            user_responses.append(UserProfileResponse(**user))
        
        return UsersListResponse(
            users=user_responses,
            total_count=len(user_responses)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving all users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user(user_id: str):
    """Get user profile by student_id"""
    try:
        user = mongodb.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with student_id {user_id} not found"
            )
        
        # Handle migration from favorite_food to favorite_foods
        if 'favorite_food' in user and 'favorite_foods' not in user:
            user['favorite_foods'] = [user['favorite_food']]
            del user['favorite_food']
            # Update the user in database
            mongodb.create_or_update_user(user)
        
        # Ensure favorite_foods exists
        if 'favorite_foods' not in user:
            user['favorite_foods'] = []
        
        return UserProfileResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/", response_model=UserProfileResponse)
async def create_or_update_user(user: UserProfile):
    """Create or update user profile"""
    try:
        # Convert Pydantic model to dict
        user_data = user.dict()
        
        # Handle migration from favorite_food to favorite_foods if needed
        if 'favorite_food' in user_data and 'favorite_foods' not in user_data:
            user_data['favorite_foods'] = [user_data['favorite_food']]
            del user_data['favorite_food']
        
        # Create or update user in MongoDB
        success = mongodb.create_or_update_user(user_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create/update user profile"
            )
        
        # Retrieve the updated user data
        updated_user = mongodb.get_user(user.student_id)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated user profile"
            )
        
        # Handle migration for retrieved user data
        if 'favorite_food' in updated_user and 'favorite_foods' not in updated_user:
            updated_user['favorite_foods'] = [updated_user['favorite_food']]
            del updated_user['favorite_food']
            mongodb.create_or_update_user(updated_user)
        
        # Ensure favorite_foods exists
        if 'favorite_foods' not in updated_user:
            updated_user['favorite_foods'] = []
        
        return UserProfileResponse(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 