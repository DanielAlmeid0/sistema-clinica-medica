from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import AgendaRegular, Especialidade, Medico, MedicoEspecialidade
from app.schemas.agenda import AgendaCreate, AgendaPublic

router = APIRouter(tags=["Agendas"])

@router.post("/medicos/{medico_id}/agendas", response_model=AgendaPublic, status_code=201)
def criar_agenda(medico_id: int, dados: AgendaCreate, session: Session = Depends(get_session)):
    medico = session.get(Medico, medico_id)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    if not medico.ativo:
        raise HTTPException(status_code=400, detail="Médico inativo não pode receber agenda")

    if not session.get(Especialidade, dados.especialidade_id):
        raise HTTPException(status_code=404, detail="Especialidade não encontrada")

    if not session.get(MedicoEspecialidade, (medico_id, dados.especialidade_id)):
        raise HTTPException(status_code=400, detail="O médico não atende essa especialidade")

    if dados.hora_inicio >= dados.hora_fim:
        raise HTTPException(status_code=422, detail="A hora de início deve ser antes da hora de fim")

    
    conflito = session.exec(
        select(AgendaRegular).where(
            AgendaRegular.medico_id == medico_id,
            AgendaRegular.dia_semana == dados.dia_semana,
            AgendaRegular.hora_inicio < dados.hora_fim,
            AgendaRegular.hora_fim > dados.hora_inicio,
        )
    ).first()
    if conflito:
        raise HTTPException(
            status_code=409,
            detail=f"O médico já atende nesse dia das {conflito.hora_inicio:%H:%M} às {conflito.hora_fim:%H:%M}",
        )

    agenda = AgendaRegular(medico_id=medico_id, **dados.model_dump())
    session.add(agenda)
    session.commit()
    session.refresh(agenda)

    return agenda

@router.get("/medicos/{medico_id}/agendas", response_model=list[AgendaPublic])
def listar_agendas(medico_id: int, session: Session = Depends(get_session)):
    if not session.get(Medico, medico_id):
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    consulta = (
        select(AgendaRegular)
        .where(AgendaRegular.medico_id == medico_id)
        .order_by(AgendaRegular.dia_semana, AgendaRegular.hora_inicio)
    )

    return session.exec(consulta).all()

@router.delete("/agendas/{agenda_id}", status_code=204)
def excluir_agenda(agenda_id: int, session: Session = Depends(get_session)):
    agenda = session.get(AgendaRegular, agenda_id)

    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda não encontrada")

    session.delete(agenda)
    session.commit()