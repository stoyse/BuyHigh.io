"""
Router für Benutzerbezogene Funktionalität.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
import os
import logging
import database.handler.postgres.postgre_transactions_handler as transactions_handler
import database.handler.postgres.postgres_db_handler as db_handler
from database.handler.postgres.postgres_db_handler import add_analytics
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import ProfilePictureUploadResponse, UserDataResponse, TransactionsListResponse, PortfolioResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Helper to get root path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@router.post("/upload/profile-picture", response_model=ProfilePictureUploadResponse)
async def api_upload_profile_picture(
    file: UploadFile = File(...), 
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    # Verwendung der Datenbank-User-ID anstelle der Firebase-ID
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_upload_profile_picture_attempt", "api_routes:api_upload_profile_picture")

    if not file:
        add_analytics(user_id_for_analytics, "api_upload_profile_picture_fail_no_file_part", "api_routes:api_upload_profile_picture")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file part in the request.")
    
    if file.filename == '':
        add_analytics(user_id_for_analytics, "api_upload_profile_picture_fail_no_selected_file", "api_routes:api_upload_profile_picture")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No selected file.")

    try:
        upload_folder = os.path.join(PROJECT_ROOT, 'static', 'user_data')
        # Verwendung der Datenbank-User-ID für den Ordnerpfad
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        file_path = os.path.join(user_folder, "profile_picture.png")
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        profile_pic_url_path = f"user_data/{current_user.id}/profile_picture.png"
        
        logger.info(f"User {current_user.id} profile picture path to be saved in DB: {profile_pic_url_path}")
        
        add_analytics(user_id_for_analytics, "api_upload_profile_picture_success", f"api_routes:api_upload_profile_picture,url={profile_pic_url_path}")
        logger.info(f"Profile picture uploaded successfully for user {current_user.id}")
        
        return ProfilePictureUploadResponse(
            success=True, 
            message="File uploaded successfully.", 
            url=f"/static/{profile_pic_url_path}"
        )
    
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}", exc_info=True)
        add_analytics(user_id_for_analytics, "api_upload_profile_picture_exception", f"api_routes:api_upload_profile_picture,error={e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error uploading file: {str(e)}")

@router.get("/get/profile-picture/{user_id_param}")
async def api_get_profile_picture(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    # Verwendung der Datenbank-User-ID für Analytics
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_profile_picture_attempt", f"api_routes:api_get_profile_picture:user_id={user_id_param}")
    
    file_path = os.path.join(PROJECT_ROOT, 'static', 'user_data', str(user_id_param), 'profile_picture.png')
    
    if os.path.exists(file_path):
        add_analytics(user_id_for_analytics, "api_get_profile_picture_success", f"api_routes:api_get_profile_picture:user_id={user_id_param}")
        return FileResponse(file_path)
    else:
        add_analytics(user_id_for_analytics, "api_get_profile_picture_fail_not_found", f"api_routes:api_get_profile_picture:user_id={user_id_param}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile picture not found.")

@router.get("/user/{user_id_param}", response_model=UserDataResponse)
async def api_get_user_data(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    # Verwendung der Datenbank-User-ID für Analytics
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_user_data_attempt", f"api_routes:api_get_user_data:user_id={user_id_param}")
    
    user_data = db_handler.get_user_by_id(user_id=user_id_param)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserDataResponse(success=True, user=user_data)

@router.get("/user/transactions/{user_id_param}", response_model=TransactionsListResponse)
async def api_get_user_last_transactions(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    # Verwendung der Datenbank-User-ID für Analytics
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_user_last_transactions_attempt", f"api_routes:api_get_user_last_transactions:user_id={user_id_param}")

    transactions = transactions_handler.get_recent_transactions(user_id=user_id_param)
    if transactions is not None:
        add_analytics(user_id_for_analytics, "api_get_user_last_transactions_success", f"api_routes:api_get_user_last_transactions:user_id={user_id_param}")
        return TransactionsListResponse(success=True, transactions=transactions)
    else:
        add_analytics(user_id_for_analytics, "api_get_user_last_transactions_fail", f"api_routes:api_get_user_last_transactions:user_id={user_id_param}")
        return TransactionsListResponse(success=False, message="No transactions found or error retrieving them.", transactions=[])

@router.get("/user/portfolio/{user_id_param}", response_model=PortfolioResponse)
async def api_get_portfolio(user_id_param: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    # Verwendung der Datenbank-User-ID für Analytics
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_portfolio", f"api_routes:api_get_portfolio:user_id={user_id_param}")

    portfolio_data = transactions_handler.show_user_portfolio(user_id_param)
    if portfolio_data and portfolio_data.get("success"):
        return portfolio_data
    else:
        message = (portfolio_data.get("message") if portfolio_data 
                  else "Failed to retrieve portfolio or portfolio is empty.")
        if portfolio_data:
            return portfolio_data 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
