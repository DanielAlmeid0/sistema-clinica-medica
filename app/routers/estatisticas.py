from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.estatisticas import Estatisticas
from app.services.estatisticas import calcular_estatisticas

router = APIRouter(prefix="/estatisticas", tags=["Estatísticas"])


@router.get("", response_model=Estatisticas)
def obter_estatisticas(session: Session = Depends(get_session)):
    return calcular_estatisticas(session)
