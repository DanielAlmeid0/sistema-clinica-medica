from pydantic import NaiveDatetime
from sqlmodel import Field, SQLModel

from app.models.agenda import BloqueioAgendaBase


class BloqueioCreate(SQLModel):
    data_hora_inicio: NaiveDatetime
    data_hora_fim: NaiveDatetime
    motivo: str = Field(min_length=3, max_length=200)


class BloqueioPublic(BloqueioAgendaBase):
    id: int
