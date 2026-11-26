import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.routers import (
    relatorios,
    estatisticas,
    agendas,
    atendimentos,
    bloqueios,
    consultas,
    consultas_relacionadas,
    especialidades,
    medicos,
    pacientes,
)

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Sistema de Clínica Médica")

app.include_router(especialidades.router)
app.include_router(medicos.router)
app.include_router(pacientes.router)
app.include_router(agendas.router)
app.include_router(consultas.router)
app.include_router(bloqueios.router)
app.include_router(consultas_relacionadas.router)
app.include_router(estatisticas.router)
app.include_router(relatorios.router)
app.include_router(atendimentos.router)


@app.exception_handler(IntegrityError)
def tratar_conflito_de_dados(request: Request, erro: IntegrityError):
    logger.warning(
        "Conflito de dados em %s %s: %s", request.method, request.url.path, erro
    )
    return JSONResponse(
        status_code=409,
        content={"detail": "A operação conflita com dados já existentes."},
    )


@app.exception_handler(OperationalError)
def tratar_banco_indisponivel(request: Request, erro: OperationalError):
    logger.error(
        "Banco de dados indisponível em %s %s: %s",
        request.method,
        request.url.path,
        erro,
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Banco de dados indisponível no momento. Tente novamente em instantes."
        },
    )


@app.exception_handler(SQLAlchemyError)
def tratar_erro_de_banco(request: Request, erro: SQLAlchemyError):
    logger.error("Erro de banco em %s %s: %s", request.method, request.url.path, erro)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro ao acessar o banco de dados."},
    )


@app.exception_handler(Exception)
def tratar_erro_inesperado(request: Request, erro: Exception):
    logger.exception("Erro inesperado em %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor."},
    )


@app.get("/")
def raiz():
    return {"status": "ok", "mensagem": "API da Clínica Médica no ar"}
