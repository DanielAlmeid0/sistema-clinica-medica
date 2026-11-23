from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import Paciente
from app.schemas.paciente import PacienteCreate, PaginaPacientes, PacientePublic
from app.schemas.paginacao import Paginacao

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


def buscar_paciente_ou_404(paciente_id: int, session: Session) -> Paciente:
    paciente = session.get(Paciente, paciente_id)

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    return paciente


@router.post("/", response_model=PacientePublic, status_code=201)
def criar_paciente(dados: PacienteCreate, session: Session = Depends(get_session)):
    paciente = Paciente.model_validate(dados)
    session.add(paciente)

    try:
        session.commit()
        session.refresh(paciente)
        return paciente
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Já existe um paciente com esse CPF ou email")


@router.get("/", response_model=PaginaPacientes)
def listar_pacientes(
    pagina: int = Query(1, ge=1),
    tamanho_pagina: int = Query(10, ge=1, le=100),
    nome: str | None = None,
    cpf: str | None = None,
    ativo: bool | None = None,
    session: Session = Depends(get_session),
):
    consulta = select(Paciente)
    consulta_total = select(func.count()).select_from(Paciente)

    if nome:
        consulta = consulta.where(Paciente.nome.ilike(f"%{nome}%"))
        consulta_total = consulta_total.where(Paciente.nome.ilike(f"%{nome}%"))

    if cpf:
        consulta = consulta.where(Paciente.cpf == cpf)
        consulta_total = consulta_total.where(Paciente.cpf == cpf)

    if ativo is not None:
        consulta = consulta.where(Paciente.ativo == ativo)
        consulta_total = consulta_total.where(Paciente.ativo == ativo)

    total = session.exec(consulta_total).one()
    total_paginas = (total + tamanho_pagina - 1) // tamanho_pagina

    consulta = consulta.order_by(Paciente.nome).offset((pagina - 1) * tamanho_pagina).limit(tamanho_pagina)
    pacientes = session.exec(consulta).all()

    return PaginaPacientes(
        dados=pacientes,
        paginacao=Paginacao(
            total=total,
            pagina=pagina,
            tamanho_pagina=tamanho_pagina,
            total_paginas=total_paginas,
        ),
    )


@router.get("/{paciente_id}", response_model=PacientePublic)
def buscar_paciente(paciente_id: int, session: Session = Depends(get_session)):
    return buscar_paciente_ou_404(paciente_id, session)
