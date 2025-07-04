from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Union
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None # Optional username

class GoogleLoginRequest(BaseModel):
    id_token: str

class FirebaseTokenLoginRequest(BaseModel):
    id_token: str

class UserCreateRequest(BaseModel): # For internal use, if creating in local DB
    email: EmailStr
    firebase_uid: str
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: Optional[str] = None # Firebase UID
    email: EmailStr
    username: Optional[str] = None
    message: Optional[str] = None

class User(BaseModel):
    id: int
    username: Optional[str] = None
    email: EmailStr
    firebase_uid: Optional[str] = None
    # Add other user fields as needed

class Token(BaseModel):
    access_token: str
    token_type: str

class TradeRequest(BaseModel):
    symbol: str
    quantity: float
    price: float

class ProfilePictureUploadResponse(BaseModel):
    success: bool
    message: str
    url: Optional[str] = None

class EasterEggRedeemRequest(BaseModel):
    code: str

class StockDataPoint(BaseModel):
    date: str # ISO format string
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]
    currency: Optional[str] = 'USD'

class Asset(BaseModel):
    id: Union[int, str]
    symbol: str
    name: str
    asset_type: str
    default_price: Optional[float] = None
    url: Optional[str] = None  # Hinzugefügtes Feld für die Artikel-URL
    image_url: Optional[str] = None # Hinzugefügtes Feld für die Bild-URL

class AssetResponse(BaseModel):
    success: bool
    asset: Optional[Asset] = None
    message: Optional[str] = None

class AssetsListResponse(BaseModel):
    success: bool
    assets: List[Asset]
    message: Optional[str] = None

class FunnyTip(BaseModel):
    id: int
    tip: str

class FunnyTipsResponse(BaseModel):
    success: bool
    tips: List[FunnyTip]

class StatusResponse(BaseModel):
    api_key_configured: bool
    timestamp: str # ISO format datetime

class DailyQuizResponse(BaseModel): # Assuming structure from education_handler
    # Define fields based on what education_handler.get_daily_quiz returns
    # Example:
    # question: str
    # options: List[str]
    # quiz_date: str
    success: bool
    data: Any # Replace Any with a more specific model if possible

class DailyQuizAttemptRequest(BaseModel):
    quiz_id: int  # Geändert von int zu str, um mit dem Frontend übereinzustimmen
    selected_answer: str

class DailyQuizAttemptResponse(BaseModel):
    success: bool
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    xp_gained: int
    message: Optional[str] = None
    selected_answer: Optional[str] = None # Added selected_answer

class RoadmapListResponse(BaseModel):
    success: bool
    roadmaps: List[Any] # Replace Any with a more specific Roadmap model if available

class RoadmapStepsResponse(BaseModel):
    success: bool
    steps: List[Any] # Replace Any with a more specific RoadmapStep model if available

class RoadmapQuizAttemptRequest(BaseModel):
    user_id: int
    roadmap_id: int
    step_id: int
    quiz_id: int
    selected_answer: str
    is_correct: bool

class RoadmapQuizAttemptResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    # Add any other relevant fields for the response, e.g.:
    # score: Optional[int] = None
    # xp_gained: Optional[int] = None

class UserDataResponse(BaseModel): # Assuming structure from db_handler.get_user_by_id
    # Define fields based on what db_handler.get_user_by_id returns
    # Example:
    # id: int
    # username: str
    # email: str
    # balance: float
    # profile_pic_url: Optional[str] = None
    success: bool
    user: Optional[Any] # Replace Any with a more specific User model

class Transaction(BaseModel): # Assuming structure from transactions_handler.get_recent_transactions
    asset_symbol: str
    quantity: float
    price_per_unit: float
    transaction_type: str
    timestamp: datetime

class TransactionsListResponse(BaseModel):
    success: bool
    transactions: Optional[List[Transaction]] = None
    message: Optional[str] = None

class PortfolioItem(BaseModel): # Assuming structure from transactions_handler.show_user_portfolio
    symbol: str
    name: str
    type: str
    quantity: float
    average_price: float
    current_price: float
    performance: float
    sector: Optional[str] = None
    value: float

class PortfolioResponse(BaseModel):
    success: bool
    portfolio: Optional[List[PortfolioItem]] = None
    total_value: Optional[float] = None
    message: Optional[str] = None

class RedeemCodeRequest(BaseModel):
    code: str

class RedeemCodeResponse(BaseModel):
    success: bool
    message: str
    reload: Optional[bool] = False
    reward: Optional[float] = None
    new_balance: Optional[float] = None

# Added BasicUser and AllUsersResponse models
class BasicUser(BaseModel):
    id: int
    username: str
    level: Optional[int] = 0
    xp: Optional[int] = 0
    balance: Optional[float] = 0.0 # Assuming balance can be float
    total_profit: Optional[float] = 0.0 # Assuming profit can be float
    total_trades: Optional[int] = 0
    profile_picture_url: Optional[str] = None
    # Add other fields that you expect to be part of a user's basic public profile

class AllUsersResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    users: List[BasicUser] = []

class ChatbotRequest(BaseModel):
    prompt: str

class ChatbotResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
