from datetime import datetime

from sqlmodel import SQLModel


class MedicoSemConsultas(SQLModel):
    id: int
    nome: str
    crm: str


class PacienteFrequente(SQLModel):
    paciente_id: int
    paciente: str
    total_consultas: int
    primeira_consulta: datetime
    ultima_consulta: datetime
