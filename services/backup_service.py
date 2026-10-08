import json
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED

from core import repositorio
from core.armazenamento import caminho_arquivo, diretorio
from services import documentos_service as documentos


def gerar_destino(prefixo):
    """Escolhe um nome livre na pasta de backups, ex.: backup_2026-10-08_1430.zip."""
    pasta = diretorio("backups")
    base = f"{prefixo}_{datetime.now().strftime('%Y-%m-%d_%H%M')}"
    destino = pasta / f"{base}.zip"
    contador = 2
    # Dois backups no mesmo minuto ganham sufixo (_2, _3...) em vez de sobrescrever o anterior.
    while destino.exists():
        destino = pasta / f"{base}_{contador}.zip"
        contador += 1
    return destino


def criar_backup(projeto=None, versao=None):
    """Sem filtros: backup geral. Com projeto e/ou versão: backup seletivo só desses documentos."""
    seletivo = projeto is not None or versao is not None

    # A trava impede que um upload/exclusão aconteça no meio do backup,
    # então o ZIP sempre reflete um estado consistente do cofre.
    with repositorio.trava:
        registros = documentos.listar_documentos(projeto=projeto, versao=versao)
        if seletivo and not registros:
            documentos.falhar(404, "Nenhum documento encontrado para os filtros informados", operacao="BACKUP_SELETIVO_VAZIO")

        destino = gerar_destino("backup_seletivo" if seletivo else "backup")
        incluidos = []
        ausentes = []
        try:
            # zipfile (biblioteca padrão) cria o arquivo .zip; ZIP_DEFLATED ativa a compressão.
            # Modo "x" falha se o arquivo já existir: garantia extra de nunca sobrescrever.
            with ZipFile(destino, "x", compression=ZIP_DEFLATED) as pacote:
                for documento in registros:
                    caminho = caminho_arquivo(documento.nome_armazenado)
                    if not caminho.is_file():
                        # Um arquivo sumido não impede o backup dos demais; fica registrado no log e na resposta.
                        documentos.logger.warning("BACKUP_ARQUIVO_AUSENTE id=%s arquivo=%s", documento.id, documento.nome_armazenado)
                        ausentes.append(str(documento.id))
                        continue
                    pacote.write(caminho, f"documentos/{documento.nome_armazenado}")
                    incluidos.append(documento)

                # Metadados dos documentos incluídos, no mesmo formato do documentos.json do cofre.
                dados = [item.model_dump(mode="json") for item in incluidos]
                pacote.writestr("metadata/documentos.json", json.dumps(dados, ensure_ascii=False, indent=2))
        except (OSError, ValueError) as erro:
            documentos.limpar_parcial(destino)
            documentos.falhar(500, "Falha ao criar o backup compactado", erro, operacao="ERRO_BACKUP")

    documentos.logger.info(
        "BACKUP_CRIADO arquivo=%s documentos=%d seletivo=%s projeto=%s versao=%s",
        destino.name, len(incluidos), seletivo, projeto, versao,
    )
    return {
        "arquivo": destino.name,
        "tamanho": destino.stat().st_size,
        "tipo": "seletivo" if seletivo else "geral",
        "filtros": {"projeto": projeto, "versao": versao} if seletivo else None,
        "total_documentos": len(incluidos),
        "arquivos_ausentes": ausentes,
    }


def listar_backups():
    """Lê a pasta de backups e devolve nome e tamanho de cada ZIP, do mais antigo ao mais novo."""
    try:
        # glob("*.zip") lista só os arquivos .zip da pasta; st_mtime é a data em que cada um foi gravado.
        arquivos = sorted(diretorio("backups").glob("*.zip"), key=lambda caminho: caminho.stat().st_mtime)
        backups = [{"arquivo": caminho.name, "tamanho": caminho.stat().st_size} for caminho in arquivos]
    except OSError as erro:
        documentos.falhar(500, "Falha ao ler a pasta de backups", erro, operacao="ERRO_LEITURA")

    documentos.logger.info("LISTAGEM_BACKUPS total=%d", len(backups))
    return backups


def localizar_backup(nome):
    """Devolve o caminho do backup pedido, ou 404 se ele não existir."""
    pasta = diretorio("backups").resolve()
    caminho = (pasta / nome).resolve()
    # Só aceita um .zip que esteja diretamente na pasta de backups (bloqueia nomes como "../config.yaml").
    if caminho.parent != pasta or caminho.suffix != ".zip" or not caminho.is_file():
        documentos.falhar(404, f"Backup não encontrado: {nome}", operacao="BACKUP_NAO_ENCONTRADO")

    documentos.logger.info("DOWNLOAD_BACKUP arquivo=%s", caminho.name)
    return caminho
