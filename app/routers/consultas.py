from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.models import Consulta
from app.schemas.consulta import ConsultaCreate, ConsultaPublic
from app.services.agendamento import agendar_consulta

router = APIRouter(prefix="/consultas", tags=["Consultas"])


@router.post("/", response_model=ConsultaPublic, status_code=201)
def criar_consulta(dados: ConsultaCreate, session: Session = Depends(get_session)):
    return agendar_consulta(session, dados)


@router.get("/{consulta_id}", response_model=ConsultaPublic)
def buscar_consulta(consulta_id: int, session: Session = Depends(get_session)):
    consulta = session.get(Consulta, consulta_id)

    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    return consulta
