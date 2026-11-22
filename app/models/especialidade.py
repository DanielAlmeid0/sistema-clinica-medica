from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.medico import MedicoEspecialidade

if TYPE_CHECKING:
    from app.models.medico import Medico

class EspecialidadeBase(SQLModel):
    nome: str = Field(min_length= 3, max_length=100, unique=True, index=True)
    descricao: str | None = Field(default=None, max_length=300)

class Especialidade(EspecialidadeBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    medicos: list["Medico"] = Relationship(back_populates="especialidades", link_model=MedicoEspecialidade)