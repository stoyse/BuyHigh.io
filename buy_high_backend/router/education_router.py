"""
Router für Bildungsfunktionen wie tägliches Quiz.
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import logging
import database.handler.postgres.postgre_education_handler as education_handler
from database.handler.postgres.postgres_db_handler import add_analytics
from ..auth_utils import get_current_user, AuthenticatedUser
# Pydantic-Modell hier importieren, falls vorhanden

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/daily-quiz") # Response-Modell je nach education_handler-Ausgabe anpassen
async def api_get_daily_quiz(current_user: AuthenticatedUser = Depends(get_current_user)):
    user_id_for_analytics = current_user.id
    add_analytics(user_id_for_analytics, "api_get_daily_quiz", "api_routes:api_get_daily_quiz")
    today = datetime.today().strftime('%Y-%m-%d')
    quiz_data = education_handler.get_daily_quiz(date=today)
    return quiz_data
