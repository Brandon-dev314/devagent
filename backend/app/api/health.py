
from fastapi import APIRouter
from app.config import settings


router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness():

    return {
        "status": "alive",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/health/ready")
async def readiness():

    # Por ahora son stubs — los implementamos cuando conectemos cada servicio
    checks = {
        "postgres": _check_postgres(),
        "redis": _check_redis(),
        "qdrant": _check_qdrant(),
    }

    all_healthy = all(c["status"] == "ok" for c in checks.values())

    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
    }


def _check_postgres() -> dict:

    return {"status": "ok", "detail": "stub — not yet implemented"}


def _check_redis() -> dict:

    return {"status": "ok", "detail": "stub — not yet implemented"}


def _check_qdrant() -> dict:

    return {"status": "ok", "detail": "stub — not yet implemented"}