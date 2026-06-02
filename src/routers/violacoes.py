from fastapi import APIRouter, Depends, Query

from src.database import db
from src.dependencies import require_admin
from src.schemas import (
    ViolacaoEtapaResumo,
    ViolacaoPainelItem,
    ViolacaoPainelResponse,
)

router = APIRouter(prefix="/violacoes", tags=["Violacoes"])

_INCLUDE = {
    "resultado": {
        "include": {
            "aluno": {"include": {"usuario": True}},
            "simulado": {"include": {"componente": True}},
        }
    }
}


@router.get("", response_model=ViolacaoPainelResponse)
async def listar_violacoes(
    simulado_id: str | None = Query(default=None),
    _=Depends(require_admin),
):
    where: dict = {}
    if simulado_id:
        where = {"resultado": {"is": {"simuladoId": simulado_id}}}

    violacoes = await db.violacaoprova.find_many(
        where=where,
        include=_INCLUDE,
        order={"criadoEm": "desc"},
    )

    ocorrencias: list[ViolacaoPainelItem] = []
    resumo: dict = {}

    for v in violacoes:
        resultado = v.resultado
        simulado = resultado.simulado if resultado else None
        aluno = resultado.aluno if resultado else None
        usuario = aluno.usuario if aluno else None

        etapa_titulo = simulado.titulo if simulado else "—"
        componente_nome = simulado.componente.nome if simulado and simulado.componente else "—"

        ocorrencias.append(ViolacaoPainelItem(
            id=v.id,
            resultadoId=v.resultadoId,
            tipo=v.tipo,
            detalhe=v.detalhe,
            criadoEm=v.criadoEm,
            alunoNome=usuario.nome if usuario else "—",
            alunoCpf=usuario.cpf if usuario else "—",
            etapaTitulo=etapa_titulo,
            componenteNome=componente_nome,
        ))

        if simulado:
            entrada = resumo.setdefault(
                simulado.id,
                {"titulo": etapa_titulo, "total": 0, "alunos": set()},
            )
            entrada["total"] += 1
            if aluno:
                entrada["alunos"].add(aluno.id)

    por_etapa = [
        ViolacaoEtapaResumo(
            simuladoId=sid,
            etapaTitulo=dados["titulo"],
            totalViolacoes=dados["total"],
            alunosEnvolvidos=len(dados["alunos"]),
        )
        for sid, dados in resumo.items()
    ]
    por_etapa.sort(key=lambda e: e.totalViolacoes, reverse=True)

    return ViolacaoPainelResponse(
        total=len(ocorrencias),
        porEtapa=por_etapa,
        ocorrencias=ocorrencias,
    )
