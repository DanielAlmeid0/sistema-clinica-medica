from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.database import get_session
from app.models import Consulta, Especialidade, Medico, Paciente
from app.schemas.consulta import PaginaConsultasDetalhadas
from app.services.consultas import condicoes_de_filtro, listar_consultas_detalhadas

router = APIRouter(tags=["Consultas relacionadas"])

StatusConsulta = Literal["agendada", "realizada", "cancelada", "nao_compareceu"]


@router.get("/pacientes/{paciente_id}/consultas", response_model=PaginaConsultasDetalhadas)
def listar_consultas_do_paciente(
    paciente_id: int,
    pagina: int = Query(1, ge=1),
    tamanho_pagina: int = Query(10, ge=1, le=100),
    status: StatusConsulta | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    session: Session = Depends(get_session),
):
    if not session.get(Paciente, paciente_id):
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    condicoes = [Consulta.paciente_id == paciente_id] + condicoes_de_filtro(status, data_inicio, data_fim)
    return listar_consultas_detalhadas(session, condicoes, pagina, tamanho_pagina)


@router.get("/medicos/{medico_id}/consultas", response_model=PaginaConsultasDetalhadas)
def listar_consultas_do_medico(
    medico_id: int,
    pagina: int = Query(1, ge=1),
    tamanho_pagina: int = Query(10, ge=1, le=100),
    status: StatusConsulta | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    session: Session = Depends(get_session),
):
    if not session.get(Medico, medico_id):
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    condicoes = [Consulta.medico_id == medico_id] + condicoes_de_filtro(status, data_inicio, data_fim)
    return listar_consultas_detalhadas(session, condicoes, pagina, tamanho_pagina)
