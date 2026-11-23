from pydantic import NaiveDatetime
from sqlmodel import Field, Relationship, SQLModel


class ConsultaBase(SQLModel):
    paciente_id: int = Field(foreign_key="pacientes.id", index=True)
    medico_id: int = Field(foreign_key="medicos.id", index=True)
    especialidade_id: int = Field(foreign_key="especialidade.id", index=True)
    data_hora_inicio: NaiveDatetime = Field(index=True)
    data_hora_fim: NaiveDatetime
    status: str = Field(default="agendada", max_length=20, index=True)


class Consulta(ConsultaBase, table=True):
    __tablename__ = "consultas"

    id: int | None = Field(default=None, primary_key=True)
    prontuario: "Prontuario" = Relationship(back_populates="consulta")


class ProntuarioBase(SQLModel):
    consulta_id: int = Field(foreign_key="consultas.id", unique=True)
    observacoes_clinicas: str = Field(min_length=5)
    prescricao_medicamentos: str | None = Field(default=None)
    orientacoes: str | None = Field(default=None)
    data_retorno: int | None = Field(default=None, gt=0)


class Prontuario(ProntuarioBase, table=True):
    __tablename__ = "prontuarios"

    id: int | None = Field(default=None, primary_key=True)

    consulta: Consulta = Relationship(back_populates="prontuario")