from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database import db
from src.schemas import LoginRequest, TokenResponse
from src.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])

bearer_scheme = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    usuario = await db.usuario.find_unique(where={"email": data.email})

    if not usuario or not verify_password(data.senha, usuario.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    token, expires_at = create_access_token({"sub": usuario.id, "role": usuario.role})

    await db.token.create(data={
        "token": token,
        "usuarioId": usuario.id,
        "expiresAt": expires_at,
    })

    return {"access_token": token}


@router.post("/logout", status_code=204)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    db_token = await db.token.find_unique(where={"token": token})

    if db_token:
        await db.token.delete(where={"token": token})
