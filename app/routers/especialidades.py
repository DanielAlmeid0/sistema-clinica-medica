from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import Especialidade
from app.schemas.especialidade import (
    EspecialidadeCreate,
    EspecialidadePublic,
    EspecialidadeUpdate,
    PaginaEspecialidades,
)
from app.schemas.paginacao import Paginacao

router = APIRouter(prefix="/especialidades", tags=["Especialidades"])


@router.post("/", response_model=EspecialidadePublic, status_code=201)
def criar_especialidade(dados: EspecialidadeCreate, session: Session = Depends(get_session)):
    especialidade = Especialidade.model_validate(dados)
    session.add(especialidade)

    try:
        session.commit()
        session.refresh(especialidade)
        return especialidade
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma especialidade com esse nome")


