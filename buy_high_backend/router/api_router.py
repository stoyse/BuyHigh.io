"""
API router for chatbot functionality.
"""

from fastapi import APIRouter, Depends, HTTPException
from ..auth_utils import get_current_user, AuthenticatedUser
from ..pydantic_models import ChatbotRequest, ChatbotResponse
from ..utils.ai import generate_finance_response
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/api/chatbot", response_model=ChatbotResponse)
async def api_chatbot(
    request: ChatbotRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Process a chatbot request using the finance AI assistant.
    
    Args:
        request: ChatbotRequest containing the user's prompt
        current_user: Authenticated user information
        
    Returns:
        ChatbotResponse: AI-generated response or error message
    """
    try:
        logger.info(f"Processing chatbot request for user {current_user.email}")
        
        # Validate prompt
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
        # Generate AI response
        ai_response = generate_finance_response(request.prompt.strip())
        
        if ai_response:
            logger.info(f"Successfully generated AI response for user {current_user.email}")
            return ChatbotResponse(
                success=True,
                response=ai_response
            )
        else:
            logger.error(f"Failed to generate AI response for user {current_user.email}")
            return ChatbotResponse(
                success=False,
                error="Failed to generate AI response. Please try again later."
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chatbot endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while processing your request"
        )
