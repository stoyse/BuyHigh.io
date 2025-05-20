from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import database.handler.postgres.postgres_db_handler as db_handler # Assuming this can be imported
from .pydantic_models import User # Import User Pydantic model

# In a real app, this would come from config
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login") # Adjusted to new login path

# Placeholder for current_user. In a real app, this would decode a JWT token.
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Placeholder for JWT token validation and user retrieval.
    For now, it simulates fetching a user based on a dummy token logic.
    A real implementation would:
    1. Decode and verify the JWT token.
    2. Extract user identifier (e.g., user_id or firebase_uid) from token.
    3. Fetch user from database.
    4. Raise HTTPException if token is invalid or user not found.
    """
    # This is a very basic placeholder.
    # In a real app, you'd validate the token and fetch user details.
    # For demonstration, let's assume the token IS the firebase_uid for simplicity here.
    # Or, if login returns a custom token, this function would validate that.
    # For now, we'll try to fetch a user if a token "user_id_X" is passed.
    
    # This is highly insecure and for demonstration only.
    # A real system would involve JWT decoding and verification.
    if token.startswith("firebase_uid_"): # Simulate token being firebase_uid
        firebase_uid = token.split("firebase_uid_")[1]
        user_data = db_handler.get_user_by_firebase_uid(firebase_uid)
        if user_data:
            # Convert dict to User Pydantic model
            return User(**user_data) # Ensure User model matches db_handler output
    
    # Fallback for a generic "fake_user_id" if the above fails or for testing
    # This part would be removed in a production system
    user_data = db_handler.get_user_by_id(1) # Example: fetch user with ID 1
    if not user_data:
        # If user 1 doesn't exist, create a dummy user object
        # This is purely for making the dependency work without a real auth flow initially
        return User(id=1, email="user@example.com", firebase_uid="dummy_firebase_uid", username="dummy_user")

    return User(**user_data) # Ensure User model matches db_handler output

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
