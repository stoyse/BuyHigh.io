"""
Router for authentication functions.
"""

from fastapi import APIRouter, HTTPException, status
import logging
from ..utils import auth as auth_module
import database.handler.postgres.postgres_db_handler as db_handler
from ..pydantic_models import LoginRequest, RegisterRequest, UserResponse, GoogleLoginRequest, FirebaseTokenLoginRequest

logger = logging.getLogger(__name__)
router = APIRouter()

logger.info(f"Auth_router: APIRouter instance created: {id(router)}")

@router.post("/login")
async def api_login(login_data: LoginRequest):
    """API route for user login"""
    logger.info(f"Auth_router: /login endpoint called.")
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
                logger.info(f"Local user found by email {login_data.email}. Updating Firebase UID to {firebase_uid}")
                db_handler.update_user_firebase_uid(local_user['id'], firebase_uid)
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

@router.post("/logout")
async def api_logout():
    """API route for user logout"""
    logger.info(f"Auth_router: /logout endpoint called.")
    logger.info("Logout request received")
    try:
        # In a complete implementation, the following actions could be performed here:
        # 1. Deleting session cookies
        # 2. Invalidating tokens on the server side (if necessary)
        # 3. Updating the last logout timestamp in the database
        
        # Since most Firebase-related logout operations are client-side,
        # we return a success message
        return {
            "success": True,
            "message": "Logout successful"
        }
    except Exception as e:
        logger.error(f"Error during logout: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail="An error occurred during logout.")

@router.post("/register", response_model=UserResponse)
async def api_register(register_data: RegisterRequest):
    """API route for user registration"""
    logger.info(f"Auth_router: /register endpoint called for email: {register_data.email}")
    logger.info(f"Registration attempt for email: {register_data.email}")
    try:
        # Step 1: Create user in Firebase Authentication
        firebase_user = auth_module.create_firebase_user(register_data.email, register_data.password, register_data.username)
        if not firebase_user or not firebase_user.uid:
            logger.error(f"Firebase user creation failed for email: {register_data.email}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user in Firebase.")
        
        logger.info(f"Firebase user created successfully: {firebase_user.uid} for email: {register_data.email}")

        # Step 2: Create user in local PostgreSQL database
        # Use email to derive a username if not provided, or use the provided one
        username_to_db = register_data.username if register_data.username else register_data.email.split('@')[0]
        
        # Check if user already exists by Firebase UID or email to prevent duplicates before adding
        existing_user_by_uid = db_handler.get_user_by_firebase_uid(firebase_user.uid)
        if existing_user_by_uid:
            logger.warning(f"User with Firebase UID {firebase_user.uid} already exists in local DB.")
            # Optionally, could update existing user or handle as an error/conflict
            return UserResponse(id=firebase_user.uid, email=firebase_user.email, username=existing_user_by_uid.get('username'), message="User already registered and linked.")

        existing_user_by_email = db_handler.get_user_by_email(register_data.email)
        if existing_user_by_email:
            logger.warning(f"User with email {register_data.email} already exists. Attempting to link Firebase UID.")
            db_handler.update_user_firebase_uid(existing_user_by_email['id'], firebase_user.uid)
            return UserResponse(id=firebase_user.uid, email=firebase_user.email, username=existing_user_by_email.get('username'), message="Existing user linked to Firebase account.")

        # Add new user to local DB
        if db_handler.add_user(username=username_to_db, email=register_data.email, firebase_uid=firebase_user.uid):
            logger.info(f"User {username_to_db} ({register_data.email}) added to local database with Firebase UID: {firebase_user.uid}")
            return UserResponse(id=firebase_user.uid, email=firebase_user.email, username=username_to_db, message="User registered successfully.")
        else:
            logger.error(f"Failed to add user {username_to_db} to local database for Firebase UID: {firebase_user.uid}")
            # Potentially, here you might want to delete the Firebase user if local DB registration fails to keep things consistent
            # auth_module.delete_firebase_user(firebase_user.uid) # Requires implementation in auth_module
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save user information locally.")

    except ValueError as ve: # Catch specific errors from create_firebase_user (e.g., email already exists)
        logger.warning(f"Firebase registration failed for {register_data.email}: {ve}")
        detail = str(ve)
        if "EMAIL_EXISTS" in detail:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")
        elif "WEAK_PASSWORD" in detail:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is too weak. It must be at least 6 characters long.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Error during user registration for {register_data.email}: {e}", exc_info=True)
        # Potentially, if firebase_user was created, try to delete it to avoid orphaned Firebase accounts
        # if 'firebase_user' in locals() and firebase_user and firebase_user.uid:
        #    auth_module.delete_firebase_user(firebase_user.uid) # Requires implementation
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during registration.")

@router.post("/google-login")
async def api_google_login(request_data: GoogleLoginRequest):
    logger.info(f"Auth_router: /google-login endpoint called.")
    try:
        id_token = request_data.id_token
        logger.debug(f"Received Google ID token: {id_token[:30]}...") # Log only a part of the token
        logger.info(f"AUTH_ROUTER: Processing Google login with token length: {len(id_token)}")

        decoded_token = auth_module.verify_google_id_token(id_token)
        if not decoded_token:
            logger.warning("Google ID token verification failed.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google ID token.")

        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        username = decoded_token.get('name') or email.split('@')[0]
        # email_verified = decoded_token.get('email_verified')
        # picture = decoded_token.get('picture')

        logger.info(f"Google token verified. Firebase UID: {firebase_uid}, Email: {email}")
        logger.info(f"AUTH_ROUTER: Decoded token data - UID: {firebase_uid}, Email: {email}, Username: {username}")

        local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
        if not local_user:
            logger.info(f"No local user for Firebase UID {firebase_uid}. Checking by email: {email}")
            local_user_by_email = db_handler.get_user_by_email(email)
            if local_user_by_email:
                logger.info(f"Local user found by email {email}. Updating Firebase UID from {local_user_by_email.get('firebase_uid')} to {firebase_uid}")
                db_handler.update_user_firebase_uid(local_user_by_email['id'], firebase_uid) # Korrigierter Funktionsname
                local_user = db_handler.get_user_by_firebase_uid(firebase_uid) # Re-fetch user with updated UID
            else:
                logger.info(f"No user found by email {email}. Creating new local user for Firebase UID: {firebase_uid}")
                if db_handler.add_user(username=username, email=email, firebase_uid=firebase_uid, provider='google.com'):
                    local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
                    logger.info(f"New local user created with ID: {local_user['id']} for Firebase UID: {firebase_uid}")
                else:
                    logger.error(f"Failed to create local user for Firebase UID: {firebase_uid} after Google login.")
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user account locally.")
        
        if not local_user:
            logger.error(f"Critical: Could not find or create local user for Firebase UID {firebase_uid} after Google login.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or could not be created locally.")

        try:
            db_handler.update_last_login(local_user['id'])
            logger.info(f"Updated last login for user ID: {local_user['id']}")
        except Exception as e:
            logger.warning(f"Failed to update last login for user ID {local_user['id']}: {e}")

        # The client already has the ID token from Google Sign-In.
        # This token can be used to authenticate with Firebase client-side services.
        # We return local user details and the Firebase UID.
        response_data = {
            "success": True,
            "message": "Google login successful.",
            "userId": local_user['id'], # Local DB user ID
            "firebase_uid": firebase_uid,
            "email": local_user['email'],
            "username": local_user['username'],
            "id_token": id_token # Return the original Google ID token, client can use this with Firebase
        }
        
        logger.info(f"AUTH_ROUTER: Google login response data: {response_data}")
        return response_data

    except ValueError as ve:
        logger.warning(f"Google login value error: {ve}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ve))
    except HTTPException:
        raise # Re-raise HTTPException directly
    except Exception as e:
        logger.error(f"Error during Google login: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during Google login.")

@router.post("/firebase-anonymous-login")
async def api_firebase_anonymous_login(request_data: FirebaseTokenLoginRequest):
    logger.info("Auth_router: /firebase-anonymous-login endpoint called.")
    try:
        id_token = request_data.id_token
        logger.debug(f"Received Firebase Anonymous ID token: {id_token[:30]}...")

        decoded_token = auth_module.verify_firebase_id_token(id_token)
        if not decoded_token:
            logger.warning("Firebase Anonymous ID token verification failed.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase Anonymous ID token.")

        firebase_uid = decoded_token.get('uid')
        
        # Check if the token is actually from an anonymous provider
        # The structure of decoded_token.firebase might vary slightly based on SDK version or token content.
        # Typically, for anonymous users, decoded_token.firebase.sign_in_provider is 'anonymous'.
        # Adjust this check if your decoded_token structure for anonymous users is different.
        firebase_info = decoded_token.get('firebase', {})
        sign_in_provider = firebase_info.get('sign_in_provider')

        if sign_in_provider != 'anonymous':
            logger.warning(f"Token provided to anonymous login is not from an anonymous provider. Provider: {sign_in_provider}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token is not for an anonymous user.")

        logger.info(f"Firebase Anonymous token verified. Firebase UID: {firebase_uid}")

        local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
        if not local_user:
            logger.info(f"No local user for Firebase Anonymous UID {firebase_uid}. Creating new local guest user.")
            
            guest_username = f"Guest_{firebase_uid[:8]}"
            # Ensure email is unique if constrained by DB. Using firebase_uid ensures uniqueness.
            guest_email = f"guest_{firebase_uid}@buyhigh.io" 

            # Assuming add_user can handle a 'provider' parameter or you adapt it.
            # If add_user doesn't take 'provider', you might need to add a specific
            # db_handler.add_guest_user function or modify add_user.
            # For now, let's assume 'provider' can be passed.
            # Also, ensure your add_user function can handle potentially NULL or placeholder emails if needed.
            if db_handler.add_user(username=guest_username, email=guest_email, firebase_uid=firebase_uid, provider='anonymous'):
                local_user = db_handler.get_user_by_firebase_uid(firebase_uid)
                if local_user:
                    logger.info(f"New local guest user created with ID: {local_user['id']} for Firebase UID: {firebase_uid}")
                else:
                    logger.error(f"Failed to retrieve guest user after creation for Firebase UID: {firebase_uid}")
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create or retrieve guest user account locally.")
            else:
                logger.error(f"Failed to create local guest user for Firebase UID: {firebase_uid} after anonymous Firebase login.")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create guest user account locally.")
        
        if not local_user: # Should be caught by the nested checks, but as a safeguard
            logger.error(f"Critical: Could not find or create local guest user for Firebase UID {firebase_uid}.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest user not found or could not be created locally.")

        try:
            db_handler.update_last_login(local_user['id'])
            logger.info(f"Updated last login for guest user ID: {local_user['id']}")
        except Exception as e:
            logger.warning(f"Failed to update last login for guest user ID {local_user['id']}: {e}")

        return {
            "success": True,
            "message": "Firebase Anonymous login successful. User is a guest.",
            "userId": local_user['id'], 
            "firebase_uid": firebase_uid,
            "email": local_user.get('email'), 
            "username": local_user.get('username'),
            "id_token": id_token, 
            "isGuest": True 
        }

    except HTTPException: # Re-raise HTTPExceptions directly to maintain status codes
        raise 
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Error during Firebase Anonymous login: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during anonymous login.")
