from datetime import date, datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy import exists, func
from sqlmodel import Session, select

from app.models import Consulta, Medico, Paciente
from app.schemas.relatorios import MedicoSemConsultas, PacienteFrequente
from app.services.agendamento import STATUS_CANCELADA


def _inicio_do_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.min)


def _validar_periodo(data_inicio: date | None, data_fim: date | None) -> None:
    if data_inicio and data_fim and data_inicio > data_fim:
        raise HTTPException(status_code=422, detail="A data inicial deve ser anterior ou igual à data final")


def medicos_sem_consultas(session: Session, data_inicio: date, data_fim: date) -> list[MedicoSemConsultas]:
    _validar_periodo(data_inicio, data_fim)

    possui_consulta = exists().where(
        Consulta.medico_id == Medico.id,
        Consulta.status != STATUS_CANCELADA,
        Consulta.data_hora_inicio >= _inicio_do_dia(data_inicio),
        Consulta.data_hora_inicio < _inicio_do_dia(data_fim + timedelta(days=1)),
    )
    medicos = session.exec(
        select(Medico).where(Medico.ativo.is_(True), ~possui_consulta).order_by(Medico.nome)
    ).all()

    return [MedicoSemConsultas(id=m.id, nome=m.nome, crm=m.crm) for m in medicos]


def pacientes_frequentes(
    session: Session, minimo: int, data_inicio: date | None, data_fim: date | None
) -> list[PacienteFrequente]:
    _validar_periodo(data_inicio, data_fim)

    condicoes = [Consulta.status != STATUS_CANCELADA]
    if data_inicio:
        condicoes.append(Consulta.data_hora_inicio >= _inicio_do_dia(data_inicio))
    if data_fim:
        condicoes.append(Consulta.data_hora_inicio < _inicio_do_dia(data_fim + timedelta(days=1)))

    total = func.count(Consulta.id)
    linhas = session.exec(
        select(Paciente.id, Paciente.nome, total, func.min(Consulta.data_hora_inicio), func.max(Consulta.data_hora_inicio))
        .select_from(Paciente)
        .join(Consulta, Consulta.paciente_id == Paciente.id)
        .where(*condicoes)
        .group_by(Paciente.id, Paciente.nome)
        .having(total >= minimo)
        .order_by(total.desc(), Paciente.nome)
    ).all()

    return [
        PacienteFrequente(
            paciente_id=i, paciente=n, total_consultas=t, primeira_consulta=primeira, ultima_consulta=ultima
        )
        for i, n, t, primeira, ultima in linhas
    ]
