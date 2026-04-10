from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr


class Role(str, Enum):
    ADMIN = "ADMIN"
    PROFESSOR = "PROFESSOR"
    ALUNO = "ALUNO"


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    role: Role = Role.ALUNO


class UsuarioUpdate(BaseModel):
    nome: str | None = None
    email: EmailStr | None = None
    role: Role | None = None
    ativo: bool | None = None


class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    role: str
    ativo: bool
    criadoEm: datetime
    atualizadoEm: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
