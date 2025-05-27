"""
Router for user-related functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
import os
import logging
from typing import List, Optional

import database.handler.postgres.postgre_transactions_handler as transactions_handler
import database.handler.postgres.postgres_db_handler as db_handler
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import ProfilePictureUploadResponse, UserDataResponse, TransactionsListResponse, PortfolioResponse, BasicUser, AllUsersResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Helper to get root path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@router.post("/upload/profile-picture", response_model=ProfilePictureUploadResponse)
async def api_upload_profile_picture(
    file: UploadFile = File(...), 
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file part in the request.")
    
    if file.filename == '':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No selected file.")

    try:
        upload_folder = os.path.join(PROJECT_ROOT, 'static', 'user_data')
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        file_path = os.path.join(user_folder, "profile_picture.png")
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        profile_pic_url_path = f"user_data/{current_user.id}/profile_picture.png"
        
        logger.info(f"User {current_user.id} profile picture path to be saved in DB: {profile_pic_url_path}")
        
        logger.info(f"Profile picture uploaded successfully for user {current_user.id}")
        
        return ProfilePictureUploadResponse(
            success=True, 
            message="File uploaded successfully.", 
            url=f"/static/{profile_pic_url_path}"
        )
    
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error uploading file: {str(e)}")

@router.get("/get/profile-picture/{user_id_param}")
async def api_get_profile_picture(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    file_path = os.path.join(PROJECT_ROOT, 'static', 'user_data', str(user_id_param), 'profile_picture.png')
    
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile picture not found.")

@router.get("/user/{user_id_param}", response_model=UserDataResponse)
async def api_get_user_data(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    user_data = db_handler.get_user_by_id(user_id=user_id_param)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserDataResponse(success=True, user=user_data)

@router.get("/user/transactions/{user_id_param}", response_model=TransactionsListResponse)
async def api_get_user_last_transactions(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    result = transactions_handler.get_recent_transactions(user_id=user_id_param)
    if result and result.get("success"):
        transactions_list = result.get("transactions", [])
        return TransactionsListResponse(success=True, transactions=transactions_list)
    else:
        message = result.get("message", "No transactions found or error retrieving them.") if result else "Error retrieving transactions."
        return TransactionsListResponse(success=False, message=message, transactions=[])

@router.get("/user/portfolio/{user_id_param}", response_model=PortfolioResponse)
async def api_get_portfolio(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    portfolio_data = transactions_handler.show_user_portfolio(user_id_param)
    if portfolio_data and portfolio_data.get("success"):
        return portfolio_data
    else:
        message = (portfolio_data.get("message") if portfolio_data 
                  else "Failed to retrieve portfolio or portfolio is empty.")
        if portfolio_data:
            return portfolio_data 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

@router.get("/users/all", response_model=AllUsersResponse)
async def api_get_all_users(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Retrieves a list of all users with basic information.
    """
    try:
        users_data = db_handler.get_all_profiles() 
        
        if users_data is None:
            logger.warning("No users found or error in fetching from DB.")
            return AllUsersResponse(success=True, users=[], message="No users found.")

        return AllUsersResponse(success=True, users=users_data)
    except Exception as e:
        logger.error(f"Error retrieving all users: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error retrieving users: {str(e)}")
