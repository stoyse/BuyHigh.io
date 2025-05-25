"""
Router for educational features such as the daily quiz.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import logging
import database.handler.postgres.postgre_education_handler as education_handler
import database.handler.postgres.postgres_db_handler as db_handler
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import DailyQuizAttemptRequest, DailyQuizAttemptResponse, RoadmapListResponse, RoadmapStepsResponse, RoadmapQuizAttemptRequest, RoadmapQuizAttemptResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/daily-quiz") # Adjust response model according to education_handler output
async def api_get_daily_quiz(current_user: AuthenticatedUser = Depends(get_current_user)):
    user_id_for_analytics = current_user.id
    today = datetime.today().strftime('%Y-%m-%d')
    quiz_data = education_handler.get_daily_quiz(date=today)
    return quiz_data

@router.post("/daily-quiz/attempt", response_model=DailyQuizAttemptResponse) # Use DailyQuizAttemptResponse
async def api_submit_daily_quiz_attempt(
    payload: DailyQuizAttemptRequest, 
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id = current_user.id
    today_str = datetime.today().strftime('%Y-%m-%d')
    
    todays_quiz_details = education_handler.get_daily_quiz(date=today_str)

    if not todays_quiz_details:
        raise HTTPException(status_code=404, detail="Daily quiz not found for today.")

    actual_quiz_id_from_db = todays_quiz_details.get('id')
    if actual_quiz_id_from_db is None:
        logger.error(f"Quiz data for date {today_str} is missing 'id' field.")
        raise HTTPException(status_code=500, detail="Quiz data is incomplete (missing ID).")

    # Check if user already attempted today's quiz using get_daily_quiz_attempts
    all_user_attempts = education_handler.get_daily_quiz_attempts(user_id)
    found_todays_attempt = None
    if all_user_attempts:
        for attempt in all_user_attempts:
            if attempt.get('quiz_id') == actual_quiz_id_from_db:
                found_todays_attempt = attempt
                break
    
    if found_todays_attempt:
        # Use todays_quiz_details for correct_answer and explanation
        # found_todays_attempt contains is_correct and selected_answer
        return DailyQuizAttemptResponse(
            success=True,
            is_correct=found_todays_attempt['is_correct'],
            correct_answer=todays_quiz_details.get('correct_answer', ""), 
            explanation=todays_quiz_details.get('explanation', ""),
            xp_gained=0,
            message="Quiz already attempted today.",
            selected_answer=found_todays_attempt['selected_answer']
        )

    db_correct_answer = todays_quiz_details.get('correct_answer', "")
    db_explanation = todays_quiz_details.get('explanation', "")
    
    is_correct = False
    if payload.selected_answer == db_correct_answer:
        is_correct = True
    
    xp_gained = 0
    if is_correct:
        xp_config = db_handler.get_xp_gains("daily_quiz_correct")
        if xp_config:
            xp_gained = xp_config.get('xp_amount', 50)
    else:
        xp_config = db_handler.get_xp_gains("daily_quiz_incorrect")
        if xp_config:
            xp_gained = xp_config.get('xp_amount', 10)

    try:
        education_handler.insert_daily_quiz_attempt(
            user_id=user_id,
            quiz_id=actual_quiz_id_from_db,
            selected_answer=payload.selected_answer,
            is_correct=is_correct
        )
        
        if xp_gained > 0:
             db_handler.manage_user_xp(action="daily_quiz", user_id_param=user_id, quantity=xp_gained)

        response_data = DailyQuizAttemptResponse(
            success=True,
            is_correct=is_correct,
            correct_answer=db_correct_answer,
            explanation=db_explanation,
            xp_gained=xp_gained,
            message="Attempt recorded successfully.",
            selected_answer=payload.selected_answer
        )
        return response_data

    except Exception as e:
        logger.error(f"Failed to insert daily quiz attempt for user {user_id}, quiz {actual_quiz_id_from_db}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while recording your quiz attempt.")

@router.get("/daily-quiz/attempt/today", response_model=DailyQuizAttemptResponse) # Use DailyQuizAttemptResponse
async def api_get_daily_quiz_attempt_today(current_user: AuthenticatedUser = Depends(get_current_user)):
    user_id = current_user.id
    today_str = datetime.today().strftime('%Y-%m-%d')
    
    attempt = education_handler.get_dayly_quiz_attempt_day(user_id, today_str)
    
    if attempt:
        return DailyQuizAttemptResponse(
            success=True,
            is_correct=attempt['is_correct'],
            correct_answer=attempt['correct_answer'],
            explanation=attempt['explanation'],
            xp_gained=0, 
            message="Existing attempt found.",
            selected_answer=attempt['selected_answer']
        )
    else:
         return DailyQuizAttemptResponse(
            success=False,
            is_correct=False,
            correct_answer="",
            explanation="",
            xp_gained=0,
            message="No attempt found for today.",
            selected_answer=None
        )

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
