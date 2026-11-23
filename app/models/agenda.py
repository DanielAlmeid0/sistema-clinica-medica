from datetime import time
from pydantic import NaiveDatetime
from sqlmodel import Field, SQLModel

class AgendaRegularBase(SQLModel):
    medico_id: int = Field(foreign_key="medicos.id", index=True)
    especialidade_id: int = Field(foreign_key="especialidade.id", index=True)
    dia_semana: int = Field(ge=0, le=6, index=True)
    hora_inicio: time
    hora_fim: time
    duracao_consulta: int = Field(default=30, gt=0)

class AgendaRegular(AgendaRegularBase, table=True):
    __tablename__ = "Agendas_regulares"

    id:int | None = Field(default=None, primary_key=True)

class BloqueioAgendaBase(SQLModel):
    medico_id: int = Field(foreign_key="medicos.id", index=True)
    data_hora_inicio: NaiveDatetime = Field(index=True)
    data_hora_fim: NaiveDatetime = Field(index=True)
    motivo: str = Field(min_length=3, max_length=200)

class BloqueioAgenda(BloqueioAgendaBase, table=True):
    __tablename__ = "bloqueios_agenda"

    id: int | None = Field(default=None, primary_key=True)