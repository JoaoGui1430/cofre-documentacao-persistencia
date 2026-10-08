from collections import Counter

from services import documentos_service as documentos

def calcular_estatisticas():
    registros = documentos.carregar_documentos()

    resultado = {
        "total_documentos": len(registros),
        "espaco_utilizado_bytes": sum(doc.tamanho for doc in registros),
        # No JSON a extensão fica com ponto (".pdf"); aqui sai sem ponto ("pdf"), como no enunciado.
        "por_extensao": dict(Counter(doc.extensao.lstrip(".") or "sem_extensao" for doc in registros)),
        "por_categoria": dict(Counter(doc.categoria for doc in registros)),
        "por_projeto": dict(Counter(doc.projeto for doc in registros)),
    }

    documentos.logger.info("ESTATISTICAS total_documentos=%d", len(registros))   
    return resultado