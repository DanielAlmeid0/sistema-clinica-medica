from datetime import date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import Consulta
from app.schemas.paginacao import Paginacao
from app.schemas.consulta import ConsultaCreate, ConsultaPublic, ConsultaRemarcar, PaginaConsultas
from app.services.agendamento import (
    agendar_consulta,
    cancelar_consulta,
    realizar_consulta,
    registrar_nao_comparecimento,
    remarcar_consulta,
)

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


@router.patch("/{consulta_id}/cancelar", response_model=ConsultaPublic)
def cancelar(consulta_id: int, session: Session = Depends(get_session)):
    return cancelar_consulta(session, consulta_id)

@router.patch("/{consulta_id}/remarcar", response_model=ConsultaPublic)
def remarcar(consulta_id: int, dados: ConsultaRemarcar, session: Session = Depends(get_session)):
    return remarcar_consulta(session, consulta_id, dados.data_hora_inicio)


@router.patch("/{consulta_id}/realizar", response_model=ConsultaPublic)
def realizar(consulta_id: int, session: Session = Depends(get_session)):
    return realizar_consulta(session, consulta_id)


@router.patch("/{consulta_id}/nao-compareceu", response_model=ConsultaPublic)
def nao_compareceu(consulta_id: int, session: Session = Depends(get_session)):
    return registrar_nao_comparecimento(session, consulta_id)


@router.get("/", response_model=PaginaConsultas)
def listar_consultas(
    pagina: int = Query(1, ge=1),
    tamanho_pagina: int = Query(10, ge=1, le=100),
    medico_id: int | None = None,
    paciente_id: int | None = None,
    especialidade_id: int | None = None,
    status: Literal["agendada", "realizada", "cancelada", "nao_compareceu"] | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    session: Session = Depends(get_session),
):
    if data_inicio and data_fim and data_inicio > data_fim:
        raise HTTPException(status_code=422, detail="A data inicial deve ser anterior ou igual à data final")

    condicoes = []
    if medico_id is not None:
        condicoes.append(Consulta.medico_id == medico_id)
    if paciente_id is not None:
        condicoes.append(Consulta.paciente_id == paciente_id)
    if especialidade_id is not None:
        condicoes.append(Consulta.especialidade_id == especialidade_id)
    if status:
        condicoes.append(Consulta.status == status)
    if data_inicio:
        condicoes.append(Consulta.data_hora_inicio >= datetime.combine(data_inicio, time.min))
    if data_fim:
        condicoes.append(Consulta.data_hora_inicio < datetime.combine(data_fim + timedelta(days=1), time.min))

    total = session.exec(select(func.count()).select_from(Consulta).where(*condicoes)).one()
    total_paginas = (total + tamanho_pagina - 1) // tamanho_pagina

    consulta = (
        select(Consulta)
        .where(*condicoes)
        .order_by(Consulta.data_hora_inicio)
        .offset((pagina - 1) * tamanho_pagina)
        .limit(tamanho_pagina)
    )
    consultas = session.exec(consulta).all()

    return PaginaConsultas(
        dados=consultas,
        paginacao=Paginacao(
            total=total,
            pagina=pagina,
            tamanho_pagina=tamanho_pagina,
            total_paginas=total_paginas,
        ),
    )
