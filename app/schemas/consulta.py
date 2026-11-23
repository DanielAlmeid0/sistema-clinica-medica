from pydantic import NaiveDatetime
from sqlmodel import SQLModel

from app.models.consulta import ConsultaBase


class ConsultaCreate(SQLModel):
    paciente_id: int
    medico_id: int
    especialidade_id: int
    data_hora_inicio: NaiveDatetime


class ConsultaPublic(ConsultaBase):
    id: int
