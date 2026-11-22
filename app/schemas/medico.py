from sqlmodel import Field, SQLModel

from app.models.medico import MedicoBase
from app.schemas.especialidade import EspecialidadePublic
from app.schemas.paginacao import Paginacao

class MedicoCreate(MedicoBase):
    pass

class MedicoPublic(MedicoBase):
    id: int

class MedicoPublicDetalhado(MedicoPublic):
    especialidades: list[EspecialidadePublic] = []

class MedicoUpdate(SQLModel):
    nome: str | None = Field(default=None, min_length=3, max_length=100)
    crm: str | None = Field(default=None, min_length=4, max_length=20)
    telefone: str | None = Field(default=None, min_length=10, max_length=15)
    email: str | None = Field(default=None, max_length=100)
    ativo: bool | None = None

class PaginaMedicos(SQLModel):
    dados: list[MedicoPublic]
    paginacao: Paginacao

class VinculoEspecialidade(SQLModel):
    especialidade_id: int
    rqe: str | None = Field(default=None, max_length=20)