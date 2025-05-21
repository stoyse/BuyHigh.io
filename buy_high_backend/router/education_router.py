"""
Router für Bildungsfunktionen wie tägliches Quiz.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import logging
import database.handler.postgres.postgre_education_handler as education_handler
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import DailyQuizAttemptRequest, RoadmapListResponse, RoadmapStepsResponse, RoadmapQuizAttemptRequest

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/daily-quiz") # Response-Modell je nach education_handler-Ausgabe anpassen
async def api_get_daily_quiz(current_user: AuthenticatedUser = Depends(get_current_user)):
    user_id_for_analytics = current_user.id
    today = datetime.today().strftime('%Y-%m-%d')
    quiz_data = education_handler.get_daily_quiz(date=today)
    return quiz_data

@router.post("/daily-quiz/attempt") # Response-Modell anpassen
async def api_submit_daily_quiz_attempt(
    payload: DailyQuizAttemptRequest, # Pydantic-Modell für die Anfrage
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id = current_user.id

    result = education_handler.submit_daily_quiz_attempt(
        user_id=user_id,
        quiz_id=payload.quiz_id,
        selected_answer=payload.selected_answer
    )
    return result

@router.get("/roadmap", response_model=RoadmapListResponse)
async def api_get_roadmaps(current_user: AuthenticatedUser = Depends(get_current_user)):
    user_id = current_user.id
    roadmaps = education_handler.get_all_roadmaps()
    if roadmaps is not None:
        return RoadmapListResponse(success=True, roadmaps=roadmaps)
    else:
        raise HTTPException(status_code=500, detail="Could not fetch roadmaps")

@router.get("/roadmap/{roadmap_id}/steps", response_model=RoadmapStepsResponse)
async def api_get_roadmap_steps(roadmap_id: int, current_user: AuthenticatedUser = Depends(get_current_user)):
    user_id = current_user.id
    steps = education_handler.get_roadmap_steps_with_quizzes(roadmap_id, user_id)
    if steps is not None:
        return RoadmapStepsResponse(success=True, steps=steps)
    else:
        raise HTTPException(status_code=500, detail=f"Could not fetch steps for roadmap {roadmap_id}")


@router.post("/roadmap/quiz/attempt", response_model=RoadmapQuizAttemptResponse)
async def api_submit_roadmap_quiz_attempt(
    payload: RoadmapQuizAttemptRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id = current_user.id

    result = education_handler.submit_roadmap_quiz_attempt(
        user_id=user_id,
        quiz_id=payload.quiz_id,
        selected_answer=payload.selected_answer,
        roadmap_id=payload.roadmap_id,
        step_id=payload.step_id
    )
    return result
