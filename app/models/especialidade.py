from sqlmodel import Field, SQLModel

class EspecialidadeBase(SQLModel):
    nome: str = Field(min_length= 3, max_length=100, unique=True, index=True)
    descricao: str | None = Field(default=None, max_length=300)

class Especialidade(EspecialidadeBase, table=True):
    id: int | None = Field(default=None, primary_key=True)