from fastapi import FastAPI
from app.routers import especialidades

app = FastAPI(title="Sistema de Clínica Médica")

app.include_router(especialidades.router)


@app.get("/")
def raiz():
    return {"status": "ok", "mensagem": "API da Clínica Médica no ar"}
