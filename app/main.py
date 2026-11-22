from fastapi import FastAPI
from app.routers import especialidades, medicos

app = FastAPI(title="Sistema de Clínica Médica")

app.include_router(especialidades.router)
app.include_router(medicos.router)


@app.get("/")
def raiz():
    return {"status": "ok", "mensagem": "API da Clínica Médica no ar"}
