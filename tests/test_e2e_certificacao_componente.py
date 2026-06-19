"""E2E do fluxo de certificação multi-componente (a correção do dossiê).

Cria uma etapa certificadora com 2 componentes obrigatórios, dirige o fluxo HTTP
do aluno (iniciar → responder tudo certo → submeter) e verifica que:
  - cada tentativa foi persistida com seu componenteId (etiquetagem no sorteio);
  - o resultado traz a quebra por componente, ambos aprovados;
  - o certificado de CONCLUSÃO é emitido (todos os obrigatórios aprovados).

Questões vêm do mock do conftest (autouse), então é determinístico e não toca
a API externa nem o banco de PROD.
"""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from prisma import Json

from src.database import db

CPF_ALUNO = "11122233396"


@pytest_asyncio.fixture
async def etapa_cert(conexao_db):
    nivel = await db.nivelensino.create(data={"nome": "Ensino Médio E2E", "ordem": 2})
    modalidade = await db.modalidade.create(
        data={"nivel": {"connect": {"id": nivel.id}}, "nome": "Regular E2E"}
    )
    # Slugs DISTINTOS por componente para que o sorteio etiquete cada questão com
    # o componente certo (o mock ignora o slug e devolve o mesmo banco).
    comp1 = await db.componentecurricular.create(
        data={
            "modalidade": {"connect": {"id": modalidade.id}},
            "nome": "Comp E2E Humanas",
            "codigo": "E2E1",
            "questionsSubjectSlug": "e2e-humanas",
        }
    )
    comp2 = await db.componentecurricular.create(
        data={
            "modalidade": {"connect": {"id": modalidade.id}},
            "nome": "Comp E2E Natureza",
            "codigo": "E2E2",
            "questionsSubjectSlug": "e2e-natureza",
        }
    )
    for c in (comp1, comp2):
        await db.nivelcomponente.create(
            data={
                "nivel": {"connect": {"id": nivel.id}},
                "componente": {"connect": {"id": c.id}},
                "obrigatorio": True,
            }
        )

    professor = await db.professor.find_first()
    assert professor is not None, "DB de teste precisa de ao menos um professor"
    agora = datetime.now(timezone.utc)
    simulado = await db.simulado.create(
        data={
            "titulo": "Etapa E2E Multi-Componente",
            "componente": {"connect": {"id": comp1.id}},
            "componenteIds": Json([comp1.id, comp2.id]),
            "professor": {"connect": {"id": professor.id}},
            "qtdFacil": 2, "qtdMedio": 2, "qtdDificil": 2,
            "vagas": 5, "duracaoMinutos": 60,
            "janelaInicio": agora - timedelta(minutes=5),
            "janelaFim": agora + timedelta(hours=2),
            "status": "PUBLICADO",
            "embaralharAlternativas": False,
            "geraCertificado": True,
            "nivelEnsino": {"connect": {"id": nivel.id}},
            "notaMinimaCertificacao": 6.0,
        }
    )

    usuario = await db.usuario.find_first(where={"cpf": CPF_ALUNO})
    aluno = await db.aluno.find_first(where={"usuarioId": usuario.id})

    yield {"nivel": nivel, "comps": (comp1, comp2), "simulado": simulado, "aluno": aluno}

    await db.certificado.delete_many(where={"alunoId": aluno.id, "nivelId": nivel.id})
    await db.aproveitamentocandidato.delete_many(where={"alunoId": aluno.id, "nivelId": nivel.id})
    resultados = await db.resultadoaluno.find_many(where={"simuladoId": simulado.id})
    for r in resultados:
        await db.resultadoaluno.delete(where={"id": r.id})
    await db.simulado.delete(where={"id": simulado.id})
    await db.nivelcomponente.delete_many(where={"nivelId": nivel.id})
    await db.componentecurricular.delete(where={"id": comp1.id})
    await db.componentecurricular.delete(where={"id": comp2.id})
    await db.modalidade.delete(where={"id": modalidade.id})
    await db.nivelensino.delete(where={"id": nivel.id})


@pytest.mark.asyncio
async def test_fluxo_certificacao_multi_componente_emite_conclusao(
    client, token_aluno, auth, etapa_cert
):
    simulado = etapa_cert["simulado"]
    nivel = etapa_cert["nivel"]
    aluno = etapa_cert["aluno"]
    comp1, comp2 = etapa_cert["comps"]

    # 1) Inicia a prova
    r = await client.post(f"/aluno/iniciar-prova/{simulado.id}", headers=auth(token_aluno))
    assert r.status_code == 201, r.text
    resultado_id = r.json()["resultadoId"]
    assert r.json()["totalQuestoes"] == 6

    # 2) Cada tentativa foi persistida COM componenteId, cobrindo os 2 componentes
    tentativas = await db.tentativaquestao.find_many(where={"resultadoId": resultado_id})
    assert all(t.componenteId is not None for t in tentativas)
    assert {t.componenteId for t in tentativas} == {comp1.id, comp2.id}

    # 3) Responde TUDO certo (lê o gabarito do banco; alternativas não embaralhadas)
    respostas = [{"questaoId": t.questaoId, "resposta": t.respostaCorreta} for t in tentativas]
    r2 = await client.patch(
        f"/aluno/responder/{resultado_id}",
        json={"respostas": respostas},
        headers=auth(token_aluno),
    )
    assert r2.status_code == 200, r2.text

    # 4) Submete e confere a quebra por componente (ambos aprovados, nota 10)
    r3 = await client.post(f"/aluno/submeter/{resultado_id}", headers=auth(token_aluno))
    assert r3.status_code == 200, r3.text
    corpo = r3.json()
    assert corpo["statusResultado"] == "FINALIZADO"
    componentes = corpo["componentes"]
    assert componentes is not None and len(componentes) == 2
    assert all(c["aprovado"] is True for c in componentes)
    assert all(c["nota"] == 10.0 for c in componentes)

    # 5) Certificado de CONCLUSÃO emitido (todos os obrigatórios aprovados)
    cert = await db.certificado.find_first(
        where={"alunoId": aluno.id, "nivelId": nivel.id}
    )
    assert cert is not None
    assert cert.tipo == "CONCLUSAO"
    assert cert.codigoVerificacao

    # crédito por componente registrado para os 2 obrigatórios
    aprov = await db.aproveitamentocandidato.find_many(
        where={"alunoId": aluno.id, "nivelId": nivel.id, "aprovado": True}
    )
    assert {a.componenteId for a in aprov} == {comp1.id, comp2.id}
