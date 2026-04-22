from fastapi import APIRouter, HTTPException

from ai_module.api.mappers import to_api_suggestion, to_domain_article
from ai_module.api.schemas import ArticleIn, SuggestionsResponse
from ai_module.application.pipelines.layout_quality_pipeline import LayoutQualityPipeline
from ai_module.application.pipelines.text_quality_pipeline import TextQualityPipeline
from ai_module.core.errors import ProviderError, ValidationError
from ai_module.providers.llm.gigachat_provider import GigaChatProvider
from ai_module.providers.llm.prompt_builder import PromptBuilder

router = APIRouter(prefix="/suggestions")


def get_layout_pipeline() -> LayoutQualityPipeline:
    return LayoutQualityPipeline()


def get_text_pipeline() -> TextQualityPipeline:
    return TextQualityPipeline(
        llm_provider=GigaChatProvider(),
        prompt_builder=PromptBuilder(),
    )


@router.post("/layout", response_model=SuggestionsResponse)
def suggest_layout(payload: ArticleIn) -> SuggestionsResponse:
    try:
        article = to_domain_article(payload)
        suggestions = get_layout_pipeline().run_for_article(article)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return SuggestionsResponse(suggestions=[to_api_suggestion(item) for item in suggestions])


@router.post("/text", response_model=SuggestionsResponse)
def suggest_text(payload: ArticleIn) -> SuggestionsResponse:
    try:
        article = to_domain_article(payload)
        suggestions = get_text_pipeline().run_for_article(article)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return SuggestionsResponse(suggestions=[to_api_suggestion(item) for item in suggestions])


@router.post("/all", response_model=SuggestionsResponse)
def suggest_all(payload: ArticleIn) -> SuggestionsResponse:
    try:
        article = to_domain_article(payload)
        layout_suggestions = get_layout_pipeline().run_for_article(article)
        text_suggestions = get_text_pipeline().run_for_article(article)
        suggestions = [*layout_suggestions, *text_suggestions]
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return SuggestionsResponse(suggestions=[to_api_suggestion(item) for item in suggestions])

