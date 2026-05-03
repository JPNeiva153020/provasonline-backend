from fastapi import APIRouter, Depends

from src.database import db
from src.dependencies import get_current_user
from src.schemas import EscolaResumo, ModalidadeResumo

router = APIRouter(prefix="/catalogo", tags=["Catálogo"])


@router.get("/escolas", response_model=list[EscolaResumo])
async def listar_escolas(_=Depends(get_current_user)):
    escolas = await db.escola.find_many(
        where={"ativo": True},
        order={"nome": "asc"},
    )
    return [EscolaResumo(id=e.id, nome=e.nome) for e in escolas]


@router.get("/modalidades", response_model=list[ModalidadeResumo])
async def listar_modalidades(_=Depends(get_current_user)):
    modalidades = await db.modalidade.find_many(
        where={"ativo": True},
        include={"nivel": True},
        order=[{"nivelId": "asc"}, {"nome": "asc"}],
    )
    return [
        ModalidadeResumo(
            id=m.id,
            nome=f"{m.nivel.nome} — {m.nome}",
        )
        for m in modalidades
    ]