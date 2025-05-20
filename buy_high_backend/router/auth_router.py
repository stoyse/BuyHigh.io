"""
Router für Authentifizierungsfunktionen.
"""

from fastapi import APIRouter, HTTPException, status
import logging
import utils.auth as auth_module
import database.handler.postgres.postgres_db_handler as db_handler
from ..pydantic_models import LoginRequest

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login")
async def api_login(login_data: LoginRequest):
    """API-Route für die Benutzeranmeldung"""
    logger.info(f"Login attempt for email: {login_data.email}")
    try:
        firebase_uid, id_token = auth_module.login_firebase_user_rest(login_data.email, login_data.password)
        logger.info(f"Firebase authentication successful for email: {login_data.email}, UID: {firebase_uid}")

        if not firebase_uid or not id_token:
            logger.warning(f"Firebase authentication returned empty UID or token for email: {login_data.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
        if not local_user:
            logger.info(f"No local user found with Firebase UID: {firebase_uid}, checking by email")
            local_user = db_handler.get_user_by_email(login_data.email)
            if not local_user:
                logger.info(f"Creating new local user for email: {login_data.email}")
                username = login_data.email.split('@')[0]
                if db_handler.add_user(username, login_data.email, firebase_uid):
                    local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
                else:
                    logger.error(f"Failed to create local user for email: {login_data.email}")
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user account.")
            else:
                db_handler.update_firebase_uid(local_user['id'], firebase_uid)
                local_user['firebase_uid'] = firebase_uid
        
        if not local_user:
            logger.error(f"Critical error: Could not find or create local user for email: {login_data.email}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in the local database.")

        try:
            db_handler.update_last_login(local_user['id'])
        except Exception as e:
            logger.warning(f"Failed to update last login timestamp: {e}")

        return {
            "success": True,
            "message": "Login successful.",
            "userId": local_user['id'],
            "firebase_uid": firebase_uid,
            "id_token": id_token
        }
    except ValueError as ve:
        logger.warning(f"Firebase authentication failed for email {login_data.email}: {ve}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during API login: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during login.")
