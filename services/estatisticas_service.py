from collections import Counter

from services import documentos_service as documentos

def calcular_estatisticas():
    registros = documentos.carregar_documentos()

    resultado = {
        "total_documentos": len(registros),
        "tamanho_total_bytes": sum(doc.tamanho for doc in registros),
        "por_extensao": dict(Counter(doc.extensao for doc in registros)),
        "por_categoria": dict(Counter(doc.categoria for doc in registros)),
        "por_projeto": dict(Counter(doc.projeto for doc in registros)),
    }

    documentos.logger.info("ESTATISTICAS total_documentos=%d", len(registros))   
    return resultado