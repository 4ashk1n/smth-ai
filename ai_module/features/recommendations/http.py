from fastapi import APIRouter

router = APIRouter(prefix="/recommendations")


@router.get("/health")
def recommendations_health() -> dict[str, str]:
    return {"status": "ok"}


__all__ = ["router"]



