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

# Benutzerdefinierte AuthenticatedUser-Klasse, die von User erbt
class AuthenticatedUser(User): # Extends the User Pydantic model
    """
    Diese Klasse erweitert das User-Pydantic-Modell und wird für authentifizierte Anfragen verwendet.
    Das id-Attribut bezieht sich auf die user_id aus der Datenbanktabelle, nicht auf die Firebase-ID.
    """
    pass

# Placeholder for current_user. In a real app, this would decode a JWT token.
async def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthenticatedUser:
    """
    Placeholder for JWT token validation and user retrieval.
    Für Firebase-Logins wird die Firebase-ID verwendet, um den Benutzer zu authentifizieren.
    Aber für alle anderen Anfragen wird die Benutzer-ID aus der Datenbank verwendet.
    
    1. Dekodieren und Verifizieren des JWT-Tokens.
    2. Extrahieren der Benutzeridentifikation (z.B. firebase_uid) aus dem Token.
    3. Abrufen des Benutzers aus der Datenbank mit der Benutzer-ID.
    4. HTTPException werfen, wenn das Token ungültig ist oder der Benutzer nicht gefunden wird.
    """
    # In einer realen App würden Token-Validierung und Benutzerabruf erfolgen
    # Für Demo-Zwecke nehmen wir an, dass das Token die Firebase-UID ist
    
    if token.startswith("firebase_uid_"): # Token ist Firebase-UID
        firebase_uid = token.split("firebase_uid_")[1]
        user_data = db_handler.get_user_by_firebase_uid(firebase_uid)
        if user_data:
            # Konvertieren des Dict in das AuthenticatedUser-Pydantic-Modell
            # Die ID ist hier die Benutzer-ID aus der Datenbank
            return AuthenticatedUser(**user_data)
    
    # Fallback für generische "fake_user_id" (nur für Tests)
    # In einem Produktionssystem würde dieser Teil entfernt werden
    user_data = db_handler.get_user_by_id(1)
    if not user_data:
        # Wenn Benutzer 1 nicht existiert, erstellen wir ein Dummy-Benutzerobjekt
        return AuthenticatedUser(id=1, email="user@example.com", firebase_uid="dummy_firebase_uid", username="dummy_user")

    return AuthenticatedUser(**user_data)

# Placeholder for a user object that might be available globally in Flask's `g`
# In FastAPI, you get this via Depends(get_current_user)

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
#     return AuthenticatedUser(**user) # Benutze AuthenticatedUser statt User
