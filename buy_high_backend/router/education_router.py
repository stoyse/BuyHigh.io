"""
Router for educational features such as the daily quiz.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import logging
import database.handler.postgres.postgre_education_handler as education_handler
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import DailyQuizAttemptRequest, RoadmapListResponse, RoadmapStepsResponse, RoadmapQuizAttemptRequest, RoadmapQuizAttemptResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/daily-quiz") # Adjust response model according to education_handler output
async def api_get_daily_quiz(current_user: AuthenticatedUser = Depends(get_current_user)):
    user_id_for_analytics = current_user.id
    today = datetime.today().strftime('%Y-%m-%d')
    quiz_data = education_handler.get_daily_quiz(date=today)
    return quiz_data

@router.post("/daily-quiz/attempt") # Adjust response model
async def api_submit_daily_quiz_attempt(
    payload: DailyQuizAttemptRequest, # Pydantic model for the request
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id = current_user.id
    quiz_data = education_handler.get_daily_quiz(date=datetime.today().strftime('%Y-%m-%d')) # Renamed for clarity
    
    is_correct = False # Initialize is_correct
    
    if quiz_data and 'correct_answer' in quiz_data: # Check if quiz_data and correct_answer exist
        correct_answer = quiz_data.get('correct_answer')
        # Assuming selected_answer is the direct value to compare
        if payload.selected_answer == correct_answer:
            is_correct = True
    
    # It's good practice to ensure quiz_id is valid or handle if not
    # For example, check if payload.quiz_id matches quiz_data.get('id') if available
    
    result = education_handler.insert_daily_quiz_attempt(
        user_id=user_id,
        quiz_id=payload.quiz_id, # Ensure this quiz_id is relevant/validated
        selected_answer=payload.selected_answer,
        is_correct=is_correct
    )
    print(f"[bold blue]Daily Quiz Attempt Result: {result}[/bold blue]")
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
