from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import AgendaRegular, Consulta, Especialidade, Medico, MedicoEspecialidade
from app.schemas.medico import (
    MedicoCreate,
    MedicoPublic,
    MedicoPublicDetalhado,
    MedicoUpdate,
    PaginaMedicos,
    VinculoEspecialidade,
)
from app.schemas.paginacao import Paginacao

router = APIRouter(prefix="/medicos", tags=["Médicos"])

def buscar_medico_ou_404(medico_id: int, session: Session) -> Medico:
    medico = session.get(Medico, medico_id)

    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrada")

    return medico

@router.get("/", response_model=PaginaMedicos)
def listar_medicos(
    pagina: int = Query(1, ge=1),
    tamanho_pagina: int = Query(10, ge=1, le=100),
    nome: str | None = None,
    ativo: bool | None = None,
    especialidade_id: int | None = None,
    session: Session = Depends(get_session),
):
    consulta = select(Medico)
    consulta_total = select(func.count()).select_from(Medico)

    if nome:
        consulta = consulta.where(Medico.nome.ilike(f"%{nome}%"))
        consulta_total = consulta_total.where(Medico.nome.ilike(f"%{nome}%"))

    if ativo is not None:
        consulta = consulta.where(Medico.ativo == ativo)
        consulta_total = consulta_total.where(Medico.ativo == ativo)

    if especialidade_id is not None:
        consulta = consulta.join(MedicoEspecialidade).where(MedicoEspecialidade.especialidade_id == especialidade_id)
        consulta_total = consulta_total.join(MedicoEspecialidade).where(MedicoEspecialidade.especialidade_id == especialidade_id)

    total = session.exec(consulta_total).one()
    total_paginas = (total + tamanho_pagina - 1) // tamanho_pagina

    consulta = consulta.order_by(Medico.nome).offset((pagina - 1) * tamanho_pagina).limit(tamanho_pagina)
    medicos = session.exec(consulta).all()

    return PaginaMedicos(
        dados=medicos,
        paginacao=Paginacao(
            total=total,
            pagina=pagina,
            tamanho_pagina=tamanho_pagina,
            total_paginas=total_paginas,
        ),
    )

