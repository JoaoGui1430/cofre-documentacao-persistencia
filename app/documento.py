from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class Documento(BaseModel):
    id: UUID
    nome_original: str
    nome_armazenado: str
    extensao: str
    tipo_mime: str
    tamanho: int = Field(ge=0)
    descricao: str
    categoria: str
    data_upload: datetime
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    #atributos do tema
    projeto: str
    versao: str
    tipo_artefato: str
    responsavel: str
    data_versao: date

class DocumentoAtualizacao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    categoria: str | None = None
    descricao: str | None = None
    projeto: str | None = None
    versao: str | None  = None
    tipo_artefato: str | None = None
    responsavel: str | None = None
    data_versao: date | None = None

    