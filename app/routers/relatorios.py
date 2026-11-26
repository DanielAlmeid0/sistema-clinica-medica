from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.relatorios import MedicoSemConsultas, PacienteFrequente
from app.services.relatorios import medicos_sem_consultas, pacientes_frequentes

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/medicos-sem-consultas", response_model=list[MedicoSemConsultas])
def listar_medicos_sem_consultas(
    data_inicio: date,
    data_fim: date,
    session: Session = Depends(get_session),
):
    return medicos_sem_consultas(session, data_inicio, data_fim)


@router.get("/pacientes-frequentes", response_model=list[PacienteFrequente])
def listar_pacientes_frequentes(
    minimo: int = Query(2, ge=1),
    data_inicio: date | None = None,
    data_fim: date | None = None,
    session: Session = Depends(get_session),
):
    return pacientes_frequentes(session, minimo, data_inicio, data_fim)
