from fastapi import APIRouter
from fastapi.responses import FileResponse

from services.exportacao_service import exportar_csv

router = APIRouter(prefix="/exportar", tags=["Exportações"])

@router.get("/csv")
def baixar_csv():
    caminho = exportar_csv()
    return FileResponse(caminho, media_type="text/csv", filename=caminho.name)
