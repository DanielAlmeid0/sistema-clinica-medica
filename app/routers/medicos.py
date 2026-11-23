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

@router.post("/", response_model=MedicoPublic, status_code=201)
def criar_medico(dados: MedicoCreate, session: Session = Depends(get_session)):
    medico = Medico.model_validate(dados)
    session.add(medico)

    try:
        session.commit()
        session.refresh(medico)
        return medico
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Já existe um médico com esse CRM ou email")



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

@router.get("/{medico_id}", response_model=MedicoPublicDetalhado)
def buscar_medico(medico_id: int, session: Session = Depends(get_session)):
    return buscar_medico_ou_404(medico_id, session)


@router.patch("/{medico_id}", response_model=MedicoPublic)
def atualizar_medico(medico_id: int, dados: MedicoUpdate, session: Session = Depends(get_session)):
    medico = buscar_medico_ou_404(medico_id, session)

    medico.sqlmodel_update(dados.model_dump(exclude_unset=True))
    session.add(medico)

    try:
        session.commit()
        session.refresh(medico)
        return medico
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Já existe um médico com esse CRM ou email")


@router.delete("/{medico_id}", status_code=204)
def excluir_medico(medico_id: int, session: Session = Depends(get_session)):
    medico = buscar_medico_ou_404(medico_id, session)

    tem_consulta = session.exec(select(Consulta).where(Consulta.medico_id == medico_id)).first()
    if tem_consulta:
        raise HTTPException(
            status_code=409,
            detail="O médico possui consultas e não pode ser excluído. Desative o cadastro (ativo = false).",
        )

    session.delete(medico)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="O médico possui agenda ou bloqueios cadastrados e não pode ser excluído")


@router.post("/{medico_id}/especialidades", response_model=MedicoPublicDetalhado, status_code=201)
def vincular_especialidade(medico_id: int, dados: VinculoEspecialidade, session: Session = Depends(get_session)):
    medico = buscar_medico_ou_404(medico_id, session)

    if not session.get(Especialidade, dados.especialidade_id):
        raise HTTPException(status_code=404, detail="Especialidade não encontrada")

    if session.get(MedicoEspecialidade, (medico_id, dados.especialidade_id)):
        raise HTTPException(status_code=409, detail="O médico já está vinculado a essa especialidade")

    vinculo = MedicoEspecialidade(medico_id=medico_id, especialidade_id=dados.especialidade_id, rqe=dados.rqe)
    session.add(vinculo)
    session.commit()
    session.refresh(medico)

    return medico


@router.delete("/{medico_id}/especialidades/{especialidade_id}", status_code=204)
def desvincular_especialidade(medico_id: int, especialidade_id: int, session: Session = Depends(get_session)):
    vinculo = session.get(MedicoEspecialidade, (medico_id, especialidade_id))

    if not vinculo:
        raise HTTPException(status_code=404, detail="O médico não está vinculado a essa especialidade")

    tem_agenda = session.exec(
        select(AgendaRegular).where(
            AgendaRegular.medico_id == medico_id,
            AgendaRegular.especialidade_id == especialidade_id,
        )
    ).first()
    if tem_agenda:
        raise HTTPException(
            status_code=409,
            detail="O médico tem agenda cadastrada nessa especialidade. Remova a agenda antes de desvincular.",
        )

    session.delete(vinculo)
    session.commit()