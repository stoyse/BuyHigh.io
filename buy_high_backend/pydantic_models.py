from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

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
    id: int
    symbol: str
    name: str
    asset_type: str
    default_price: Optional[float] = None
    # Removed last_price and last_price_updated as per original logic for /assets/<symbol>

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
    user_id: int
    quiz_id: int
    selected_answer: str
    is_correct: bool
    attempted_at: Optional[datetime] = None

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
