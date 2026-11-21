from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.database import getSession
from app.models import Especialidade
from app.schemas.especialidade import (
    EspecialidadeCreate,
    EspecialidadePublic,
    EspecialidadeUpdate,
    PaginaEspecialidades,
)
from app.schemas.paginacao import Paginacao