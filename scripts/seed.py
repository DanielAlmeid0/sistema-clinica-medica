import sys
from datetime import date, datetime, time, timedelta

from sqlmodel import Session, delete, select

from app.core.database import engine
from app.models import (
    AgendaRegular,
    BloqueioAgenda,
    Consulta,
    Especialidade,
    Medico,
    MedicoEspecialidade,
    Paciente,
    Prontuario,
)

ESPECIALIDADES = [
    ("Clínica Geral", "Atendimento clínico geral e acompanhamento preventivo"),
    ("Cardiologia", "Coração e sistema circulatório"),
    ("Dermatologia", "Pele, cabelos e unhas"),
    ("Pediatria", "Saúde de crianças e adolescentes"),
]

# nome, crm, ativo, [(especialidade, rqe)]
MEDICOS = [
    ("Dr. Carlos Mendes", "10101-CE", True, [("Clínica Geral", None)]),
    ("Dra. Helena Rocha", "20202-CE", True, [("Cardiologia", "1234"), ("Clínica Geral", None)]),
    ("Dr. Rafael Lima", "30303-CE", True, [("Dermatologia", "2345")]),
    ("Dra. Beatriz Nogueira", "40404-CE", True, [("Pediatria", "3456")]),
    ("Dr. Marcos Vieira", "50505-CE", True, [("Cardiologia", "4567")]),
    ("Dr. Paulo Ferraz", "60606-CE", False, [("Clínica Geral", None)]),
]

# nome, data de nascimento, ativo
PACIENTES = [
    ("Maria Souza", date(1990, 5, 20), True),
    ("Carlos Lima", date(1985, 3, 10), True),
    ("Ana Beatriz Costa", date(1978, 11, 2), True),
    ("João Pedro Alves", date(1969, 7, 15), True),
    ("Fernanda Ribeiro", date(1994, 1, 30), True),
    ("Roberto Santos", date(1955, 9, 8), True),
    ("Luciana Martins", date(1982, 12, 25), True),
    ("Pedro Henrique Dias", date(2000, 4, 17), True),
    ("Camila Ferreira", date(1998, 8, 5), True),
    ("Antônio Barbosa", date(1948, 6, 12), True),
    ("Sofia Oliveira", date(2018, 2, 14), True),
    ("Tereza Cavalcante", date(1960, 10, 1), False),
]

# crm, especialidade, dias da semana (0 = segunda), inicio, fim, duracao em minutos
AGENDAS = [
    ("10101-CE", "Clínica Geral", [0, 1, 3], "08:00", "12:00", 30),
    ("20202-CE", "Cardiologia", [1, 3], "08:00", "12:00", 30),
    ("20202-CE", "Clínica Geral", [0], "14:00", "17:00", 30),
    ("30303-CE", "Dermatologia", [2, 4], "09:00", "12:00", 20),
    ("40404-CE", "Pediatria", [0, 2, 4], "08:00", "11:00", 30),
    ("50505-CE", "Cardiologia", [0, 2], "14:00", "18:00", 30),
    ("60606-CE", "Clínica Geral", [0], "08:00", "12:00", 30),
]

# crm, semana (0 = atual), dia inicial, hora inicial, dia final, hora final, motivo
BLOQUEIOS = [
    ("10101-CE", 1, 0, "10:00", 0, "12:00", "Reunião administrativa"),
    ("20202-CE", 2, 1, "08:00", 3, "18:00", "Congresso de Cardiologia"),
    ("30303-CE", 2, 2, "09:00", 4, "12:00", "Férias"),
]

# observações, prescrição, orientações, retorno em dias
PRONTUARIOS = {
    "Clínica Geral": ("Paciente em bom estado geral, sem queixas relevantes.", "Vitamina D 2000 UI ao dia", "Manter hidratação e atividade física", 90),
    "Cardiologia": ("Pressão arterial controlada, ritmo cardíaco regular.", "Losartana 50 mg ao dia", "Reduzir sal e repetir exames em 60 dias", 60),
    "Dermatologia": ("Lesão cutânea superficial sem sinais de infecção.", "Pomada de corticoide tópico", "Evitar exposição solar prolongada", 30),
    "Pediatria": ("Criança com desenvolvimento adequado para a idade.", None, "Manter vacinação em dia e boa alimentação", 180),
}

# paciente (posicao na lista), crm, especialidade, semana, dia, hora, status
CONSULTAS = [
    (1, "10101-CE", "Clínica Geral", -2, 0, "08:00", "realizada"),
    (2, "10101-CE", "Clínica Geral", -2, 0, "08:30", "realizada"),
    (3, "10101-CE", "Clínica Geral", -2, 1, "09:00", "nao_compareceu"),
    (1, "10101-CE", "Clínica Geral", -1, 3, "08:00", "realizada"),
    (4, "10101-CE", "Clínica Geral", 1, 0, "08:00", "agendada"),
    (5, "10101-CE", "Clínica Geral", 1, 1, "09:30", "agendada"),
    (2, "10101-CE", "Clínica Geral", 1, 1, "10:00", "cancelada"),
    (6, "20202-CE", "Cardiologia", -2, 1, "08:00", "realizada"),
    (7, "20202-CE", "Cardiologia", -1, 1, "09:00", "realizada"),
    (6, "20202-CE", "Cardiologia", -1, 3, "08:30", "nao_compareceu"),
    (8, "20202-CE", "Cardiologia", 1, 1, "08:00", "agendada"),
    (6, "20202-CE", "Cardiologia", 1, 3, "10:00", "agendada"),
    (9, "20202-CE", "Clínica Geral", 1, 0, "14:00", "agendada"),
    (10, "30303-CE", "Dermatologia", -1, 2, "09:00", "realizada"),
    (3, "30303-CE", "Dermatologia", -1, 4, "09:20", "realizada"),
    (10, "30303-CE", "Dermatologia", 1, 2, "09:40", "agendada"),
    (11, "40404-CE", "Pediatria", -2, 0, "08:00", "realizada"),
    (12, "40404-CE", "Pediatria", -1, 2, "08:30", "realizada"),
    (11, "40404-CE", "Pediatria", 1, 0, "08:00", "agendada"),
    (11, "40404-CE", "Pediatria", 1, 4, "09:00", "cancelada"),
    (7, "50505-CE", "Cardiologia", -1, 0, "14:00", "realizada"),
    (5, "50505-CE", "Cardiologia", 1, 2, "15:00", "agendada"),
]


def segunda_da_semana(semana: int) -> date:
    hoje = date.today()
    return hoje - timedelta(days=hoje.weekday()) + timedelta(weeks=semana)


def momento(semana: int, dia: int, hora: str) -> datetime:
    return datetime.combine(segunda_da_semana(semana) + timedelta(days=dia), time.fromisoformat(hora))


def banco_tem_dados(session: Session) -> bool:
    return any(
        session.exec(select(modelo)).first() is not None
        for modelo in (Especialidade, Medico, Paciente)
    )


def limpar_banco(session: Session) -> None:
    for modelo in (
        Prontuario,
        Consulta,
        BloqueioAgenda,
        AgendaRegular,
        MedicoEspecialidade,
        Medico,
        Paciente,
        Especialidade,
    ):
        session.exec(delete(modelo))
    session.commit()


def criar_cadastros(session: Session):
    especialidades = {}
    for nome, descricao in ESPECIALIDADES:
        especialidades[nome] = Especialidade(nome=nome, descricao=descricao)
        session.add(especialidades[nome])

    medicos = {}
    for i, (nome, crm, ativo, _) in enumerate(MEDICOS, start=1):
        medicos[crm] = Medico(
            nome=nome, crm=crm, telefone=f"88991000{i:03d}", email=f"medico{i}@clinica.com", ativo=ativo
        )
        session.add(medicos[crm])

    pacientes = []
    for i, (nome, nascimento, ativo) in enumerate(PACIENTES, start=1):
        paciente = Paciente(
            nome=nome,
            cpf=f"123456789{i:02d}",
            telefone=f"889880000{i:02d}",
            email=f"paciente{i:02d}@email.com",
            data_nasc=nascimento,
            ativo=ativo,
        )
        session.add(paciente)
        pacientes.append(paciente)

    session.flush()

    for _, crm, _, vinculos in MEDICOS:
        for nome_especialidade, rqe in vinculos:
            session.add(
                MedicoEspecialidade(
                    medico_id=medicos[crm].id,
                    especialidade_id=especialidades[nome_especialidade].id,
                    rqe=rqe,
                )
            )
    session.flush()

    return especialidades, medicos, pacientes


def criar_agendas_e_bloqueios(session: Session, especialidades: dict, medicos: dict) -> dict:
    duracoes = {}
    for crm, nome_especialidade, dias, inicio, fim, duracao in AGENDAS:
        for dia in dias:
            session.add(
                AgendaRegular(
                    medico_id=medicos[crm].id,
                    especialidade_id=especialidades[nome_especialidade].id,
                    dia_semana=dia,
                    hora_inicio=time.fromisoformat(inicio),
                    hora_fim=time.fromisoformat(fim),
                    duracao_consulta=duracao,
                )
            )
        duracoes[(crm, nome_especialidade)] = duracao

    for crm, semana, dia_i, hora_i, dia_f, hora_f, motivo in BLOQUEIOS:
        session.add(
            BloqueioAgenda(
                medico_id=medicos[crm].id,
                data_hora_inicio=momento(semana, dia_i, hora_i),
                data_hora_fim=momento(semana, dia_f, hora_f),
                motivo=motivo,
            )
        )

    return duracoes


def criar_consultas(session: Session, especialidades: dict, medicos: dict, pacientes: list, duracoes: dict) -> None:
    realizadas = []
    for numero, crm, nome_especialidade, semana, dia, hora, status in CONSULTAS:
        inicio = momento(semana, dia, hora)
        consulta = Consulta(
            paciente_id=pacientes[numero - 1].id,
            medico_id=medicos[crm].id,
            especialidade_id=especialidades[nome_especialidade].id,
            data_hora_inicio=inicio,
            data_hora_fim=inicio + timedelta(minutes=duracoes[(crm, nome_especialidade)]),
            status=status,
        )
        session.add(consulta)
        if status == "realizada":
            realizadas.append((consulta, nome_especialidade))

    session.flush()

    for consulta, nome_especialidade in realizadas:
        observacoes, prescricao, orientacoes, retorno = PRONTUARIOS[nome_especialidade]
        session.add(
            Prontuario(
                consulta_id=consulta.id,
                observacoes_clinicas=observacoes,
                prescricao_medicamentos=prescricao,
                orientacoes=orientacoes,
                data_retorno=retorno,
            )
        )


def executar(limpar: bool = False) -> None:
    engine.echo = False

    with Session(engine) as session:
        if banco_tem_dados(session):
            if not limpar:
                print("O banco já possui dados. Use --limpar para apagar tudo e popular novamente.")
                return
            limpar_banco(session)

        especialidades, medicos, pacientes = criar_cadastros(session)
        duracoes = criar_agendas_e_bloqueios(session, especialidades, medicos)
        criar_consultas(session, especialidades, medicos, pacientes, duracoes)
        session.commit()

    print(
        f"Seed concluído: {len(especialidades)} especialidades, {len(medicos)} médicos, "
        f"{len(pacientes)} pacientes, {len(CONSULTAS)} consultas."
    )


if __name__ == "__main__":
    executar(limpar="--limpar" in sys.argv)
