from datetime import date

from sqlmodel import Field, SQLModel

from app.models.paciente import PacienteBase
from app.schemas.paginacao import Paginacao


class PacienteCreate(PacienteBase):
    pass


class PacientePublic(PacienteBase):
    id: int


class PacienteUpdate(SQLModel):
    nome: str | None = Field(default=None, min_length=3, max_length=100)
    cpf: str | None = Field(default=None, min_length=11, max_length=11)
    telefone: str | None = Field(default=None, min_length=10, max_length=15)
    email: str | None = Field(default=None, max_length=100)
    data_nasc: date | None = None
    ativo: bool | None = None


class PaginaPacientes(SQLModel):
    dados: list[PacientePublic]
    paginacao: Paginacao