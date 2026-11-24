from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import (
    AgendaRegular,
    BloqueioAgenda,
    Consulta,
    Especialidade,
    Medico,
    MedicoEspecialidade,
    Paciente,
)
from app.schemas.consulta import ConsultaCreate

STATUS_AGENDADA = "agendada"
STATUS_REALIZADA = "realizada"
STATUS_CANCELADA = "cancelada"
STATUS_NAO_COMPARECEU = "nao_compareceu"


# Regra 1: paciente, medico e especialidade precisam existir e estar ativos,
# e o medico precisa atender a especialidade escolhida.
def validar_participantes(session: Session, dados: ConsultaCreate) -> None:
    paciente = session.get(Paciente, dados.paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    if not paciente.ativo:
        raise HTTPException(status_code=400, detail="Paciente inativo não pode agendar consulta")

    medico = session.get(Medico, dados.medico_id)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")
    if not medico.ativo:
        raise HTTPException(status_code=400, detail="Médico inativo não pode receber consultas")

    if not session.get(Especialidade, dados.especialidade_id):
        raise HTTPException(status_code=404, detail="Especialidade não encontrada")

    if not session.get(MedicoEspecialidade, (dados.medico_id, dados.especialidade_id)):
        raise HTTPException(status_code=400, detail="O médico não atende essa especialidade")


# Regra 2: nao e possivel agendar no passado.
def validar_data_futura(inicio: datetime) -> None:
    if inicio <= datetime.now():
        raise HTTPException(status_code=400, detail="A consulta deve ser agendada para uma data futura")


# Regra 3: o horario precisa estar dentro da agenda regular do medico
# para aquela especialidade e dia da semana. Devolve o horario de fim.
def calcular_fim_pela_agenda(session: Session, dados: ConsultaCreate) -> datetime:
    inicio = dados.data_hora_inicio

    agendas = session.exec(
        select(AgendaRegular).where(
            AgendaRegular.medico_id == dados.medico_id,
            AgendaRegular.especialidade_id == dados.especialidade_id,
            AgendaRegular.dia_semana == inicio.weekday(),
            AgendaRegular.hora_inicio <= inicio.time(),
        )
    ).all()

    for agenda in agendas:
        fim = inicio + timedelta(minutes=agenda.duracao_consulta)
        if fim.date() == inicio.date() and fim.time() <= agenda.hora_fim:
            return fim

    raise HTTPException(
        status_code=409,
        detail="O médico não atende essa especialidade nesse dia e horário",
    )


def verificar_bloqueio(session: Session, medico_id: int, inicio: datetime, fim: datetime) -> None:
    bloqueio = session.exec(
        select(BloqueioAgenda).where(
            BloqueioAgenda.medico_id == medico_id,
            BloqueioAgenda.data_hora_inicio < fim,
            BloqueioAgenda.data_hora_fim > inicio,
        )
    ).first()
    if bloqueio:
        raise HTTPException(
            status_code=409,
            detail=f"O médico está indisponível nesse período: {bloqueio.motivo}",
        )


def verificar_conflito_medico(session: Session, medico_id: int, inicio: datetime, fim: datetime) -> None:
    conflito = session.exec(
        select(Consulta).where(
            Consulta.medico_id == medico_id,
            Consulta.status != STATUS_CANCELADA,
            Consulta.data_hora_inicio < fim,
            Consulta.data_hora_fim > inicio,
        )
    ).first()
    if conflito:
        raise HTTPException(status_code=409, detail="O médico já possui consulta nesse horário")


def verificar_conflito_paciente(session: Session, paciente_id: int, inicio: datetime, fim: datetime) -> None:
    conflito = session.exec(
        select(Consulta).where(
            Consulta.paciente_id == paciente_id,
            Consulta.status != STATUS_CANCELADA,
            Consulta.data_hora_inicio < fim,
            Consulta.data_hora_fim > inicio,
        )
    ).first()
    if conflito:
        raise HTTPException(status_code=409, detail="O paciente já possui consulta nesse horário")


def agendar_consulta(session: Session, dados: ConsultaCreate) -> Consulta:
    validar_participantes(session, dados)
    validar_data_futura(dados.data_hora_inicio)

    inicio = dados.data_hora_inicio
    fim = calcular_fim_pela_agenda(session, dados)

    verificar_bloqueio(session, dados.medico_id, inicio, fim)
    verificar_conflito_medico(session, dados.medico_id, inicio, fim)
    verificar_conflito_paciente(session, dados.paciente_id, inicio, fim)

    consulta = Consulta(
        paciente_id=dados.paciente_id,
        medico_id=dados.medico_id,
        especialidade_id=dados.especialidade_id,
        data_hora_inicio=inicio,
        data_hora_fim=fim,
        status=STATUS_AGENDADA,
    )
    session.add(consulta)

    try:
        session.commit()
        session.refresh(consulta)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível registrar a consulta")

    return consulta


def cancelar_consulta(session: Session, consulta_id: int) -> Consulta:
    consulta = session.get(Consulta, consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    if consulta.status != STATUS_AGENDADA:
        raise HTTPException(
            status_code=409,
            detail=f"Só é possível cancelar consultas agendadas (status atual: {consulta.status})",
        )

    consulta.status = STATUS_CANCELADA
    session.add(consulta)
    session.commit()
    session.refresh(consulta)

    return consulta
