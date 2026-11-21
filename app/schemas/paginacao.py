from sqlmodel import SQLModel

class Paginacao(SQLModel):
    total: int
    pagina: int
    tamanho_pagina: int
    total_paginas: int