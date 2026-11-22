from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import Especialidade
from app.schemas.especialidade import (
    EspecialidadeCreate,
    EspecialidadePublic,
    EspecialidadeUpdate,
    PaginaEspecialidades,
)
from app.schemas.paginacao import Paginacao

router = APIRouter(prefix="/especialidades", tags=["Especialidades"])


@router.post("/", response_model=EspecialidadePublic, status_code=201)
def criar_especialidade(dados: EspecialidadeCreate, session: Session = Depends(get_session)):
    especialidade = Especialidade.model_validate(dados)
    session.add(especialidade)

    try:
        session.commit()
        session.refresh(especialidade)
        return especialidade
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma especialidade com esse nome")


@router.get("/", response_model=PaginaEspecialidades)
def listar_especialidades(
    pagina: int = Query(1, ge=1),
    tamanho_pagina: int = Query(10, ge=1, le=100),
    nome: str | None = None,
    session: Session = Depends(get_session),
):
    consulta = select(Especialidade)
    consulta_total = select(func.count()).select_from(Especialidade)

    if nome:
        consulta = consulta.where(Especialidade.nome.ilike(f"%{nome}%"))
        consulta_total = consulta_total.where(Especialidade.nome.ilike(f"%{nome}%"))

    total = session.exec(consulta_total).one()
    total_paginas = (total + tamanho_pagina - 1) // tamanho_pagina
    consulta = consulta.order_by(Especialidade.nome).offset((pagina - 1) * tamanho_pagina).limit(tamanho_pagina)
    especialidades = session.exec(consulta).all()

    return PaginaEspecialidades(
        dados=especialidades,
        paginacao=Paginacao(
            total=total,
            pagina=pagina,
            tamanho_pagina=tamanho_pagina,
            total_paginas=total_paginas,
        ),
    )

router.get("/{especialidade_id}", response_model=EspecialidadePublic)
def buscar_especialidade(especialidade_id: int, session: Session = Depends(get_session)):
    especialidade = session.get(Especialidade, especialidade_id)

    if not especialidade:
        raise HTTPException(status_code=404, detail="Especialidade não encontrada")

    return especialidade


@router.patch("/{especialidade_id}", response_model=EspecialidadePublic)
def atualizar_especialidade(
    especialidade_id: int,
    dados: EspecialidadeUpdate,
    session: Session = Depends(get_session),
):
    especialidade = session.get(Especialidade, especialidade_id)

    if not especialidade:
        raise HTTPException(status_code=404, detail="Especialidade não encontrada")

    especialidade.sqlmodel_update(dados.model_dump(exclude_unset=True))
    session.add(especialidade)

    try:
        session.commit()
        session.refresh(especialidade)
        return especialidade
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Já existe uma especialidade com esse nome")


@router.delete("/{especialidade_id}", status_code=204)
def excluir_especialidade(especialidade_id: int, session: Session = Depends(get_session)):
    especialidade = session.get(Especialidade, especialidade_id)

    if not especialidade:
        raise HTTPException(status_code=404, detail="Especialidade não encontrada")

    session.delete(especialidade)
    session.commit()