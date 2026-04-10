# Seed Backend — Residência de Software II

API REST em FastAPI com autenticação JWT e CRUD de usuários.

## Requisitos

- Python 3.11+
- PostgreSQL rodando localmente

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

```bash
cp .env.example .env
```

Edite `.env` com suas credenciais do banco:

```
DATABASE_URL="postgresql://usuario:senha@localhost:5432/seed_db"
SECRET_KEY="uma-chave-secreta-forte-qualquer"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Banco de dados

```bash
prisma db push
prisma generate
```

## Rodar o servidor

```bash
uvicorn main:app --reload
```

O servidor sobe em `http://localhost:8000`.

Documentação interativa: `http://localhost:8000/docs`

---

## Rotas disponíveis

### Health

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/` | Não | Verifica se a API está online |

---

### Auth

#### POST `/auth/login`

Autentica um usuário e retorna o token JWT.

**Body:**
```json
{
  "email": "usuario@email.com",
  "senha": "minhasenha"
}
```

**Resposta:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

#### POST `/auth/logout`

Revoga o token JWT do usuário autenticado.

**Header:**
```
Authorization: Bearer eyJ...
```

---

### Usuários

#### POST `/usuarios`

Cria um novo usuário. Rota pública (não requer token).

**Body:**
```json
{
  "nome": "João Silva",
  "email": "joao@email.com",
  "senha": "senha123",
  "role": "ALUNO"
}
```

Valores aceitos para `role`: `ALUNO`, `PROFESSOR`, `ADMIN`

---

#### GET `/usuarios`

Lista todos os usuários. Requer token.

**Header:**
```
Authorization: Bearer eyJ...
```

---

#### GET `/usuarios/{id}`

Retorna um usuário pelo ID. Requer token.

---

#### PUT `/usuarios/{id}`

Atualiza dados de um usuário. Requer token.

**Body (todos os campos são opcionais):**
```json
{
  "nome": "Novo Nome",
  "email": "novo@email.com",
  "role": "PROFESSOR",
  "ativo": true
}
```

---

#### DELETE `/usuarios/{id}`

Remove um usuário. Requer token. Retorna `204 No Content`.

---

## Exemplo de fluxo completo

```bash
# 1. Criar usuário
curl -X POST http://localhost:8000/usuarios \
  -H "Content-Type: application/json" \
  -d '{"nome": "Admin", "email": "admin@seed.com", "senha": "admin123", "role": "ADMIN"}'

# 2. Fazer login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@seed.com", "senha": "admin123"}'

# 3. Usar o token retornado para listar usuários
curl http://localhost:8000/usuarios \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"

# 4. Logout
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```
