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
    payload: DailyQuizAttemptRequest, 
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id = current_user.id
    today_str = datetime.today().strftime('%Y-%m-%d')
    
    # Fetch today's quiz data from the database
    todays_quiz_details = education_handler.get_daily_quiz(date=today_str)

    if not todays_quiz_details:
        raise HTTPException(status_code=404, detail="Daily quiz not found for today.")

    actual_quiz_id_from_db = todays_quiz_details.get('id')
    if actual_quiz_id_from_db is None:
        logger.error(f"Quiz data for date {today_str} is missing 'id' field.")
        raise HTTPException(status_code=500, detail="Quiz data is incomplete (missing ID).")

    db_correct_answer = todays_quiz_details.get('correct_answer', "")
    db_explanation = todays_quiz_details.get('explanation', "") # Assuming 'explanation' field exists
    
    is_correct = False
    if payload.selected_answer == db_correct_answer:
        is_correct = True
    
    xp_gained = 50 if is_correct else 0 # Example XP logic

    try:
        # Insert the attempt using the actual quiz ID from the database
        education_handler.insert_daily_quiz_attempt(
            user_id=user_id,
            quiz_id=actual_quiz_id_from_db, # Use the ID from the fetched quiz data
            selected_answer=payload.selected_answer,
            is_correct=is_correct
        )
        
        # Construct the response expected by the frontend
        response_data = {
            "success": True,
            "is_correct": is_correct,
            "correct_answer": db_correct_answer,
            "explanation": db_explanation,
            "xp_gained": xp_gained,
            "message": "Attempt recorded successfully."
        }
        # logger.info(f"Daily Quiz Attempt Response for user {user_id}: {response_data}")
        return response_data

    except Exception as e:
        logger.error(f"Failed to insert daily quiz attempt for user {user_id}, quiz {actual_quiz_id_from_db}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while recording your quiz attempt.")

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
