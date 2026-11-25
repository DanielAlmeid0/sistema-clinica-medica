from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.atendimento import (
    AtendimentoCreate,
    AtendimentoPublic,
    ProntuarioPacientePublic,
    ReceitaCreate,
    ReceitaPublic,
)
from app.services.atendimentos import (
    adicionar_receita,
    obter_prontuario_paciente,
    registrar_atendimento,
)

router = APIRouter(tags=["Atendimentos e receitas"])


@router.post(
    "/consultas/{consulta_id}/atendimentos",
    response_model=AtendimentoPublic,
    status_code=201,
)
def criar_atendimento(
    consulta_id: int, dados: AtendimentoCreate, session: Session = Depends(get_session)
):
    return registrar_atendimento(session=session, consulta_id=consulta_id, dados=dados)


@router.post(
    "/atendimentos/{atendimento_id}/receitas",
    response_model=ReceitaPublic,
    status_code=201,
)
def criar_receita(
    atendimento_id: int, dados: ReceitaCreate, session: Session = Depends(get_session)
):
    return adicionar_receita(
        session=session, atendimento_id=atendimento_id, dados=dados
    )


@router.get(
    "/pacientes/{paciente_id}/prontuario",
    response_model=ProntuarioPacientePublic,
)
def listar_prontuario_paciente(
    paciente_id: int, session: Session = Depends(get_session)
):
    return obter_prontuario_paciente(session=session, paciente_id=paciente_id)
