from fastapi import FastAPI

app = FastAPI(title="Sistema de Clínica Médica")


@app.get("/")
def raiz():
    return {"status": "ok", "mensagem": "API da Clínica Médica no ar"}
