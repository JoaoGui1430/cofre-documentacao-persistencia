import csv
from uuid import uuid4

from app.documento import Documento
from services import documentos_service as documentos

def exportar_csv():
    registros = documentos.carregar_documentos()
    destino = documentos.PASTA_EXPORTACOES / f"catalogo_{uuid4()}.csv"

    try:
        with destino.open("x", encoding="utf-8-sig", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(Documento.model_fields))
            escritor.writeheader()
            for documento in registros:
                escritor.writerow(documento.model_dump(mode="json"))
    except (OSError, csv.Error, ValueError) as erro:
        documentos.limpar_parcial(destino)
        documentos.falhar(500, "Falha ao exportar o catálogo para CSV.", erro, operacao="ERRO_EXPORTACAO_CSV")

    documentos.logger.info("EXPORTACAO_CSV arquivo=%s registros=%d", destino.name, len(registros))
    return destino