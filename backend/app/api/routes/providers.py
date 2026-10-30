from fastapi import APIRouter

from app.core.config import get_settings
from app.core.errors import NotFoundError
from app.schemas import ModelsResponse, ProviderOut, ProvidersResponse
from app.services.llm.factory import PROVIDERS, list_provider_models

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=ProvidersResponse)
async def list_providers():
    settings = get_settings()
    return ProvidersResponse(
        default_provider=settings.llm_provider,
        embedding_model=settings.active_embedding_model,
        providers=[
            ProviderOut(
                name=spec.name,
                label=spec.label,
                description=spec.description,
                configured=bool(spec.api_key(settings)),
                default_model=spec.default_model(settings),
            )
            for spec in PROVIDERS.values()
        ],
    )


@router.get("/{name}/models", response_model=ModelsResponse)
async def list_models(name: str):
    settings = get_settings()
    spec = PROVIDERS.get(name.lower())
    if spec is None:
        raise NotFoundError("Unknown provider.")
    if not spec.api_key(settings):
        default = spec.default_model(settings)
        return ModelsResponse(provider=spec.name, default_model=default, models=[default])
    models, default = await list_provider_models(spec.name, settings)
    return ModelsResponse(provider=spec.name, default_model=default, models=models)
