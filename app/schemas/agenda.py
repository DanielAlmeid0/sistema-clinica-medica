from datetime import time
from pydantic import NaiveDatetime

from sqlmodel import Field, SQLModel

from app.models.agenda import AgendaRegularBase


class AgendaCreate(SQLModel):
    especialidade_id: int
    dia_semana: int = Field(ge=0, le=6, description="0 = segunda, 1 = terça, ..., 6 = domingo")
    hora_inicio: time
    hora_fim: time
    duracao_consulta: int = Field(default=30, gt=0, description="Duração de cada consulta, em minutos")

class AgendaPublic(AgendaRegularBase):
    id: int

class HorarioDisponivel(SQLModel):
    inicio: NaiveDatetime
    fim: NaiveDatetime