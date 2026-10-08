"""Popula o cofre com documentos de exemplo, enviando cada um pela API (POST /documentos).

Uso (com o servidor rodando):
    python seed.py                       # usa http://127.0.0.1:8000
    python seed.py http://127.0.0.1:8001 # outro endereço

Rodar de novo não duplica: documentos com mesmo nome, projeto e versão já cadastrados são pulados.
"""
import json
import mimetypes
import struct
import sys
import urllib.error
import urllib.request
import zlib
from uuid import uuid4

URL_API = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")


# ---------- Arquivos binários gerados aqui mesmo (sem depender de arquivos externos) ----------

def gerar_png(largura, altura, cor_fundo, cor_caixas):
    """Gera um PNG simples (fundo + duas "caixas" de diagrama) usando só zlib e struct."""
    linhas = []
    for y in range(altura):
        linha = bytearray([0])  # cada linha do PNG começa com o tipo de filtro (0 = nenhum)
        for x in range(largura):
            dentro_caixa = (10 <= y < 40) and (10 <= x < 50 or 70 <= x < 110)
            seta = (24 <= y < 26) and (50 <= x < 70)
            linha += bytes(cor_caixas if dentro_caixa or seta else cor_fundo)
        linhas.append(bytes(linha))

    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados))

    cabecalho = struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0)  # 8 bits por cor, RGB
    return (b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", cabecalho)
            + bloco(b"IDAT", zlib.compress(b"".join(linhas))) + bloco(b"IEND", b""))


def gerar_pdf(titulo, linhas):
    """Gera um PDF de uma página com texto, montando a estrutura mínima do formato à mão."""
    texto = f"BT /F1 16 Tf 50 780 Td ({titulo}) Tj /F1 11 Tf"
    for linha in linhas:
        texto += f" 0 -20 Td ({linha}) Tj"
    texto += " ET"
    objetos = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(texto)} >>\nstream\n{texto}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = b"%PDF-1.4\n"
    posicoes = []
    for numero, conteudo in enumerate(objetos, start=1):
        posicoes.append(len(pdf))
        pdf += f"{numero} 0 obj\n{conteudo}\nendobj\n".encode("latin-1")
    inicio_xref = len(pdf)
    pdf += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    pdf += "".join(f"{p:010d} 00000 n \n" for p in posicoes).encode()
    pdf += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n".encode()
    return pdf


# ---------- Documentos de exemplo (domínio: documentação de projetos de software) ----------

DOCUMENTOS = [
    # Projeto SisBiblioteca - versão 1.0
    {
        "arquivo": "requisitos_funcionais.md", "categoria": "requisitos", "projeto": "SisBiblioteca", "versao": "1.0",
        "tipo_artefato": "especificacao_requisitos", "responsavel": "Ana Souza", "data_versao": "2026-03-02",
        "descricao": "Requisitos funcionais do módulo de empréstimos",
        "conteudo": "# Requisitos Funcionais - SisBiblioteca\n\n"
                    "RF01 - O sistema deve permitir o cadastro de livros com título, autor, ISBN e ano.\n"
                    "RF02 - O sistema deve permitir que um aluno faça o empréstimo de até 3 livros.\n"
                    "RF03 - O sistema deve calcular multa de R$ 1,00 por dia de atraso.\n"
                    "RF04 - O bibliotecário deve poder registrar a devolução de um livro.\n",
    },
    {
        "arquivo": "requisitos_nao_funcionais.txt", "categoria": "requisitos", "projeto": "SisBiblioteca", "versao": "1.0",
        "tipo_artefato": "especificacao_requisitos", "responsavel": "Ana Souza", "data_versao": "2026-03-02",
        "descricao": "Requisitos de desempenho, segurança e usabilidade",
        "conteudo": "REQUISITOS NAO FUNCIONAIS - SisBiblioteca v1.0\n\n"
                    "RNF01 - Tempo de resposta das consultas inferior a 2 segundos.\n"
                    "RNF02 - Senhas armazenadas com hash.\n"
                    "RNF03 - Interface acessível em navegadores de celular.\n",
    },
    {
        "arquivo": "diagrama_casos_de_uso.png", "categoria": "arquitetura", "projeto": "SisBiblioteca", "versao": "1.0",
        "tipo_artefato": "diagrama", "responsavel": "Bruno Lima", "data_versao": "2026-03-05",
        "descricao": "Diagrama de casos de uso do empréstimo",
        "conteudo": gerar_png(120, 50, (255, 255, 255), (52, 101, 164)),
    },
    {
        "arquivo": "plano_de_testes.csv", "categoria": "testes", "projeto": "SisBiblioteca", "versao": "1.0",
        "tipo_artefato": "plano_testes", "responsavel": "Carla Mendes", "data_versao": "2026-03-10",
        "descricao": "Casos de teste do módulo de empréstimos",
        "conteudo": "id,caso_de_teste,requisito,resultado_esperado\n"
                    "CT01,Emprestar livro disponível,RF02,Empréstimo registrado\n"
                    "CT02,Emprestar o 4º livro,RF02,Operação bloqueada\n"
                    "CT03,Devolver com 5 dias de atraso,RF03,Multa de R$ 5\n",
    },
    {
        "arquivo": "manual_do_usuario.pdf", "categoria": "manual", "projeto": "SisBiblioteca", "versao": "1.0",
        "tipo_artefato": "manual", "responsavel": "Diego Rocha", "data_versao": "2026-03-15",
        "descricao": "Manual do usuário para bibliotecários",
        "conteudo": gerar_pdf("Manual do Usuario - SisBiblioteca 1.0", [
            "1. Acesse o sistema com seu login institucional.",
            "2. Use o menu Emprestimos para registrar uma retirada.",
            "3. Use o menu Devolucoes para registrar a entrega.",
        ]),
    },
    # Projeto SisBiblioteca - versão 1.1
    {
        "arquivo": "release_notes.md", "categoria": "gestao", "projeto": "SisBiblioteca", "versao": "1.1",
        "tipo_artefato": "release_notes", "responsavel": "Ana Souza", "data_versao": "2026-05-20",
        "descricao": "Notas da versão 1.1",
        "conteudo": "# SisBiblioteca 1.1\n\n## Novidades\n- Reserva de livros pela internet.\n- Aviso por e-mail 2 dias antes do vencimento.\n\n"
                    "## Correções\n- Multa era calculada contando o dia da devolução.\n",
    },
    {
        "arquivo": "requisitos_funcionais.md", "categoria": "requisitos", "projeto": "SisBiblioteca", "versao": "1.1",
        "tipo_artefato": "especificacao_requisitos", "responsavel": "Ana Souza", "data_versao": "2026-05-12",
        "descricao": "Requisitos funcionais revisados com reservas",
        "conteudo": "# Requisitos Funcionais - SisBiblioteca 1.1\n\n"
                    "RF01 a RF04 - mantidos da versão 1.0.\n"
                    "RF05 - O aluno deve poder reservar um livro emprestado.\n"
                    "RF06 - O sistema deve enviar aviso de vencimento por e-mail.\n",
    },
    {
        "arquivo": "relatorio_de_testes.json", "categoria": "testes", "projeto": "SisBiblioteca", "versao": "1.1",
        "tipo_artefato": "relatorio_testes", "responsavel": "Carla Mendes", "data_versao": "2026-05-18",
        "descricao": "Resultado da execução dos testes da versão 1.1",
        "conteudo": json.dumps({
            "versao": "1.1", "executados": 24, "aprovados": 23, "reprovados": 1,
            "falhas": [{"caso": "CT07", "descricao": "E-mail de aviso não enviado em feriado"}],
        }, ensure_ascii=False, indent=2),
    },
    # Projeto AppDelivery - versão 2.0
    {
        "arquivo": "documento_de_arquitetura.md", "categoria": "arquitetura", "projeto": "AppDelivery", "versao": "2.0",
        "tipo_artefato": "documento_arquitetura", "responsavel": "Bruno Lima", "data_versao": "2026-06-01",
        "descricao": "Visão geral da arquitetura em microsserviços",
        "conteudo": "# Arquitetura - AppDelivery 2.0\n\n"
                    "- API Gateway recebe as requisições do aplicativo.\n"
                    "- Serviço de Pedidos, Serviço de Pagamentos e Serviço de Entregas.\n"
                    "- Comunicação assíncrona por fila de mensagens.\n",
    },
    {
        "arquivo": "diagrama_de_componentes.png", "categoria": "arquitetura", "projeto": "AppDelivery", "versao": "2.0",
        "tipo_artefato": "diagrama", "responsavel": "Bruno Lima", "data_versao": "2026-06-01",
        "descricao": "Diagrama de componentes dos microsserviços",
        "conteudo": gerar_png(120, 50, (245, 245, 245), (204, 85, 0)),
    },
    {
        "arquivo": "contrato_api_pedidos.yaml", "categoria": "arquitetura", "projeto": "AppDelivery", "versao": "2.0",
        "tipo_artefato": "especificacao_api", "responsavel": "Eduarda Alves", "data_versao": "2026-06-03",
        "descricao": "Contrato OpenAPI do serviço de pedidos",
        "conteudo": "openapi: 3.0.0\ninfo:\n  title: API de Pedidos\n  version: 2.0.0\npaths:\n"
                    "  /pedidos:\n    post:\n      summary: Cria um pedido\n"
                    "  /pedidos/{id}:\n    get:\n      summary: Consulta um pedido\n",
    },
    {
        "arquivo": "ata_reuniao_sprint_12.txt", "categoria": "gestao", "projeto": "AppDelivery", "versao": "2.0",
        "tipo_artefato": "ata_reuniao", "responsavel": "Diego Rocha", "data_versao": "2026-06-10",
        "descricao": "Ata da revisão da sprint 12",
        "conteudo": "ATA - REVISAO DA SPRINT 12\nData: 10/06/2026\n\n"
                    "Concluido: rastreamento do entregador em tempo real.\n"
                    "Pendente: pagamento por PIX (movido para a sprint 13).\n"
                    "Decisao: congelar a versao 2.0 em 20/06.\n",
    },
    {
        "arquivo": "casos_de_teste_pagamento.csv", "categoria": "testes", "projeto": "AppDelivery", "versao": "2.0",
        "tipo_artefato": "plano_testes", "responsavel": "Carla Mendes", "data_versao": "2026-06-12",
        "descricao": "Casos de teste do serviço de pagamentos",
        "conteudo": "id,cenario,entrada,resultado_esperado\n"
                    "PG01,Cartão válido,cartao=4111...,Pagamento aprovado\n"
                    "PG02,Cartão recusado,cartao=4000...,Pedido não confirmado\n"
                    "PG03,Tempo esgotado no gateway,timeout,Nova tentativa automática\n",
    },
    # Projeto PortalAcademico - versão 0.9
    {
        "arquivo": "visao_do_produto.pdf", "categoria": "requisitos", "projeto": "PortalAcademico", "versao": "0.9",
        "tipo_artefato": "documento_visao", "responsavel": "Eduarda Alves", "data_versao": "2026-08-04",
        "descricao": "Documento de visão do portal acadêmico",
        "conteudo": gerar_pdf("Visao do Produto - PortalAcademico", [
            "Problema: alunos consultam notas e horarios em sistemas diferentes.",
            "Solucao: um portal unico com notas, horarios e matricula.",
            "Usuarios: alunos, professores e coordenacao.",
        ]),
    },
    {
        "arquivo": "backlog_do_produto.csv", "categoria": "gestao", "projeto": "PortalAcademico", "versao": "0.9",
        "tipo_artefato": "backlog", "responsavel": "Diego Rocha", "data_versao": "2026-08-06",
        "descricao": "Backlog priorizado para a primeira entrega",
        "conteudo": "id,historia,prioridade,estimativa\n"
                    "US01,Como aluno quero ver minhas notas,alta,5\n"
                    "US02,Como aluno quero ver meu horário,alta,3\n"
                    "US03,Como professor quero lançar notas,média,8\n",
    },
    {
        "arquivo": "guia_de_contribuicao.md", "categoria": "manual", "projeto": "PortalAcademico", "versao": "0.9",
        "tipo_artefato": "manual", "responsavel": "Bruno Lima", "data_versao": "2026-08-08",
        "descricao": "Padrões de código e fluxo de Git da equipe",
        "conteudo": "# Guia de Contribuição\n\n1. Crie uma branch a partir da main: feat/<nome>.\n"
                    "2. Faça commits pequenos com mensagens no padrão feat:/fix:.\n"
                    "3. Abra um Pull Request e peça revisão de um colega.\n",
    },
]


# ---------- Envio pela API ----------

def montar_multipart(campos, nome_arquivo, conteudo):
    """Monta o corpo multipart/form-data (o mesmo formato que um formulário com upload usa)."""
    fronteira = uuid4().hex
    partes = []
    for nome, valor in campos.items():
        partes.append(f'--{fronteira}\r\nContent-Disposition: form-data; name="{nome}"\r\n\r\n{valor}\r\n'.encode("utf-8"))
    tipo = mimetypes.guess_type(nome_arquivo)[0] or "application/octet-stream"
    partes.append(
        f'--{fronteira}\r\nContent-Disposition: form-data; name="arquivo"; filename="{nome_arquivo}"\r\n'
        f"Content-Type: {tipo}\r\n\r\n".encode("utf-8") + conteudo + b"\r\n"
    )
    partes.append(f"--{fronteira}--\r\n".encode("utf-8"))
    return b"".join(partes), f"multipart/form-data; boundary={fronteira}"


def requisicao(metodo, caminho, corpo=None, tipo=None):
    pedido = urllib.request.Request(URL_API + caminho, data=corpo, method=metodo)
    if tipo:
        pedido.add_header("Content-Type", tipo)
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def main():
    try:
        existentes = requisicao("GET", "/documentos")
    except urllib.error.URLError as erro:
        print(f"Não consegui acessar a API em {URL_API} ({erro}).")
        print("Inicie o servidor antes: python -m uvicorn main:app --reload")
        sys.exit(1)

    ja_cadastrados = {(d["nome_original"], d["projeto"], d["versao"]) for d in existentes}
    enviados = pulados = falhas = 0

    for item in DOCUMENTOS:
        chave = (item["arquivo"], item["projeto"], item["versao"])
        if chave in ja_cadastrados:
            print(f"  já existe   {item['projeto']} {item['versao']}  {item['arquivo']}")
            pulados += 1
            continue

        conteudo = item["conteudo"]
        if isinstance(conteudo, str):
            conteudo = conteudo.encode("utf-8")
        campos = {campo: item[campo] for campo in
                  ("categoria", "descricao", "projeto", "versao", "tipo_artefato", "responsavel", "data_versao")}
        corpo, tipo = montar_multipart(campos, item["arquivo"], conteudo)

        try:
            documento = requisicao("POST", "/documentos", corpo, tipo)
            print(f"  enviado     {item['projeto']} {item['versao']}  {item['arquivo']}  (id={documento['id']})")
            enviados += 1
        except urllib.error.HTTPError as erro:
            print(f"  FALHOU      {item['arquivo']}: HTTP {erro.code} {erro.read().decode('utf-8', 'replace')}")
            falhas += 1

    print(f"\nEnviados: {enviados} | Já existiam: {pulados} | Falhas: {falhas}")
    estatisticas = requisicao("GET", "/documentos/estatisticas")
    print(f"Total no cofre: {estatisticas['total_documentos']} documentos")
    print(f"Por extensão: {estatisticas['por_extensao']}")
    print(f"Por categoria: {estatisticas['por_categoria']}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
