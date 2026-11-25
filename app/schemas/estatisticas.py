from datetime import datetime

from sqlmodel import SQLModel


class ContagemPorStatus(SQLModel):
    status: str
    total: int


class ContagemPorEspecialidade(SQLModel):
    especialidade_id: int
    especialidade: str
    total: int


class ContagemPorMedico(SQLModel):
    medico_id: int
    medico: str
    total: int


class Estatisticas(SQLModel):
    total_pacientes: int
    total_medicos: int
    total_consultas: int
    consultas_por_status: list[ContagemPorStatus]
    consultas_por_especialidade: list[ContagemPorEspecialidade]
    consultas_por_medico: list[ContagemPorMedico]
    taxa_nao_comparecimento: float | None
    duracao_media_agenda_minutos: float | None
    primeira_consulta: datetime | None
    ultima_consulta: datetime | None
