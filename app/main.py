from fastapi import FastAPI
from app.routers import agendas, consultas, especialidades, medicos, pacientes

app = FastAPI(title="Sistema de Clínica Médica")

app.include_router(especialidades.router)
app.include_router(medicos.router)
app.include_router(pacientes.router)
app.include_router(agendas.router)
app.include_router(consultas.router)


@app.get("/")
def raiz():
    return {"status": "ok", "mensagem": "API da Clínica Médica no ar"}
