from fastapi import APIRouter

from services.integridade_service import verificar_todos

router = APIRouter(tags=["Integridade"])

@router.get("/integridade")
def integridade_global():
    return verificar_todos()

