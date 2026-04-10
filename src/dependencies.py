from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from src.database import db
from src.security import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    db_token = await db.token.find_unique(where={"token": token})
    if not db_token:
        raise HTTPException(status_code=401, detail="Token revogado ou inválido")

    usuario = await db.usuario.find_unique(where={"id": payload["sub"]})
    if not usuario or not usuario.ativo:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")

    return usuario
