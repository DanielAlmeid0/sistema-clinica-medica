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


def validar_data_futura(inicio: datetime) -> None:
    if inicio <= datetime.now():
        raise HTTPException(status_code=400, detail="A consulta deve ser agendada para uma data futura")



def calcular_fim_pela_agenda(
    session: Session, medico_id: int, especialidade_id: int, inicio: datetime
) -> datetime:
    agendas = session.exec(
        select(AgendaRegular).where(
            AgendaRegular.medico_id == medico_id,
            AgendaRegular.especialidade_id == especialidade_id,
            AgendaRegular.dia_semana == inicio.weekday(),
            AgendaRegular.hora_inicio <= inicio.time(),
        )
    ).all()

    desalinhada = None

    for agenda in agendas:
        duracao = timedelta(minutes=agenda.duracao_consulta)
        fim = inicio + duracao
        if fim.date() != inicio.date() or fim.time() > agenda.hora_fim:
            continue

        desde_o_inicio = inicio - datetime.combine(inicio.date(), agenda.hora_inicio)
        if desde_o_inicio % duracao == timedelta(0):
            return fim
        desalinhada = agenda

    if desalinhada:
        raise HTTPException(
            status_code=409,
            detail=(
                f"O horário deve seguir a grade do médico: consultas de "
                f"{desalinhada.duracao_consulta} em {desalinhada.duracao_consulta} minutos, "
                f"a partir das {desalinhada.hora_inicio:%H:%M}"
            ),
        )

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


def verificar_conflito_medico(session: Session, medico_id: int, inicio: datetime, fim: datetime, ignorar_id: int | None = None) -> None:
    conflito = session.exec(
        select(Consulta).where(
            Consulta.medico_id == medico_id,
            Consulta.id != ignorar_id,
            Consulta.status != STATUS_CANCELADA,
            Consulta.data_hora_inicio < fim,
            Consulta.data_hora_fim > inicio,
        )
    ).first()
    if conflito:
        raise HTTPException(status_code=409, detail="O médico já possui consulta nesse horário")


def verificar_conflito_paciente(session: Session, paciente_id: int, inicio: datetime, fim: datetime, ignorar_id: int | None = None) -> None:
    conflito = session.exec(
        select(Consulta).where(
            Consulta.paciente_id == paciente_id,
            Consulta.id != ignorar_id, 
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
    fim = calcular_fim_pela_agenda(session, dados.medico_id, dados.especialidade_id, inicio)

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


def buscar_consulta_agendada(session: Session, consulta_id: int, acao: str) -> Consulta:
    """Busca a consulta e garante que ela ainda está 'agendada'.
    Usada por cancelar, remarcar, realizar e registrar falta."""
    consulta = session.get(Consulta, consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    if consulta.status != STATUS_AGENDADA:
        raise HTTPException(
            status_code=409,
            detail=f"Só é possível {acao} consultas agendadas (status atual: {consulta.status})",
        )
    return consulta


def _salvar(session: Session, consulta: Consulta) -> Consulta:
    session.add(consulta)
    try:
        session.commit()
        session.refresh(consulta)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível atualizar a consulta")
    return consulta


def cancelar_consulta(session: Session, consulta_id: int) -> Consulta:
    consulta = buscar_consulta_agendada(session, consulta_id, "cancelar")
    consulta.status = STATUS_CANCELADA
    return _salvar(session, consulta)


def realizar_consulta(session: Session, consulta_id: int) -> Consulta:
    consulta = buscar_consulta_agendada(session, consulta_id, "marcar como realizada")
    consulta.status = STATUS_REALIZADA
    return _salvar(session, consulta)


def registrar_nao_comparecimento(session: Session, consulta_id: int) -> Consulta:
    consulta = buscar_consulta_agendada(session, consulta_id, "registrar falta em")
    consulta.status = STATUS_NAO_COMPARECEU
    return _salvar(session, consulta)


def remarcar_consulta(session: Session, consulta_id: int, novo_inicio: datetime) -> Consulta:
    consulta = buscar_consulta_agendada(session, consulta_id, "remarcar")

    validar_data_futura(novo_inicio)
    novo_fim = calcular_fim_pela_agenda(
        session, consulta.medico_id, consulta.especialidade_id, novo_inicio
    )
    verificar_bloqueio(session, consulta.medico_id, novo_inicio, novo_fim)
    verificar_conflito_medico(session, consulta.medico_id, novo_inicio, novo_fim, consulta.id)
    verificar_conflito_paciente(session, consulta.paciente_id, novo_inicio, novo_fim, consulta.id)

    consulta.data_hora_inicio = novo_inicio
    consulta.data_hora_fim = novo_fim
    return _salvar(session, consulta)