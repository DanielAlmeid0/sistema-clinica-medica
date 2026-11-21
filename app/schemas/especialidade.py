from sqlmodel import Field, SQLModel

from app.models.especialidade import EspecialidadeBase
from app.schemas.paginacao import Paginacao

class EspecialidadeCreate(EspecialidadeBase):
    pass

class EspecialidadePublic(EspecialidadeBase):
    id: int

class EspecialidadeUpdate(SQLModel):
    nome: str | None = Field(default=None, min_length=3, max_length=100)
    descricao: str | None = Field(default=None, max_length=300)

class PaginaEspecialidades(SQLModel):
    dados: list[EspecialidadePublic]
    paginacao: Paginacao