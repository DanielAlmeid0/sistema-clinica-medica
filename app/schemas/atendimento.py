from sqlmodel import Field, SQLModel


class ReceitaCreate(SQLModel):
    medicamento: str = Field(min_length=2, max_length=150)
    dosagem: str = Field(min_length=1, max_length=100)
    frequencia: str = Field(min_length=2, max_length=100)
    duracao: str = Field(min_length=2, max_length=100)
    observacoes: str | None = Field(default=None, max_length=500)


class ReceitaPublic(ReceitaCreate):
    id: int
    atendimento_id: int
    criado_em: datetime


class AtendimentoCreate(SQLModel):
    observacoes_clinicas: str | None = Field(default=None, max_length=500)
    prescricao_medicamentos: str | None = Field(default=None)
    orientacoes: str | None = Field(default=None)
    data_retorno: int | None = Field(default=None, gt=0)


class AtendimentoPublic(AtendimentoCreate):
    id: int
    consulta_id: int
    receitas: list[ReceitaPublic] = []


class AtendimentohistoricoItem(SQLModel):
    atendimento_id: int
    consulta_id: int
    data_hora_inicio: NaiveDatetime
    data_hora_fim: NaiveDatetime
    medico_id: int
    medico_nome: str
    especialidade_id: int
    especialidade_nome: str
    observacoes_clinicas: str
    prescricao_medicamentos: str | None = None
    orientacoes: str | None = None
    data_retorno: int | None = None
    receitas: list[ReceitaPublic] = []


class ProntuarioPacientePublic(SQLModel):
    paciente_id: int
    paciente_nome: str
    paciente_cpf: str
    total_atendimentos: int
    atendimentos: list[AtendimentohistoricoItem] = []
