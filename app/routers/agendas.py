from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import AgendaRegular, BloqueioAgenda, Consulta, Especialidade, Medico, MedicoEspecialidade
from app.schemas.agenda import AgendaCreate, AgendaPublic, HorarioDisponivel
from app.services.agendamento import STATUS_CANCELADA

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

def _esta_ocupado(itens, inicio: datetime, fim: datetime) -> bool:
    for item in itens:
        if item.data_hora_inicio < fim and item.data_hora_fim > inicio:
            return True
    return False

@router.get("/medicos/{medico_id}/disponibilidade", response_model=list[HorarioDisponivel])
def listar_disponibilidade(
    medico_id: int,
    data: date,
    especialidade_id: int,
    session: Session = Depends(get_session),
):
    medico = session.get(Medico, medico_id)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    if not medico.ativo:
        raise HTTPException(status_code=400, detail="Médico inativo não recebe consultas")

    if not session.get(Especialidade, especialidade_id):
        raise HTTPException(status_code=404, detail="Especialidade não encontrada")

    agendas = session.exec(
        select(AgendaRegular).where(
            AgendaRegular.medico_id == medico_id,
            AgendaRegular.especialidade_id == especialidade_id,
            AgendaRegular.dia_semana == data.weekday(),
        )
    ).all()

    inicio_dia = datetime.combine(data, time.min)
    fim_dia = inicio_dia + timedelta(days=1)

    consultas = session.exec(
        select(Consulta).where(
            Consulta.medico_id == medico_id,
            Consulta.status != STATUS_CANCELADA,
            Consulta.data_hora_inicio < fim_dia,
            Consulta.data_hora_fim > inicio_dia,
        )
    ).all()

    bloqueios = session.exec(
        select(BloqueioAgenda).where(
            BloqueioAgenda.medico_id == medico_id,
            BloqueioAgenda.data_hora_inicio < fim_dia,
            BloqueioAgenda.data_hora_fim > inicio_dia,
        )
    ).all()

    agora = datetime.now()
    livres = []

    for agenda in agendas:
        duracao = timedelta(minutes=agenda.duracao_consulta)
        inicio = datetime.combine(data, agenda.hora_inicio)
        limite = datetime.combine(data, agenda.hora_fim)

        while inicio + duracao <= limite:
            fim = inicio + duracao
            if (
                inicio > agora
                and not _esta_ocupado(consultas, inicio, fim)
                and not _esta_ocupado(bloqueios, inicio, fim)
            ):
                livres.append(HorarioDisponivel(inicio=inicio, fim=fim))
            inicio = fim

    livres.sort(key=lambda horario: horario.inicio)
    return livres