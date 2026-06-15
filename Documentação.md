# Documentação de APIs — Hub Social

### 🔐 Autenticação

| # | Método | Endpoint | Descrição | Auth | Códigos de status |
|---|---|---|---|---|---|
| 1 | POST | `/auth/cadastro` | Criar conta com senha criptografada (bcrypt) | ❌ | 201, 409, 422 |
| 2 | POST | `/auth/login` | Login com e-mail e senha → retorna JWT | ❌ | 200, 401, 403 |
| 3 | GET  | `/auth/me` | Retorna dados do usuário autenticado | ✅ | 200, 401 |

### 💰 Doações

| # | Método | Endpoint | Descrição | Auth | Códigos de status |
|---|---|---|---|---|---|
| 4 | GET    | `/doacoes/` | Listar todas as doações da ONG | ✅ | 200, 401 |
| 5 | POST   | `/doacoes/` | Registrar nova doação (financeira ou em espécie) | ✅ | 201, 401 |
| 6 | PATCH  | `/doacoes/{id}/status` | Atualizar status da doação | ✅ | 200, 400, 404 |
| 7 | DELETE | `/doacoes/{id}` | Remover doação | ✅ | 204, 404 |

### 👥 Voluntários

| # | Método | Endpoint | Descrição | Auth | Códigos de status |
|---|---|---|---|---|---|
| 8  | GET   | `/voluntarios/` | Listar voluntários da ONG | ✅ | 200, 401 |
| 9  | POST  | `/voluntarios/` | Cadastrar voluntário (respeita limite do plano) | ✅ | 201, 403 |
| 10 | PATCH | `/voluntarios/{id}/desativar` | Desativar voluntário | ✅ | 200, 404 |
| 11 | DELETE | `/voluntarios/{id}` | Remover voluntário permanentemente | ✅ | 204, 404 |

### 📅 Eventos (Plano Impacto e Transformação)

| # | Método | Endpoint | Descrição | Auth | Códigos de status |
|---|---|---|---|---|---|
| 12 | GET    | `/eventos/` | Listar eventos ordenados por data | ✅ | 200, 403 |
| 13 | POST   | `/eventos/` | Criar novo evento | ✅ | 201, 403 |
| 14 | PUT    | `/eventos/{id}` | Editar evento existente | ✅ | 200, 403, 404 |
| 15 | DELETE | `/eventos/{id}` | Remover evento | ✅ | 204, 403, 404 |

### 📊 Relatórios (Plano Impacto e Transformação)

| # | Método | Endpoint | Descrição | Auth | Códigos de status |
|---|---|---|---|---|---|
| 16 | GET | `/relatorios/visao-geral` | Resumo completo: doações, voluntários e eventos | ✅ | 200, 403 |
| 17 | GET | `/relatorios/doacoes-por-tipo` | Doações agrupadas por tipo (financeira/espécie) | ✅ | 200, 403 |

---

## Exemplos completos de Request e Response

---

### 1. POST /auth/cadastro

**Request:**
```json
{
  "nome":     "Maria Silva",
  "email":    "maria@ong.org.br",
  "senha":    "Senha123",
  "telefone": "(11) 99999-9999",
  "cargo":    "Diretora",
  "nome_ong": "Lar dos Bichinhos",
  "plano":    "impacto",
  "forma_pag":"cartao"
}
```

**Response 201 – Criado com sucesso:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type":   "bearer",
  "usuario_id":   1,
  "nome":         "Maria Silva",
  "nome_ong":     "Lar dos Bichinhos",
  "plano":        "impacto"
}
```

**Response 409 – E-mail duplicado:**
```json
{ "detail": "Este e-mail já está cadastrado. Tente fazer login." }
```

**Response 422 – Senha fraca:**
```json
{
  "detail": [{ "msg": "A senha deve ter no mínimo 8 caracteres." }]
}
```

---

### 2. POST /auth/login

**Request (form-data):**
```
username = maria@ong.org.br
password = Senha123
```

**Response 200 – Login realizado:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type":   "bearer",
  "usuario_id":   1,
  "nome":         "Maria Silva",
  "nome_ong":     "Lar dos Bichinhos",
  "plano":        "impacto"
}
```

**Response 401 – Credenciais inválidas:**
```json
{ "detail": "E-mail ou senha incorretos." }
```

---

### 3. GET /auth/me

**Header:** `Authorization: Bearer <token>`

**Response 200:**
```json
{
  "id":       1,
  "nome":     "Maria Silva",
  "email":    "maria@ong.org.br",
  "nome_ong": "Lar dos Bichinhos",
  "plano":    "impacto",
  "status":   "ativo",
  "is_admin": false
}
```

---

### 4. POST /doacoes/

**Header:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "doador":    "João Souza",
  "tipo":      "financeira",
  "descricao": "Doação mensal",
  "valor":     "200.00"
}
```

**Response 201:**
```json
{
  "id":         1,
  "usuario_id": 1,
  "doador":     "João Souza",
  "tipo":       "financeira",
  "descricao":  "Doação mensal",
  "valor":      "200.00",
  "status":     "pendente",
  "criado_em":  "2025-05-01T14:30:00"
}
```

---

### 5. PATCH /doacoes/{id}/status

**Header:** `Authorization: Bearer <token>`

**Parâmetros:**
- `doacao_id` (path): `1`
- `novo_status` (query): `confirmada`

**Response 200:**
```json
{ "mensagem": "Status atualizado para 'confirmada'." }
```

**Response 400 – Status inválido:**
```json
{ "detail": "Status inválido. Use: pendente, confirmada ou cancelada." }
```

---

### 6. POST /voluntarios/

**Header:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "nome":     "Ana Lima",
  "email":    "ana@email.com",
  "telefone": "(11) 98888-7777",
  "area":     "veterinária"
}
```

**Response 201:**
```json
{
  "id":         1,
  "usuario_id": 1,
  "nome":       "Ana Lima",
  "email":      "ana@email.com",
  "telefone":   "(11) 98888-7777",
  "area":       "veterinária",
  "ativo":      true,
  "criado_em":  "2025-05-01T10:00:00"
}
```

**Response 403 – Limite do plano atingido:**
```json
{
  "detail": "Seu plano 'semente' permite até 10 voluntários. Faça upgrade para cadastrar mais."
}
```

---

### 7. POST /eventos/

**Header:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "nome":      "Feira de Adoção",
  "tipo":      "adocao",
  "data":      "2025-06-15",
  "local":     "Parque Ibirapuera - SP",
  "descricao": "Evento de adoção responsável de cães e gatos"
}
```

**Response 201:**
```json
{
  "id":         1,
  "usuario_id": 1,
  "nome":       "Feira de Adoção",
  "tipo":       "adocao",
  "data":       "2025-06-15",
  "local":      "Parque Ibirapuera - SP",
  "descricao":  "Evento de adoção responsável de cães e gatos",
  "criado_em":  "2025-05-01T09:00:00"
}
```

**Response 403 – Plano insuficiente:**
```json
{ "detail": "Calendário de Eventos disponível a partir do Plano Impacto." }
```

---

### 8. GET /relatorios/visao-geral

**Header:** `Authorization: Bearer <token>`

**Response 200 (Plano Impacto ou Transformação):**
```json
{
  "ong":   "Lar dos Bichinhos",
  "plano": "impacto",
  "doacoes": {
    "total":            18,
    "confirmadas":      14,
    "valor_arrecadado": 3450.00
  },
  "voluntarios": {
    "ativos":       12,
    "limite_plano": 25
  },
  "eventos": {
    "total": 5
  }
}
```

**Response 403 (Plano Semente):**
```json
{ "detail": "Relatórios disponíveis a partir do Plano Impacto." }
```

---

## Permissões por plano

| Recurso | Semente | Impacto | Transformação |
|---|---|---|---|
| Doações | ✅ ilimitadas | ✅ ilimitadas | ✅ ilimitadas |
| Voluntários | ✅ até 10 | ✅ até 25 | ✅ ilimitados |
| Eventos | ❌ | ✅ | ✅ |
| Relatórios | ❌ | ✅ | ✅ |
| Plataforma personalizada | ❌ | ❌ | ✅ |
```
**Response 403 (Plano Semente):**
```json
{ "detail": "Relatórios disponíveis a partir do Plano Impacto." }
```
