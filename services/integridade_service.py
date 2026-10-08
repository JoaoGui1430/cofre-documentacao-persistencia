from fastapi import HTTPException

from services import documentos_service as documentos
from utils.hash import calcular_sha256

def verificar_arquivo(documento):
    resultado = {
        "id": str(documento.id),
        "nome_original": documento.nome_original,
        "sha256_armazenado": documento.sha256,
        "sha256_atual": None,
        "status" : "ausente",
    }

    try:
        caminho = documentos.caminho_do_arquivo(documento)
        atual = calcular_sha256(caminho, documentos.config["hash"]["algoritmo"])
    except HTTPException as erro:
        # 404 = arquivo físico sumiu (já registrado no log por caminho_do_arquivo).
        if erro.status_code == 404:
            return resultado
        raise
    except FileNotFoundError:
        documentos.logger.error("ARQUIVO_FISICO_NAO_ENCONTRADO id=%s arquivo=%s", documento.id, documento.nome_armazenado)
        return resultado
    except OSError as erro:
        resultado["status"] = "erro_leitura"
        documentos.logger.error("ERRO_LEITURA id=%s arquivo=%s erro=%s", documento.id, documento.nome_armazenado, erro)
        return resultado
    resultado["sha256_atual"] = atual
    resultado["status"] = "integro" if atual == documento.sha256 else "alterado"
    if resultado["status"] == "integro":
        documentos.logger.info("INTEGRIDADE_OK id=%s arquivo=%s", documento.id, documento.nome_original)
    else:
        documentos.logger.warning("INTEGRIDADE_FALHOU id=%s arquivo=%s", documento.id, documento.nome_original)
    return resultado

def verificar_documento(identificador):
    with documentos.repositorio.trava:
        documento = documentos.buscar_documento(identificador)
        resultado = verificar_arquivo(documento)

    if resultado["status"] == "ausente":
        raise HTTPException(status_code=404, detail=f"Documento {identificador} não encontrado")
    if resultado["status"] == "erro_leitura":
        raise HTTPException(status_code=500, detail=f"Falha ao ler o arquivo do documento {identificador}")
    return resultado

def verificar_todos():
    with documentos.repositorio.trava:
        registros = documentos.carregar_documentos()
        resultados = [verificar_arquivo(item) for item in registros]

        integros = sum(item["status"] == "integro" for item in resultados)
        alterados = sum(item["status"] == "alterado" for item in resultados)
        ausentes = sum(item["status"] == "ausente" for item in resultados)
        erros = sum(item["status"] == "erro_leitura" for item in resultados)

        documentos.logger.info("INTEGRIDADE_GLOBAL total=%d integros=%d alterados=%d ausentes=%d erros=%d", len(registros), integros, alterados, ausentes, erros)

        return {
            "total_documentos": len(registros),
            "verificados": integros + alterados,
            "integros": integros,
            "alterados": alterados,
            "ausentes": ausentes,
            "erros_leitura": erros,
            "resultados": resultados,
        }