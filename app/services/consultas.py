from datetime import date, datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.models import Consulta, Especialidade, Medico, Paciente
from app.schemas.consulta import ConsultaDetalhada, PaginaConsultasDetalhadas
from app.schemas.paginacao import Paginacao


def condicoes_de_filtro(status: str | None, data_inicio: date | None, data_fim: date | None) -> list:
    if data_inicio and data_fim and data_inicio > data_fim:
        raise HTTPException(status_code=422, detail="A data inicial deve ser anterior ou igual à data final")

    condicoes = []
    if status:
        condicoes.append(Consulta.status == status)
    if data_inicio:
        condicoes.append(Consulta.data_hora_inicio >= datetime.combine(data_inicio, time.min))
    if data_fim:
        condicoes.append(Consulta.data_hora_inicio < datetime.combine(data_fim + timedelta(days=1), time.min))

    return condicoes


def listar_consultas_detalhadas(
    session: Session, condicoes: list, pagina: int, tamanho_pagina: int
) -> PaginaConsultasDetalhadas:
    total = session.exec(select(func.count()).select_from(Consulta).where(*condicoes)).one()
    total_paginas = (total + tamanho_pagina - 1) // tamanho_pagina

    consulta = (
        select(Consulta, Paciente, Medico, Especialidade)
        .join(Paciente, Consulta.paciente_id == Paciente.id)
        .join(Medico, Consulta.medico_id == Medico.id)
        .join(Especialidade, Consulta.especialidade_id == Especialidade.id)
        .where(*condicoes)
        .order_by(Consulta.data_hora_inicio)
        .offset((pagina - 1) * tamanho_pagina)
        .limit(tamanho_pagina)
    )
    linhas = session.exec(consulta).all()

    dados = [
        ConsultaDetalhada(
            id=c.id,
            data_hora_inicio=c.data_hora_inicio,
            data_hora_fim=c.data_hora_fim,
            status=c.status,
            paciente_id=p.id,
            paciente_nome=p.nome,
            medico_id=m.id,
            medico_nome=m.nome,
            especialidade_id=e.id,
            especialidade_nome=e.nome,
        )
        for c, p, m, e in linhas
    ]

    return PaginaConsultasDetalhadas(
        dados=dados,
        paginacao=Paginacao(
            total=total,
            pagina=pagina,
            tamanho_pagina=tamanho_pagina,
            total_paginas=total_paginas,
        ),
    )
