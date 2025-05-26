from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import database.handler.postgres.postgres_db_handler as db_handler # Assuming this can be imported
from .pydantic_models import User # Import User Pydantic model
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from utils import auth as auth_module

# In a real app, this would come from config
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login") # Adjusted to new login path

# Placeholder for current_user. In a real app, this would decode a JWT token.
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Authenticate user based on Firebase ID token or test tokens.
    This function now properly handles Firebase JWT tokens.
    """
    
    # First try to verify as Firebase ID token (real JWT)
    try:
        decoded_token = auth_module.verify_firebase_id_token(token)
        if decoded_token:
            firebase_uid = decoded_token.get('uid')
            if firebase_uid:
                user_data = db_handler.get_user_by_firebase_uid(firebase_uid)
                if user_data:
                    return User(**user_data)
    except Exception as e:
        # Log the error but continue to try other token formats
        print(f"Firebase token verification failed: {e}")
    
    # Fallback: Try to parse Firebase UID from custom token format (for testing)
    if token.startswith("firebase_uid_"):
        firebase_uid = token.split("firebase_uid_")[1]
        user_data = db_handler.get_user_by_firebase_uid(firebase_uid)
        if user_data:
            return User(**user_data)
    
    # Fallback: Try to parse user_id from token (for testing purposes)
    if token.startswith("user_id_"):
        try:
            user_id = int(token.split("user_id_")[1])
            user_data = db_handler.get_user_by_id(user_id)
            if user_data:
                return User(**user_data)
        except ValueError:
            pass
    
    # If no valid token format found, raise authentication error
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Placeholder for a user object that might be available globally in Flask's `g`
# In FastAPI, you get this via Depends(get_current_user)
class AuthenticatedUser(User): # Extends the User Pydantic model
    pass

# Example of how you might structure a more complete get_current_user
# from jose import JWTError, jwt
# async def get_current_user_real(token: str = Depends(oauth2_scheme)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         firebase_uid: str = payload.get("sub") # Assuming 'sub' contains firebase_uid
#         if firebase_uid is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     user = db_handler.get_user_by_firebase_uid(firebase_uid)
#     if user is None:
#         raise credentials_exception
#     return User(**user)
