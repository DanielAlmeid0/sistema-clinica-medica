from pydantic import NaiveDatetime
from sqlmodel import SQLModel

from app.models.consulta import ConsultaBase
from app.schemas.paginacao import Paginacao


class ConsultaCreate(SQLModel):
    paciente_id: int
    medico_id: int
    especialidade_id: int
    data_hora_inicio: NaiveDatetime

class ConsultaRemarcar(SQLModel):
    data_hora_inicio: NaiveDatetime


class ConsultaPublic(ConsultaBase):
    id: int


class PaginaConsultas(SQLModel):
    dados: list[ConsultaPublic]
    paginacao: Paginacao


class ConsultaDetalhada(SQLModel):
    id: int
    data_hora_inicio: NaiveDatetime
    data_hora_fim: NaiveDatetime
    status: str
    paciente_id: int
    paciente_nome: str
    medico_id: int
    medico_nome: str
    especialidade_id: int
    especialidade_nome: str


class PaginaConsultasDetalhadas(SQLModel):
    dados: list[ConsultaDetalhada]
    paginacao: Paginacao
