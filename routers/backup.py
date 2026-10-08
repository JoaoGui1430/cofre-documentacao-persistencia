from fastapi import APIRouter
from fastapi.responses import FileResponse

from services.backup_service import criar_backup, listar_backups, localizar_backup, restaurar_backup

router = APIRouter(tags=["Backup"])


# F14 - Backup compactado
# Sem parâmetros: backup geral. Com ?projeto= e/ou ?versao=: backup seletivo.
@router.post("/backup", status_code=201)
def gerar_backup(projeto: str | None = None, versao: str | None = None):
    return criar_backup(projeto=projeto, versao=versao)


# F15 - Listagem de backups
@router.get("/backups")
def listar():
    return listar_backups()


# Download de um backup específico (404 se ele não existir)
@router.get("/backups/{nome}")
def baixar_backup(nome: str):
    caminho = localizar_backup(nome)
    return FileResponse(caminho, media_type="application/zip", filename=caminho.name)

@router.post("/backups/{nome}/restaurar")
def restaurar(nome: str):
    return restaurar_backup(nome)
