from sqlalchemy import func
from sqlmodel import Session, select

from app.models import AgendaRegular, Consulta, Especialidade, Medico, Paciente
from app.schemas.estatisticas import (
    ContagemPorEspecialidade,
    ContagemPorMedico,
    ContagemPorStatus,
    Estatisticas,
)
from app.services.agendamento import STATUS_NAO_COMPARECEU, STATUS_REALIZADA


def calcular_estatisticas(session: Session) -> Estatisticas:
    total_pacientes = session.exec(select(func.count()).select_from(Paciente)).one()
    total_medicos = session.exec(select(func.count()).select_from(Medico)).one()
    total_consultas = session.exec(select(func.count()).select_from(Consulta)).one()

    por_status = session.exec(
        select(Consulta.status, func.count()).group_by(Consulta.status).order_by(Consulta.status)
    ).all()

    por_especialidade = session.exec(
        select(Especialidade.id, Especialidade.nome, func.count(Consulta.id))
        .select_from(Especialidade)
        .outerjoin(Consulta, Consulta.especialidade_id == Especialidade.id)
        .group_by(Especialidade.id, Especialidade.nome)
        .order_by(func.count(Consulta.id).desc(), Especialidade.nome)
    ).all()

    por_medico = session.exec(
        select(Medico.id, Medico.nome, func.count(Consulta.id))
        .select_from(Medico)
        .outerjoin(Consulta, Consulta.medico_id == Medico.id)
        .group_by(Medico.id, Medico.nome)
        .order_by(func.count(Consulta.id).desc(), Medico.nome)
        .limit(10)
    ).all()

    contagem = {status: total for status, total in por_status}
    atendimentos = contagem.get(STATUS_REALIZADA, 0) + contagem.get(STATUS_NAO_COMPARECEU, 0)
    faltas = contagem.get(STATUS_NAO_COMPARECEU, 0)
    taxa = round(faltas / atendimentos * 100, 2) if atendimentos else None

    media = session.exec(select(func.avg(AgendaRegular.duracao_consulta))).one()
    primeira, ultima = session.exec(
        select(func.min(Consulta.data_hora_inicio), func.max(Consulta.data_hora_inicio))
    ).one()

    return Estatisticas(
        total_pacientes=total_pacientes,
        total_medicos=total_medicos,
        total_consultas=total_consultas,
        consultas_por_status=[ContagemPorStatus(status=s, total=t) for s, t in por_status],
        consultas_por_especialidade=[
            ContagemPorEspecialidade(especialidade_id=i, especialidade=n, total=t) for i, n, t in por_especialidade
        ],
        consultas_por_medico=[ContagemPorMedico(medico_id=i, medico=n, total=t) for i, n, t in por_medico],
        taxa_nao_comparecimento=taxa,
        duracao_media_agenda_minutos=float(media) if media is not None else None,
        primeira_consulta=primeira,
        ultima_consulta=ultima,
    )
