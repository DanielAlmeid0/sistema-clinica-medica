# Sistema de Clínica Médica

API REST para gerenciamento de uma clínica médica: cadastro de pacientes, médicos e especialidades, agenda dos médicos, agendamento de consultas **sem conflito de horário**, registro de atendimentos (prontuário e receitas), relatórios e estatísticas.

Trabalho Prático 2 da disciplina **QXD0099 – Desenvolvimento de Software para Persistência** (UFC – Campus Quixadá), Prof. Francisco Victor da Silva Pinheiro.

## Integrantes

- Daniel Almeida
- José Yago
- Lorhann de Oliveira

## Tema recebido

**Tema 1 — Sistema de Clínica Médica.**
Funcionalidade específica: **verificar a disponibilidade de um médico e agendar consultas sem conflito de horário.**

## Objetivo

Substituir o controle por planilhas de uma clínica por uma aplicação com banco relacional, capaz de:

- consultar a disponibilidade dos médicos e agendar consultas sem conflitos, respeitando a agenda regular, as especialidades e os períodos de indisponibilidade;
- cancelar, remarcar e registrar o resultado das consultas **sem apagar o histórico**;
- guardar o atendimento (observações clínicas, orientações, prescrições e receitas) associado a cada consulta realizada;
- recuperar o histórico de um paciente e os atendimentos de um profissional em um período.

## Tecnologias

| Tecnologia | Uso |
| --- | --- |
| Python 3.11+ | Linguagem |
| FastAPI + Uvicorn | API REST e documentação automática (Swagger) |
| SQLModel (SQLAlchemy + Pydantic) | Mapeamento objeto-relacional e validação |
| PostgreSQL | Banco principal |
| SQLite | Banco alternativo (troca apenas a variável `DATABASE_URL`) |
| Alembic | Migrações do esquema |
| python-dotenv | Leitura do arquivo `.env` |

## Estrutura do projeto

```
app/
├── main.py            # cria a aplicação, registra os routers e os tratadores de erro
├── core/database.py   # engine, sessão e leitura do DATABASE_URL
├── models/            # tabelas (SQLModel)
├── schemas/           # entrada/saída da API (validação)
├── routers/           # rotas organizadas por recurso (APIRouter)
└── services/          # regras de negócio, consultas e estatísticas
alembic/               # migrações
scripts/seed.py        # povoamento inicial do banco
alembic.ini
requirements.txt
.env.example
```

## Entidades

| Tabela | Descrição |
| --- | --- |
| `especialidade` | Especialidades médicas (nome único). |
| `medicos` | Médicos (CRM e e-mail únicos, flag `ativo`). |
| `medico_especialidades` | Tabela associativa Médico ↔ Especialidade, com o RQE do médico naquela especialidade. |
| `pacientes` | Pacientes (CPF e e-mail únicos, flag `ativo`). |
| `Agendas_regulares` | Agenda semanal do médico: especialidade, dia da semana, hora de início/fim e duração da consulta. |
| `bloqueios_agenda` | Períodos de indisponibilidade do médico (férias, congresso etc.). |
| `consultas` | Agendamentos (paciente, médico, especialidade, início, fim e status: `agendada`, `realizada`, `cancelada`, `nao_compareceu`). |
| `prontuarios` | Atendimento registrado após a consulta: observações clínicas, prescrição, orientações e retorno. |
| `receitas` | Receitas (medicamento, dosagem, frequência, duração) vinculadas a um atendimento. |

## Relacionamentos

| Tipo | Relacionamento |
| --- | --- |
| **1:1** | `consultas` ↔ `prontuarios` (uma consulta tem no máximo um atendimento; `consulta_id` é único). |
| **1:N** | `medicos` → `consultas`, `pacientes` → `consultas`, `especialidade` → `consultas` |
| **1:N** | `medicos` → `Agendas_regulares`, `medicos` → `bloqueios_agenda` |
| **1:N** | `prontuarios` → `receitas` |
| **N:N** | `medicos` ↔ `especialidade`, via `medico_especialidades` (um médico pode atender mais de uma especialidade, com agendas distintas para cada uma). |

### Diagrama do modelo relacional

```mermaid
erDiagram
    ESPECIALIDADE ||--o{ MEDICO_ESPECIALIDADES : "tem"
    MEDICOS ||--o{ MEDICO_ESPECIALIDADES : "atende"
    MEDICOS ||--o{ AGENDAS_REGULARES : "possui"
    ESPECIALIDADE ||--o{ AGENDAS_REGULARES : "define"
    MEDICOS ||--o{ BLOQUEIOS_AGENDA : "possui"
    MEDICOS ||--o{ CONSULTAS : "realiza"
    PACIENTES ||--o{ CONSULTAS : "agenda"
    ESPECIALIDADE ||--o{ CONSULTAS : "classifica"
    CONSULTAS ||--o| PRONTUARIOS : "gera"
    PRONTUARIOS ||--o{ RECEITAS : "contém"

    ESPECIALIDADE { int id PK string nome UK string descricao }
    MEDICOS { int id PK string nome string crm UK string telefone string email UK bool ativo }
    MEDICO_ESPECIALIDADES { int medico_id PK,FK int especialidade_id PK,FK string rqe }
    PACIENTES { int id PK string nome string cpf UK date data_nasc string email UK bool ativo }
    AGENDAS_REGULARES { int id PK int medico_id FK int especialidade_id FK int dia_semana time hora_inicio time hora_fim int duracao_consulta }
    BLOQUEIOS_AGENDA { int id PK int medico_id FK datetime data_hora_inicio datetime data_hora_fim string motivo }
    CONSULTAS { int id PK int paciente_id FK int medico_id FK int especialidade_id FK datetime data_hora_inicio datetime data_hora_fim string status }
    PRONTUARIOS { int id PK int consulta_id FK,UK string observacoes_clinicas string prescricao_medicamentos string orientacoes int data_retorno }
    RECEITAS { int id PK int atendimento_id FK string medicamento string dosagem string frequencia string duracao }
```

## Instalação e execução

### 1. Clonar e criar o ambiente virtual

```bash
git clone https://github.com/DanielAlmeid0/sistema-clinica-medica.git
cd sistema-clinica-medica

python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 2. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar o banco (variável `DATABASE_URL`)

Copie o arquivo de exemplo e edite conforme o banco escolhido:

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

**Opção A — PostgreSQL (banco principal)**

Crie o usuário e o banco (exemplo com `psql`):

```sql
CREATE USER clinica_user WITH PASSWORD 'sua_senha';
CREATE DATABASE clinica OWNER clinica_user;
```

No `.env`:

```
DATABASE_URL=postgresql+psycopg://clinica_user:sua_senha@localhost:5432/clinica
```

**Opção B — SQLite (sem instalar nada)**

No `.env`:

```
DATABASE_URL=sqlite:///./database.db
```

> Se `DATABASE_URL` não for definida, a aplicação usa SQLite (`./database.db`) por padrão.
> Trocar de banco **não exige alterar** models, routers ou services — só essa variável.

### 4. Executar as migrações

```bash
alembic upgrade head
```

Isso cria todas as tabelas. Histórico de migrações do projeto:

| Versão | O que faz |
| --- | --- |
| `28f9aa313405` | Cria as tabelas iniciais da clínica |
| `bd9329131674` | Altera o tipo das colunas de data/hora (remove o fuso horário) em consultas e bloqueios |
| `7af57b832cf2` | Cria a tabela `receitas` |

### 5. Povoar o banco (seed)

```bash
python -m scripts.seed
```

Cria 4 especialidades, 6 médicos (um inativo), 12 pacientes, agendas regulares, bloqueios, 22 consultas em vários status e prontuários. As datas são calculadas a partir da semana atual.

Se o banco já tiver dados, o script avisa e não faz nada. Para apagar tudo e popular de novo:

```bash
python -m scripts.seed --limpar
```

### 6. Rodar a aplicação

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Documentação interativa (Swagger): http://127.0.0.1:8000/docs

## Principais endpoints

Todas as listagens são paginadas com `pagina` (padrão 1) e `tamanho_pagina` (padrão 10, máx. 100), e a resposta traz as informações de paginação (total, página atual etc.). A limitação é feita no banco (`LIMIT/OFFSET`).

| Recurso | Endpoints |
| --- | --- |
| Especialidades | `POST/GET /especialidades/`, `GET/PATCH/DELETE /especialidades/{id}` |
| Médicos | `POST/GET /medicos/`, `GET/PATCH/DELETE /medicos/{id}` |
| Médico ↔ Especialidade (N:N) | `POST /medicos/{id}/especialidades`, `DELETE /medicos/{id}/especialidades/{especialidade_id}` |
| Agendas regulares | `POST/GET /medicos/{id}/agendas`, `DELETE /agendas/{id}` |
| Bloqueios | `POST/GET /medicos/{id}/bloqueios`, `DELETE /bloqueios/{id}` |
| Pacientes | `POST/GET /pacientes/`, `GET/PATCH/DELETE /pacientes/{id}` |
| Consultas | `POST/GET /consultas/`, `GET /consultas/{id}` |
| Ações da consulta | `PATCH /consultas/{id}/cancelar`, `/remarcar`, `/realizar`, `/nao-compareceu` |
| Atendimento (prontuário) | `POST /consultas/{id}/atendimentos`, `GET /pacientes/{id}/prontuario` |
| Receitas | `POST /atendimentos/{id}/receitas` |
| Disponibilidade | `GET /medicos/{id}/disponibilidade?data=AAAA-MM-DD&especialidade_id=1` |
| Estatísticas | `GET /estatisticas` |
| Relatórios | `GET /relatorios/medicos-sem-consultas`, `GET /relatorios/pacientes-frequentes` |

## Filtros disponíveis

Aplicados diretamente na consulta SQL e combináveis entre si.

| Endpoint | Filtros |
| --- | --- |
| `GET /consultas/` | `medico_id`, `paciente_id`, `especialidade_id`, `status`, `data_inicio`, `data_fim` |
| `GET /medicos/` | `nome`, `ativo`, `especialidade_id` |
| `GET /pacientes/` | `nome`, `cpf`, `ativo` |
| `GET /especialidades/` | `nome` |

## Consultas específicas

**Consultas que usam relacionamentos (F10):**

- `GET /medicos/{id}/consultas` — consultas de um médico (filtros: `status`, `data_inicio`, `data_fim`).
- `GET /pacientes/{id}/consultas` — histórico de consultas de um paciente.
- `GET /especialidades/{id}/consultas` — consultas de uma especialidade.
- `GET /pacientes/{id}/prontuario` — histórico de atendimentos do paciente, com as receitas de cada um.
- `GET /medicos?especialidade_id=` e `GET /medicos/{id}` — médicos com suas especialidades (N:N).

**Consultas complexas (F11):**

- `GET /relatorios/medicos-sem-consultas?data_inicio=&data_fim=` — médicos **ativos** sem nenhuma consulta (não cancelada) no período (`NOT EXISTS`).
- `GET /relatorios/pacientes-frequentes?minimo=&data_inicio=&data_fim=` — pacientes com no mínimo N consultas (não canceladas) no período, ordenados pelo total (`JOIN` + `GROUP BY` + `HAVING`).

**Estatísticas (F12):** `GET /estatisticas` retorna, calculados no banco (`COUNT`, `GROUP BY`, `AVG`, `MIN`, `MAX`): totais de pacientes, médicos e consultas; consultas por status, por especialidade e por médico; taxa de não comparecimento; duração média das consultas na agenda; primeira e última consulta.

## Regras de negócio

**Agendamento (`POST /consultas/`)** — todas revalidadas também ao remarcar:

1. Paciente, médico e especialidade devem existir e estar **ativos**, e o médico deve **atender a especialidade** escolhida.
2. A consulta deve ser em **data futura**.
3. O horário deve estar **dentro da agenda regular** do médico para aquela especialidade e dia da semana; o fim da consulta é calculado pela duração configurada na agenda.
4. O médico não pode estar em um **período bloqueado** (férias, congresso etc.).
5. **Sem conflito de horário:** o médico não pode ter outra consulta sobreposta, e o paciente também não. Consultas **canceladas liberam o horário**.

**Ciclo de vida da consulta**

6. Só é possível **cancelar, remarcar, marcar como realizada ou registrar falta** em consultas com status `agendada` (caso contrário, `409`).
7. Cancelar **não apaga** o registro: apenas muda o status, preservando o histórico.
8. O **atendimento (prontuário)** só pode ser registrado para consultas `realizada`, e apenas um por consulta.

**Agenda e cadastros**

9. Um médico não pode ter agendas sobrepostas no mesmo dia da semana.
10. Não é possível criar um bloqueio sobre um período que já tenha consultas agendadas.
11. Não é possível desvincular uma especialidade de um médico que ainda tem agenda nela.
12. Pacientes, médicos e especialidades com registros associados **não podem ser excluídos** (`409`); a orientação é desativá-los (`ativo = false`).
13. CPF, CRM, e-mail e nome de especialidade não podem se repetir.

## Funcionalidade específica do tema

**Disponibilidade e agendamento sem conflito de horário.**

- `GET /medicos/{id}/disponibilidade?data=2026-12-07&especialidade_id=1` retorna os horários livres do médico naquele dia, a partir da agenda regular, descontando consultas já marcadas (não canceladas) e bloqueios.
- `POST /consultas/` só confirma o agendamento se passar por todas as regras de 1 a 5 acima. Um médico pode atender em duas especialidades com dias e horários diferentes, e alterar a agenda regular **não modifica** o histórico de consultas já realizadas.

Exemplo de agendamento:

```json
POST /consultas/
{
  "paciente_id": 1,
  "medico_id": 2,
  "especialidade_id": 2,
  "data_hora_inicio": "2026-12-07T08:00:00"
}
```

## Tratamento de erros

Os erros do banco não são expostos ao usuário: são convertidos em respostas HTTP com mensagens claras.

| Código | Quando |
| --- | --- |
| `200` / `201` | Sucesso / recurso criado |
| `400` | Regra de negócio violada (ex.: paciente inativo, data no passado) |
| `404` | Recurso inexistente |
| `409` | Conflito (duplicidade, horário ocupado, exclusão com dependências) |
| `422` | Dados inválidos (validação) |
| `500` / `503` | Falha inesperada de persistência / banco indisponível |

## Uso do banco nos dois SGBDs

Para validar o funcionamento em ambos, basta trocar o `DATABASE_URL` no `.env` e repetir os passos 4 a 6 (`alembic upgrade head`, `python -m scripts.seed`, `uvicorn ...`) em um banco vazio.
