"""
Zyro AI Smart Assistant.
`_call_llm` is the single integration point for the underlying LLM provider
(configured via settings.AI_PROVIDER_API_KEY / AI_PROVIDER_MODEL). Every
endpoint below is a real, usable API contract; swap the rule-based logic for
an LLM call here without touching routers or other services.
"""
from app.modules.ai.schemas import (
    AssistantChatResponse,
    GenerateDescriptionResponse,
    PrintSettingsRecommendationRequest,
    PrintSettingsRecommendationResponse,
    ProductSuggestionResponse,
)


def _call_llm(prompt: str) -> str:
    # Placeholder for a real call, e.g.:
    # response = anthropic.Anthropic(api_key=settings.AI_PROVIDER_API_KEY).messages.create(
    #     model=settings.AI_PROVIDER_MODEL, max_tokens=500,
    #     messages=[{"role": "user", "content": prompt}],
    # )
    # return response.content[0].text
    return f"[AI response placeholder for prompt: {prompt[:80]}...]"


class AIService:
    def recommend_print_settings(self, payload: PrintSettingsRecommendationRequest) -> PrintSettingsRecommendationResponse:
        purpose = (payload.purpose or "").lower()
        if "wedding" in purpose or "invite" in purpose:
            return PrintSettingsRecommendationResponse(
                recommended_color_mode="color", recommended_paper_size="A4",
                recommended_binding="none",
                reasoning="Wedding invitations typically use premium color printing without binding.",
            )
        if "resume" in purpose or "assignment" in purpose or "report" in purpose:
            binding = "spiral" if payload.page_count > 20 else "none"
            return PrintSettingsRecommendationResponse(
                recommended_color_mode="black_white", recommended_paper_size="A4",
                recommended_binding=binding,
                reasoning=f"Text documents of {payload.page_count} pages are cost-effective in B&W;"
                          f" spiral binding recommended above 20 pages.",
            )
        return PrintSettingsRecommendationResponse(
            recommended_color_mode="black_white", recommended_paper_size="A4", recommended_binding="none",
            reasoning="Default recommendation for general documents.",
        )

    def suggest_products(self, query: str) -> ProductSuggestionResponse:
        catalog_hints = {
            "wedding": ["Wedding Invitation Cards", "Photo Frame", "Custom Guest Book"],
            "birthday": ["Birthday Card", "Custom Poster", "Photo Mug"],
            "office": ["Business Card", "Letterhead", "Corporate Gift Set"],
            "shirt": ["Custom T-Shirt", "Printed Cap", "Hoodie"],
        }
        for key, suggestions in catalog_hints.items():
            if key in query.lower():
                return ProductSuggestionResponse(suggestions=suggestions)
        return ProductSuggestionResponse(suggestions=["Business Card", "Poster", "Sticker"])

    def chat(self, message: str, context: str | None) -> AssistantChatResponse:
        prompt = f"Context: {context or 'none'}\nCustomer question: {message}"
        return AssistantChatResponse(reply=_call_llm(prompt))

    def generate_product_description(self, title: str, features: list[str]) -> GenerateDescriptionResponse:
        prompt = f"Write a short marketing description for '{title}' with features: {', '.join(features)}"
        return GenerateDescriptionResponse(description=_call_llm(prompt))
