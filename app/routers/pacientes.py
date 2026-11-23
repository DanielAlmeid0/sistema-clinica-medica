from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core.database import get_session
from app.models import Paciente
from app.schemas.paciente import PacienteCreate, PacientePublic

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.post("/", response_model=PacientePublic, status_code=201)
def criar_paciente(dados: PacienteCreate, session: Session = Depends(get_session)):
    paciente = Paciente.model_validate(dados)
    session.add(paciente)

    try:
        session.commit()
        session.refresh(paciente)
        return paciente
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Já existe um paciente com esse CPF ou email")
