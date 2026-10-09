<div align="center">

# 🗄️ Cofre Digital de Arquivos

### Documentação de Projetos de Software

API para armazenar, consultar, proteger, verificar e recuperar os artefatos de documentação de projetos de software.

Trabalho Prático 1 · **QXD0099 – Desenvolvimento de Software para Persistência** · UFC – Campus Quixadá

<br>

<img alt="Python 3.14" src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img alt="FastAPI 0.141" src="https://img.shields.io/badge/FastAPI-0.141-009688?style=for-the-badge&logo=fastapi&logoColor=white">
<img alt="Pydantic 2.13" src="https://img.shields.io/badge/Pydantic-2.13-E92063?style=for-the-badge&logo=pydantic&logoColor=white">
<img alt="Uvicorn 0.52" src="https://img.shields.io/badge/Uvicorn-0.52-2F2F2F?style=for-the-badge">
<img alt="PyYAML 6.0" src="https://img.shields.io/badge/PyYAML-6.0-CB171E?style=for-the-badge&logo=yaml&logoColor=white">
<img alt="Swagger OpenAPI" src="https://img.shields.io/badge/Swagger-OpenAPI-85EA2D?style=for-the-badge&logo=swagger&logoColor=black">

<img alt="JSON metadados" src="https://img.shields.io/badge/JSON-metadados-000000?style=for-the-badge&logo=json&logoColor=white">
<img alt="YAML configuração" src="https://img.shields.io/badge/YAML-configura%C3%A7%C3%A3o-CB171E?style=for-the-badge&logo=yaml&logoColor=white">
<img alt="CSV exportação" src="https://img.shields.io/badge/CSV-exporta%C3%A7%C3%A3o-217346?style=for-the-badge">
<img alt="ZIP backups" src="https://img.shields.io/badge/ZIP-backups-6E4C13?style=for-the-badge">
<img alt="Logs logging" src="https://img.shields.io/badge/Logs-logging-4B5563?style=for-the-badge">
<img alt="SHA-256 integridade" src="https://img.shields.io/badge/SHA--256-integridade-1F6FEB?style=for-the-badge">

<img alt="Git" src="https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white">
<img alt="GitHub" src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white">
<img alt="Sem banco de dados persistência em arquivos" src="https://img.shields.io/badge/Sem_banco_de_dados-persist%C3%AAncia_em_arquivos-555555?style=for-the-badge">

</div>

---

## Sumário

- 👥 [Integrantes](#integrantes)
- 📌 [Tema recebido](#tema-recebido)
- 🎯 [Objetivo](#objetivo)
- 🧰 [Requisitos](#requisitos)
- 📚 [Bibliotecas utilizadas](#bibliotecas-utilizadas)
- 📦 [Instalação](#instalação)
- 🚀 [Execução](#execução)
- 🗂️ [Estrutura do projeto](#estrutura-do-projeto)
- ⚙️ [Configuração](#configuração)
- 🏷️ [Metadados específicos do domínio](#metadados-específicos-do-domínio)
- ⭐ [Funcionalidade específica do tema (F16)](#funcionalidade-específica-do-tema-f16)
- 🔌 [Principais endpoints](#principais-endpoints)
- 💡 [Exemplos de utilização](#exemplos-de-utilização)
- 📝 [Logging](#logging)
- 🚨 [Tratamento de erros](#tratamento-de-erros)

---

## Integrantes

- João Guilherme Gadelha Abreu De Souza
- Pedro Henrique Sampaio de Sousa

## Tema recebido

**Tema 6 — Documentação de Projetos de Software.**

O cofre guarda os artefatos de documentação produzidos ao longo de um projeto de software (especificações de requisitos, diagramas, planos e relatórios de testes, manuais, atas, release notes etc.), organizados por **projeto** e **versão**.

## Objetivo

API em Python + FastAPI que **armazena, consulta, protege, verifica a integridade, exporta e recupera** arquivos digitais, mantendo os metadados de cada um em arquivo. Ao receber um documento, a aplicação:

1. recebe o arquivo pela API;
2. grava o arquivo no sistema de arquivos com um nome único;
3. identifica extensão, tipo MIME e tamanho;
4. gera um identificador único (UUID);
5. calcula o hash SHA-256;
6. registra os metadados em `documentos.json`;
7. registra a operação no log.

Depois disso o documento pode ser consultado, baixado, atualizado, excluído, verificado, exportado em CSV e incluído em backups.

Formatos utilizados:

| Formato | Uso no sistema |
|---|---|
| **JSON** | Persistência principal dos metadados (`storage/metadata/documentos.json`) |
| **YAML** | Configuração externa (`config.yaml`) e configuração do log (`logging.yaml`) |
| **CSV** | Exportação do catálogo (`GET /exportar/csv`) |
| **Log** | Registro das operações (`storage/logs/sistema.log`) |
| **Binários** | Os próprios documentos (PDF, PNG...) são gravados e devolvidos byte a byte |
| **ZIP** | Backups e pacote de recuperação de versão |

Nenhum banco de dados é usado: tudo é persistido em arquivos.

## Requisitos

- **Python 3.14** (versão usada no desenvolvimento e nos testes)
- `pip` para instalar as dependências
- Sistema operacional: Windows, Linux ou macOS

## Bibliotecas utilizadas

| Biblioteca | Para que serve no projeto |
|---|---|
| **FastAPI** | Framework web: define os endpoints, valida as entradas e gera a documentação interativa em `/docs` |
| **Uvicorn** | Servidor que executa a aplicação FastAPI |
| **Pydantic** | Define o modelo `Documento` e valida os metadados (tipos, formato do SHA-256, campos obrigatórios) |
| **PyYAML** | Lê os arquivos `config.yaml` e `logging.yaml` |
| **python-multipart** | Permite ao FastAPI receber arquivos enviados por formulário (`multipart/form-data`) |

Da biblioteca padrão do Python: `json` (metadados), `csv` (exportação), `hashlib` (SHA-256), `zipfile` (backups), `logging` (log), `mimetypes` (tipo MIME), `uuid` (identificadores), `pathlib` (caminhos) e `threading` (trava contra gravações simultâneas no JSON).

## Instalação

1. Baixe o projeto e entre na pasta:

   ```bash
   git clone https://github.com/JoaoGui1430/cofre-documentacao-persistencia.git
   cd cofre-documentacao-persistencia
   ```

2. (Opcional, recomendado) Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. Instale as dependências:

   ```bash
   python -m pip install -r requirements.txt
   ```

## Execução

1. Inicie a API:

   ```bash
   python -m uvicorn main:app --reload
   ```

   A API fica em `http://127.0.0.1:8000` e a documentação interativa (Swagger) em **`http://127.0.0.1:8000/docs`**. As pastas de `storage/` são criadas automaticamente.

2. Em **outro terminal**, com a API rodando, cadastre os documentos de exemplo:

   ```bash
   python seed.py
   ```

   O script envia 16 documentos pela própria API (`POST /documentos`), então cada um passa pelo fluxo real de upload (id, SHA-256, JSON e log). Ele pode ser executado mais de uma vez: documentos já cadastrados (mesmo nome, projeto e versão) são pulados. Se a API estiver em outro endereço: `python seed.py http://127.0.0.1:8001`.

   A pasta `storage/` não vai para o repositório, por isso quem baixa o projeto precisa rodar o seed para ter os dados.

> O `config.yaml` é lido uma única vez, quando a API inicia. Depois de alterá-lo, **reinicie o servidor** (o `--reload` só observa arquivos `.py`).

## Estrutura do projeto

```
cofre-documentacao-persistencia/
├── main.py                       # Cria a aplicação, registra as rotas e os tratadores de erro
├── config.yaml                   # Configuração externa (diretórios, limite de upload, hash, log, backup)
├── logging.yaml                  # Formato das linhas de log e destinos (terminal e arquivo)
├── seed.py                       # Cadastra os 16 documentos de exemplo pela API
├── requirements.txt
├── app/
│   └── documento.py              # Modelos Pydantic: Documento e DocumentoAtualizacao
├── core/
│   ├── config.py                 # Lê e valida o config.yaml
│   ├── logging_config.py         # Configura o logging a partir do config.yaml + logging.yaml
│   ├── armazenamento.py          # Grava/remove os arquivos físicos e calcula o hash no upload
│   ├── repositorio.py            # Lê e grava o documentos.json (gravação atômica + trava)
│   └── serializacao.py           # Trava compartilhada para operações de armazenamento
├── routers/                      # Endpoints da API
│   ├── documentos.py             # CRUD, filtros, estatísticas, integridade individual, recuperação de versão
│   ├── integridade.py            # Integridade global
│   ├── exportacoes.py            # Exportação CSV
│   └── backup.py                 # Criação, listagem, download e restauração de backups
├── services/                     # Regras de negócio usadas pelos routers
│   ├── documentos_service.py
│   ├── estatisticas_service.py
│   ├── integridade_service.py
│   ├── exportacao_service.py
│   └── backup_service.py
├── utils/
│   └── hash.py                   # Cálculo do SHA-256 de arquivos e de conteúdo
└── storage/                      # Criada ao executar (não versionada)
    ├── arquivos/                 # Arquivos originais, salvos como <id>_<nome_original>
    ├── metadata/documentos.json  # Metadados de todos os documentos
    ├── logs/sistema.log          # Log das operações
    ├── exportacoes/              # CSVs exportados e ZIPs de recuperação de versão
    └── backups/                  # Backups ZIP
```

Cada diretório de `storage/` tem uma responsabilidade única, e todos os caminhos são definidos no `config.yaml`.

## Configuração

Toda a configuração externa fica no arquivo `config.yaml`, na raiz do projeto:

```yaml
aplicacao:
  nome: "Cofre de Documentação de Projetos de Software"

diretorios:
  arquivos: "storage/arquivos"
  metadata: "storage/metadata"
  exportacoes: "storage/exportacoes"
  backups: "storage/backups"

upload:
  tamanho_maximo_mb: 20

hash:
  algoritmo: "sha256"

logging:
  arquivo: "storage/logs/sistema.log"
  nivel: "INFO"

backup:
  formato: "zip"
```

Todos os valores são usados pelo sistema. Por exemplo: trocar `logging.nivel` para `WARNING` faz as linhas INFO deixarem de ser gravadas; trocar `diretorios.backups` muda a pasta onde os backups são criados; reduzir `upload.tamanho_maximo_mb` faz uploads maiores serem recusados com 400.

Ao iniciar, o arquivo é **validado**. Se estiver ausente, com YAML inválido ou com valores inválidos, a API não sobe e mostra uma mensagem listando todos os problemas, por exemplo:

```
ERRO DE CONFIGURAÇÃO: config.yaml inválido:
  - 'hash.algoritmo' não suportado: md5 (use sha256)
  - 'logging.nivel' inválido: TUDO (use CRITICAL, DEBUG, ERROR, INFO, WARNING)
Corrija o arquivo e inicie o servidor novamente.
```

## Metadados específicos do domínio

Além dos metadados gerais (`id`, `nome_original`, `nome_armazenado`, `extensao`, `tipo_mime`, `tamanho`, `categoria`, `descricao`, `data_upload`, `sha256`), cada documento tem:

| Campo | Tipo | Significado | Exemplo |
|---|---|---|---|
| `projeto` | texto | Projeto de software ao qual o artefato pertence | `SisBiblioteca` |
| `versao` | texto | Versão do projeto à qual o artefato se refere | `1.1` |
| `tipo_artefato` | texto | Tipo de artefato de documentação | `especificacao_requisitos`, `diagrama`, `plano_testes`, `manual`, `release_notes` |
| `responsavel` | texto | Pessoa responsável pelo artefato | `Ana Souza` |
| `data_versao` | data (AAAA-MM-DD) | Data da versão do projeto | `2026-05-12` |

Exemplo de registro em `documentos.json`:

```json
{
  "id": "bd10f7fe-c7a7-4247-af42-be31914ef3fa",
  "nome_original": "requisitos_funcionais.md",
  "nome_armazenado": "bd10f7fe-c7a7-4247-af42-be31914ef3fa_requisitos_funcionais.md",
  "extensao": ".md",
  "tipo_mime": "text/markdown",
  "tamanho": 201,
  "descricao": "Requisitos funcionais revisados com reservas",
  "categoria": "requisitos",
  "data_upload": "2026-10-08T21:01:20",
  "sha256": "9f0c1dea599e22b982df4d0be0d7767da2c8c5de9c1c34c035af5979af2bd52d",
  "projeto": "SisBiblioteca",
  "versao": "1.1",
  "tipo_artefato": "especificacao_requisitos",
  "responsavel": "Ana Souza",
  "data_versao": "2026-05-12"
}
```

Os metadados do domínio são usados nos **filtros** (`projeto`, `versao`), nas **estatísticas** (`por_projeto`), no **backup seletivo** (`projeto`, `versao`) e na **funcionalidade específica do tema** (`projeto`, `versao`).

## Funcionalidade específica do tema (F16)

### Recuperação de uma versão do projeto

**Endpoint:** `GET /documentos/versao/download?projeto=<projeto>&versao=<versao>`

Gera e devolve um **pacote ZIP com todos os artefatos de uma versão de um projeto**, como uma "release" da documentação. A funcionalidade:

1. lê os documentos **persistidos** em `documentos.json` e seleciona os que têm o `projeto` **e** a `versao` informados (metadados do domínio);
2. para cada documento, **recalcula o SHA-256** do arquivo armazenado e compara com o hash do upload. Se algum arquivo tiver sido alterado, a recuperação é recusada com **409** (não se entrega uma versão corrompida);
3. monta o ZIP com:
   - `arquivos/<id>/<nome_original>` — os arquivos originais;
   - `documentos.json` — os metadados dos documentos incluídos;
4. grava o pacote em `storage/exportacoes/release_<uuid>.zip`, devolve o arquivo para download e registra `RECUPERACAO_VERSAO` no log.

Respostas: **200** com o ZIP; **404** se não houver documentos para aquele projeto e versão; **409** se algum arquivo falhar na verificação de integridade; **400** se `projeto` ou `versao` vierem em branco.

Exemplo (com os dados do seed, a versão 1.1 do SisBiblioteca tem 3 documentos):

```bash
curl -o sisbiblioteca_1.1.zip "http://127.0.0.1:8000/documentos/versao/download?projeto=SisBiblioteca&versao=1.1"
```

## Principais endpoints

| Método | Rota | Descrição | Sucesso |
|---|---|---|---|
| POST | `/documentos` | **F1** Upload de documento (arquivo + metadados em formulário) | 201 |
| GET | `/documentos` | **F2/F7** Lista todos os documentos (metadados completos), com filtros opcionais | 200 |
| GET | `/documentos/estatisticas` | **F8** Estatísticas do cofre | 200 |
| GET | `/documentos/versao/download` | **F16** ZIP com todos os documentos de um projeto e versão | 200 |
| GET | `/documentos/{id}` | **F3** Metadados de um documento | 200 |
| GET | `/documentos/{id}/download` | **F4** Download do arquivo original | 200 |
| PUT | `/documentos/{id}` | **F5** Atualiza metadados (não altera o arquivo) | 200 |
| DELETE | `/documentos/{id}` | **F6** Exclui documento (registro + arquivo) | 204 |
| GET | `/documentos/{id}/integridade` | **F9** Verifica a integridade de um documento | 200 |
| GET | `/integridade` | **F10** Verifica a integridade de todos os documentos | 200 |
| GET | `/exportar/csv` | **F13** Exporta o catálogo em CSV | 200 |
| POST | `/backup` | **F14** Cria backup ZIP geral ou seletivo | 201 |
| GET | `/backups` | **F15** Lista os backups existentes | 200 |
| GET | `/backups/{nome}` | Baixa um backup | 200 |
| POST | `/backups/{nome}/restaurar` | Restaura um backup em um cofre vazio | 200 |

### Detalhes e decisões de cada endpoint

**F1 — Upload.** Campos do formulário: `arquivo` (obrigatório), `categoria`, `projeto`, `versao`, `tipo_artefato`, `responsavel`, `data_versao` (obrigatórios) e `descricao` (opcional). O arquivo é gravado como `<id>_<nome_original>`, então dois arquivos com o mesmo nome nunca se sobrescrevem. Arquivo vazio, sem nome ou maior que `upload.tamanho_maximo_mb` é recusado com 400.

**F2 — Listagem.** Devolve a lista com os **metadados completos** de cada documento, lidos do `documentos.json`.

**F5 — Atualização.** Campos alteráveis: `categoria`, `descricao`, `projeto`, `versao`, `tipo_artefato`, `responsavel`, `data_versao`. Campos como `nome_original`, `tamanho` ou `sha256` não podem ser alterados (422), e o arquivo físico nunca é modificado.

**F6 — Exclusão (comportamento adotado).** Remove o registro do `documentos.json` **e** o arquivo de `storage/arquivos/`. A operação é feita de forma segura: o arquivo é primeiro renomeado para `.tmp`, o JSON é gravado e só então o `.tmp` é apagado; se a gravação do JSON falhar, o arquivo volta ao lugar e nada é perdido. Se o arquivo físico **já não existir**, o registro é removido mesmo assim (para não deixar um registro órfão no JSON) e a operação é registrada como `WARNING EXCLUSAO_SEM_ARQUIVO`. Backups já criados não são alterados.

**F7 — Filtros.** Podem ser combinados. Filtros gerais: `categoria` e `extensao`. Filtros do domínio: `projeto` e `versao`. A comparação é exata. Um filtro desconhecido (ex.: `?projetto=X`) é recusado com 400, para não devolver a lista inteira por engano.

**Extensão — decisão de formato.** No `documentos.json` e no CSV a extensão é gravada **com ponto e em minúsculas** (`".pdf"`), como no exemplo de registro do enunciado. No filtro, `extensao=pdf`, `extensao=.pdf` e `extensao=PDF` são equivalentes. Nas estatísticas a extensão aparece **sem ponto** (`"pdf": 2`), como no exemplo de estatísticas do enunciado; arquivos sem extensão aparecem como `"sem_extensao"`.

**F8 — Estatísticas.** Calculadas a partir do `documentos.json`: `total_documentos`, `espaco_utilizado_bytes`, `por_extensao`, `por_categoria` e a estatística do domínio `por_projeto`.

**F9 / F10 — Integridade.** Recalcula o SHA-256 do arquivo armazenado e compara com o hash registrado no upload. Detecta alteração manual do arquivo. O F10 informa quantos foram verificados, íntegros e alterados, e lista os documentos cujo arquivo físico não foi localizado.

**F14 — Backup.** `POST /backup` gera um backup **geral** (`backup_AAAA-MM-DD_HHMM.zip`). Com `?projeto=` e/ou `?versao=` gera um backup **seletivo** apenas desses documentos (`backup_seletivo_AAAA-MM-DD_HHMM.zip`). O ZIP contém `documentos/` (arquivos originais) e `metadata/documentos.json`. Backups anteriores nunca são sobrescritos: dois backups no mesmo minuto recebem sufixo (`_2`, `_3`...).

**Restauração de backup.** `POST /backups/{nome}/restaurar` recria os arquivos e o `documentos.json` a partir de um backup. Só é permitida com o **cofre vazio** (senão 409), para nunca misturar ou sobrescrever documentos existentes. Antes de gravar, confere a estrutura do ZIP, o tamanho e o SHA-256 de cada arquivo.

## Exemplos de utilização

Os exemplos usam `curl`. No **PowerShell do Windows**, use `curl.exe` (o `curl` do PowerShell 5 é outro comando). Também é possível testar tudo pelo Swagger em `http://127.0.0.1:8000/docs`. Substitua `<id>` por um id real (obtido na listagem).

**Upload (F1):**

```bash
curl -X POST http://127.0.0.1:8000/documentos \
  -F "arquivo=@manual.pdf" \
  -F "categoria=manual" \
  -F "descricao=Manual do usuário" \
  -F "projeto=SisBiblioteca" \
  -F "versao=1.0" \
  -F "tipo_artefato=manual" \
  -F "responsavel=Ana Souza" \
  -F "data_versao=2026-03-15"
```

**Listagem e filtros (F2/F7):**

```bash
curl http://127.0.0.1:8000/documentos
curl "http://127.0.0.1:8000/documentos?projeto=SisBiblioteca&versao=1.1"
curl "http://127.0.0.1:8000/documentos?extensao=pdf&categoria=manual"
```

**Consulta, download, atualização e exclusão (F3–F6):**

```bash
curl http://127.0.0.1:8000/documentos/<id>
curl -o arquivo_baixado.pdf http://127.0.0.1:8000/documentos/<id>/download
curl -X PUT http://127.0.0.1:8000/documentos/<id> \
  -H "Content-Type: application/json" \
  -d '{"descricao": "Manual revisado", "versao": "1.1"}'
curl -X DELETE http://127.0.0.1:8000/documentos/<id>
```

**Estatísticas (F8):**

```bash
curl http://127.0.0.1:8000/documentos/estatisticas
```

```json
{
  "total_documentos": 16,
  "espaco_utilizado_bytes": 4611,
  "por_extensao": {"md": 5, "txt": 2, "png": 2, "csv": 3, "pdf": 2, "json": 1, "yaml": 1},
  "por_categoria": {"requisitos": 4, "arquitetura": 4, "testes": 3, "manual": 2, "gestao": 3},
  "por_projeto": {"SisBiblioteca": 8, "AppDelivery": 5, "PortalAcademico": 3}
}
```

**Integridade (F9/F10):**

```bash
curl http://127.0.0.1:8000/documentos/<id>/integridade
curl http://127.0.0.1:8000/integridade
```

```json
{"id": "bd10f7fe-...", "nome": "requisitos_funcionais.md", "hash_original": "9f0c1dea...", "hash_atual": "9f0c1dea...", "integro": true}
```

Para ver a detecção de alteração: abra um arquivo em `storage/arquivos/`, altere o conteúdo e chame a integridade de novo; a resposta passa a ter `"integro": false` e o log registra `WARNING INTEGRIDADE_FALHOU`.

**Exportação CSV (F13):**

```bash
curl -o catalogo.csv http://127.0.0.1:8000/exportar/csv
```

```
id,nome_original,nome_armazenado,extensao,tipo_mime,tamanho,descricao,categoria,data_upload,sha256,projeto,versao,tipo_artefato,responsavel,data_versao
bd10f7fe-...,requisitos_funcionais.md,bd10f7fe-..._requisitos_funcionais.md,.md,text/markdown,201,Requisitos funcionais revisados com reservas,requisitos,2026-10-08T21:01:20,9f0c1dea...,SisBiblioteca,1.1,especificacao_requisitos,Ana Souza,2026-05-12
```

**Backup (F14/F15) e restauração:**

```bash
curl -X POST http://127.0.0.1:8000/backup
curl -X POST "http://127.0.0.1:8000/backup?projeto=AppDelivery"
curl http://127.0.0.1:8000/backups
curl -o backup.zip http://127.0.0.1:8000/backups/<nome_do_backup>.zip
curl -X POST http://127.0.0.1:8000/backups/<nome_do_backup>.zip/restaurar
```

**Recuperação de versão (F16):**

```bash
curl -o release.zip "http://127.0.0.1:8000/documentos/versao/download?projeto=SisBiblioteca&versao=1.0"
```

## Logging

As operações são gravadas em `storage/logs/sistema.log` (caminho e nível definidos no `config.yaml`), no formato `data hora NÍVEL OPERAÇÃO chave=valor`:

```
2026-10-08 14:32:18 INFO UPLOAD id=bd10f7fe-... arquivo=requisitos_funcionais.md tamanho=201
2026-10-08 14:35:09 INFO DOWNLOAD id=bd10f7fe-... arquivo=requisitos_funcionais.md
2026-10-08 14:38:41 WARNING INTEGRIDADE_FALHOU id=bd10f7fe-... arquivo=requisitos_funcionais.md
2026-10-08 14:42:15 ERROR DOCUMENTO_NAO_ENCONTRADO id=00000000-0000-0000-0000-000000000000
```

São registradas: inicialização, upload, download, consulta, listagem, atualização, exclusão, estatísticas, verificação de integridade, exportação CSV, criação/listagem/download/restauração de backup, recuperação de versão, documentos inexistentes, erros de leitura/escrita e requisições inválidas.

Critério dos níveis:

| Nível | Quando |
|---|---|
| **INFO** | Operação concluída com sucesso |
| **WARNING** | Problema na requisição do cliente (400, 404 de backup/filtro, 409, 422) e falha de integridade |
| **ERROR** | Falha do servidor (500, leitura/escrita), documento inexistente e arquivo físico não encontrado |

## Tratamento de erros

| Código | Quando ocorre |
|---|---|
| 200 | Sucesso |
| 201 | Documento ou backup criado |
| 204 | Documento excluído |
| 400 | Upload inválido (vazio, sem nome, acima do limite), campo em branco, filtro desconhecido, nenhum campo para atualizar, backup inválido |
| 404 | Documento inexistente, arquivo físico não encontrado, backup inexistente, nenhum documento para o projeto/versão |
| 409 | Falha de integridade na recuperação de versão ou na restauração; restauração com o cofre não vazio |
| 422 | Dados inválidos (campo obrigatório ausente, data inválida, id fora do formato UUID, campo não alterável no PUT) |
| 500 | `documentos.json` com JSON inválido, erro de leitura/escrita, falha na compactação, erro inesperado |

Toda resposta de erro tem o formato `{"detail": "mensagem"}` e é registrada no log.
