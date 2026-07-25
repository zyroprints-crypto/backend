from uuid import UUID

from pydantic import BaseModel


class PrintSettingsRecommendationRequest(BaseModel):
    file_type: str
    page_count: int
    purpose: str | None = None  # e.g. "resume", "wedding invite", "assignment"


class PrintSettingsRecommendationResponse(BaseModel):
    recommended_color_mode: str
    recommended_paper_size: str
    recommended_binding: str
    reasoning: str


class PriceEstimateRequest(BaseModel):
    document_id: UUID


class ProductSuggestionRequest(BaseModel):
    query: str


class ProductSuggestionResponse(BaseModel):
    suggestions: list[str]


class AssistantChatRequest(BaseModel):
    message: str
    context: str | None = None


class AssistantChatResponse(BaseModel):
    reply: str


class GenerateDescriptionRequest(BaseModel):
    product_title: str
    key_features: list[str] = []


class GenerateDescriptionResponse(BaseModel):
    description: str
