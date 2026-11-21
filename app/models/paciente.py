from datetime import date
from sqlmodel import Field, SQLModel

class PacienteBase(SQLModel):
    nome: str = Field(min_length=3, max_length=100, index=True)
    cpf: str = Field(min_length=11, max_length=11, unique=True, index=True)
    telefone: str = Field(min_length=10, max_length=15)
    email: str | None = Field(default=None, max_length=100, unique=True, index=True)
    data_nasc: date
    ativo: bool = Field(default=True)


class Paciente(PacienteBase, table=True):
    __tablename__ = "pacientes"

    id:int | None = Field(default=None, primary_key=True)