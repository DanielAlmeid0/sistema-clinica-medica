from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.especialidade import Especialidade


class MedicoEspecialidade(SQLModel, table=True):
    __tablename__ = "medico_especialidades"

    medico_id: int = Field(foreign_key="medicos.id", primary_key=True)
    especialidade_id: int = Field(foreign_key="especialidade.id", primary_key=True)
    rqe: str | None = Field(default=None, max_length=20)


class MedicoBase(SQLModel):
    nome: str = Field(min_length=3, max_length=100, index=True)
    crm: str = Field(min_length=4, max_length=20, unique=True, index=True)
    telefone: str = Field(min_length=10, max_length=15)
    email: str | None = Field(default=None, max_length=100, unique=True)
    ativo: bool = Field(default=True)


class Medico(MedicoBase, table=True):
    __tablename__ = "medicos"

    id: int | None = Field(default=None, primary_key=True)

    especialidades: list["Especialidade"] = Relationship(back_populates="medicos", link_model=MedicoEspecialidade)