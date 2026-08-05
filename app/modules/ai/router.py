from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.ai.schemas import (
    AssistantChatRequest,
    AssistantChatResponse,
    GenerateDescriptionRequest,
    GenerateDescriptionResponse,
    PrintSettingsRecommendationRequest,
    PrintSettingsRecommendationResponse,
    ProductSuggestionRequest,
    ProductSuggestionResponse,
)
from app.modules.ai.service import AIService
from app.modules.users.models import User

router = APIRouter(prefix="/ai", tags=["Zyro AI Assistant"])
ai_service = AIService()


@router.post("/recommend-print-settings", response_model=SuccessResponse[PrintSettingsRecommendationResponse])
def recommend_print_settings(payload: PrintSettingsRecommendationRequest, current_user: User = Depends(get_current_user)):
    return SuccessResponse(data=ai_service.recommend_print_settings(payload))


@router.post("/suggest-products", response_model=SuccessResponse[ProductSuggestionResponse])
def suggest_products(payload: ProductSuggestionRequest, current_user: User = Depends(get_current_user)):
    return SuccessResponse(data=ai_service.suggest_products(payload.query))


@router.post("/chat", response_model=SuccessResponse[AssistantChatResponse])
def chat(payload: AssistantChatRequest, current_user: User = Depends(get_current_user)):
    return SuccessResponse(data=ai_service.chat(payload.message, payload.context))


@router.post("/generate-product-description", response_model=SuccessResponse[GenerateDescriptionResponse])
def generate_product_description(payload: GenerateDescriptionRequest, current_user: User = Depends(get_current_user)):
    return SuccessResponse(data=ai_service.generate_product_description(payload.product_title, payload.key_features))
