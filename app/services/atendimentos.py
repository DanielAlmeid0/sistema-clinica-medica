from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Consulta, Especialidade, Medico, Paciente, Prontuario, Receita
from app.schemas.atendimento import (
    AtendimentoCreate,
    AtendimentoHistoricoItem,
    AtendimentoPublic,
    ProntuarioPacientePublic,
    ReceitaCreate,
    ReceitaPublic,
)


def registrar_atendimento(
    session: Session, consulta_id: int, dados: AtendimentoCreate
) -> AtendimentoPublic:
    consulta = session.get(Consulta, consulta_id)
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")
    if consulta.status != "realizada":
        raise HTTPException(
            status_code=400,
            detail="Só é possível registrar atendimento para consultas com o status 'realizada'",
        )

    atendimento_existente = session.exec(
        select(Prontuario).where(Prontuario.consulta_id == consulta_id)
    ).first()
    if atendimento_existente:
        raise HTTPException(
            status_code=400, detail="Atendimento já registrado para esta consulta"
        )

    atendimento = Prontuario(
        consulta_id=consulta_id,
        observacoes_clinicas=dados.observacoes_clinicas,
        prescricao_medicamentos=dados.prescricao_medicamentos,
        orientacoes=dados.orientacoes,
        data_retorno=dados.data_retorno,
    )
    session.add(atendimento)
    session.commit()
    session.refresh(atendimento)

    return AtendimentoPublic(
        id=atendimento.id,
        consulta_id=atendimento.consulta_id,
        observacoes_clinicas=atendimento.observacoes_clinicas,
        prescricao_medicamentos=atendimento.prescricao_medicamentos,
        orientacoes=atendimento.orientacoes,
        data_retorno=atendimento.data_retorno,
        receitas=[],
    )


def adicionar_receita(
    session: Session, atendimento_id: int, dados: ReceitaCreate
) -> ReceitaPublic:
    atendimento = session.get(Prontuario, atendimento_id)
    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")

    receita = Receita(
        atendimento_id=atendimento_id,
        medicamento=dados.medicamento,
        dosagem=dados.dosagem,
        frequencia=dados.frequencia,
        duracao=dados.duracao,
        observacoes=dados.observacoes,
    )
    session.add(receita)
    session.commit()
    session.refresh(receita)

    return ReceitaPublic.model_validate(receita)


def obter_prontuario_paciente(
    session: Session, paciente_id: int
) -> ProntuarioPacientePublic:
    paciente = session.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    linhas = session.exec(
        select(Prontuario, Consulta, Medico, Especialidade)
        .join(Consulta, Prontuario.consulta_id == Consulta.id)
        .join(Medico, Consulta.medico_id == Medico.id)
        .join(Especialidade, Consulta.especialidade_id == Especialidade.id)
        .where(Consulta.paciente_id == paciente_id)
        .order_by(Consulta.data_hora_inicio.desc())
    ).all()

    receitas_por_atendimento: dict[int, list[Receita]] = {}
    ids = [prontuario.id for prontuario, _, _, _ in linhas]
    if ids:
        receitas_do_paciente = session.exec(
            select(Receita).where(Receita.atendimento_id.in_(ids)).order_by(Receita.id)
        ).all()
        for receita in receitas_do_paciente:
            receitas_por_atendimento.setdefault(receita.atendimento_id, []).append(receita)


    historico: list[AtendimentoHistoricoItem] = []
    for prontuario, consulta, medico, especialidade in linhas:
        receitas = session.exec(
            select(Receita)
            .where(Receita.atendimento_id == prontuario.id)
            .order_by(Receita.id)
        ).all()

        historico.append(
            AtendimentoHistoricoItem(
                atendimento_id=prontuario.id,
                consulta_id=consulta.id,
                data_hora_inicio=consulta.data_hora_inicio,
                data_hora_fim=consulta.data_hora_fim,
                medico_id=medico.id,
                medico_nome=medico.nome,
                especialidade_id=especialidade.id,
                especialidade_nome=especialidade.nome,
                observacoes_clinicas=prontuario.observacoes_clinicas,
                prescricao_medicamentos=prontuario.prescricao_medicamentos,
                orientacoes=prontuario.orientacoes,
                data_retorno=prontuario.data_retorno,
                receitas=[ReceitaPublic.model_validate(r) for r in receitas],
            )
        )

    return ProntuarioPacientePublic(
        paciente_id=paciente.id,
        paciente_nome=paciente.nome,
        paciente_cpf=paciente.cpf,
        total_atendimentos=len(historico),
        atendimentos=historico,
    )
