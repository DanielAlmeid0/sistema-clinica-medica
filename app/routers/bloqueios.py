from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.models import BloqueioAgenda, Consulta, Medico
from app.schemas.bloqueio import BloqueioCreate, BloqueioPublic
from app.services.agendamento import STATUS_AGENDADA

router = APIRouter(tags=["Bloqueios"])


@router.post("/medicos/{medico_id}/bloqueios", response_model=BloqueioPublic, status_code=201)
def criar_bloqueio(medico_id: int, dados: BloqueioCreate, session: Session = Depends(get_session)):
    medico = session.get(Medico, medico_id)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    if not medico.ativo:
        raise HTTPException(status_code=400, detail="Médico inativo não pode receber bloqueios")

    if dados.data_hora_inicio >= dados.data_hora_fim:
        raise HTTPException(status_code=422, detail="O início do bloqueio deve ser antes do fim")

    bloqueio_existente = session.exec(
        select(BloqueioAgenda).where(
            BloqueioAgenda.medico_id == medico_id,
            BloqueioAgenda.data_hora_inicio < dados.data_hora_fim,
            BloqueioAgenda.data_hora_fim > dados.data_hora_inicio,
        )
    ).first()
    if bloqueio_existente:
        raise HTTPException(status_code=409, detail="Já existe um bloqueio nesse período para o médico")

    consulta_agendada = session.exec(
        select(Consulta).where(
            Consulta.medico_id == medico_id,
            Consulta.status == STATUS_AGENDADA,
            Consulta.data_hora_inicio < dados.data_hora_fim,
            Consulta.data_hora_fim > dados.data_hora_inicio,
        )
    ).first()
    if consulta_agendada:
        raise HTTPException(
            status_code=409,
            detail="O médico possui consultas agendadas nesse período. Cancele-as antes de criar o bloqueio",
        )

    bloqueio = BloqueioAgenda(medico_id=medico_id, **dados.model_dump())
    session.add(bloqueio)
    session.commit()
    session.refresh(bloqueio)

    return bloqueio


@router.get("/medicos/{medico_id}/bloqueios", response_model=list[BloqueioPublic])
def listar_bloqueios(medico_id: int, session: Session = Depends(get_session)):
    if not session.get(Medico, medico_id):
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    consulta = (
        select(BloqueioAgenda)
        .where(BloqueioAgenda.medico_id == medico_id)
        .order_by(BloqueioAgenda.data_hora_inicio)
    )

    return session.exec(consulta).all()


@router.delete("/bloqueios/{bloqueio_id}", status_code=204)
def excluir_bloqueio(bloqueio_id: int, session: Session = Depends(get_session)):
    bloqueio = session.get(BloqueioAgenda, bloqueio_id)

    if not bloqueio:
        raise HTTPException(status_code=404, detail="Bloqueio não encontrado")

    session.delete(bloqueio)
    session.commit()
