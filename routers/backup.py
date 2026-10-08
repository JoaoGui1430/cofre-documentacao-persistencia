from fastapi import APIRouter

from services.backup_service import criar_backup

router = APIRouter(tags=["Backup"])


# F14 - Backup compactado
# Sem parâmetros: backup geral. Com ?projeto= e/ou ?versao=: backup seletivo.
@router.post("/backup", status_code=201)
def gerar_backup(projeto: str | None = None, versao: str | None = None):
    return criar_backup(projeto=projeto, versao=versao)
