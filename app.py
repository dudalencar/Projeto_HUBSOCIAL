# ============================================================
#  HUB SOCIAL – app.py
#  Backend completo em um único arquivo
#  FastAPI + SQLite + bcrypt + JWT
# ============================================================
#
#  INSTALAÇÃO (uma única vez):
#  pip install fastapi uvicorn passlib[bcrypt] python-jose[cryptography] python-multipart sqlalchemy pydantic[email]
#
#  PARA RODAR:
#  uvicorn app:app --reload
#
#  DOCUMENTAÇÃO INTERATIVA:
#  http://localhost:8000/docs
# ============================================================

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import bcrypt as _bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timedelta
from typing import Optional, List
import enum


# ============================================================
#  CONFIGURAÇÕES
# ============================================================

DATABASE_URL  = "sqlite:///./hubsocial.db"
SECRET_KEY    = "hubsocial_super_secret_key_troque_em_producao_2025"
ALGORITHM     = "HS256"
TOKEN_EXPIRA_HORAS = 8


# ============================================================
#  BANCO DE DADOS – conexão SQLite
# ============================================================

engine       = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
#  ENUMS
# ============================================================

class PlanoEnum(str, enum.Enum):
    semente       = "semente"
    impacto       = "impacto"
    transformacao = "transformacao"

class StatusEnum(str, enum.Enum):
    ativo    = "ativo"
    inativo  = "inativo"
    pendente = "pendente"


# ============================================================
#  MODELOS (tabelas do banco)
# ============================================================

class Usuario(Base):
    __tablename__ = "usuarios"
    id            = Column(Integer, primary_key=True, index=True)
    nome          = Column(String(120), nullable=False)
    email         = Column(String(180), unique=True, index=True, nullable=False)
    senha_hash    = Column(String(255), nullable=False)
    telefone      = Column(String(20),  nullable=True)
    cargo         = Column(String(80),  nullable=True)
    nome_ong      = Column(String(150), nullable=False)
    cnpj          = Column(String(20),  nullable=True)
    endereco      = Column(String(255), nullable=True)
    plano         = Column(Enum(PlanoEnum), default=PlanoEnum.semente)
    forma_pag     = Column(String(30),  nullable=True)
    status        = Column(Enum(StatusEnum), default=StatusEnum.ativo)
    is_admin      = Column(Boolean, default=False)
    criado_em     = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

class Doacao(Base):
    __tablename__ = "doacoes"
    id         = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False)
    doador     = Column(String(120), nullable=False)
    tipo       = Column(String(60),  nullable=False)
    descricao  = Column(Text,        nullable=True)
    valor      = Column(String(30),  nullable=True)
    status     = Column(String(30),  default="pendente")
    criado_em  = Column(DateTime(timezone=True), server_default=func.now())

class Voluntario(Base):
    __tablename__ = "voluntarios"
    id         = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False)
    nome       = Column(String(120), nullable=False)
    email      = Column(String(180), nullable=True)
    telefone   = Column(String(20),  nullable=True)
    area       = Column(String(80),  nullable=True)
    ativo      = Column(Boolean, default=True)
    criado_em  = Column(DateTime(timezone=True), server_default=func.now())

class Evento(Base):
    __tablename__ = "eventos"
    id         = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False)
    nome       = Column(String(150), nullable=False)
    tipo       = Column(String(60),  nullable=True)
    data       = Column(String(20),  nullable=False)
    local      = Column(String(200), nullable=True)
    descricao  = Column(Text,        nullable=True)
    criado_em  = Column(DateTime(timezone=True), server_default=func.now())

# Cria as tabelas no banco se não existirem
Base.metadata.create_all(bind=engine)


# ============================================================
#  SEGURANÇA – bcrypt + JWT
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_senha(senha: str) -> str:
    salt = _bcrypt.gensalt()
    return _bcrypt.hashpw(senha[:72].encode(), salt).decode()

def verificar_senha(senha: str, hash_: str) -> bool:
    return _bcrypt.checkpw(senha[:72].encode(), hash_.encode())

def criar_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRA_HORAS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ============================================================
#  DEPENDÊNCIA – usuário autenticado via token
# ============================================================

def get_usuario_atual(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db)
) -> Usuario:
    payload = decodificar_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload.get("sub")
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")
    if usuario.status == StatusEnum.inativo:
        raise HTTPException(status_code=403, detail="Conta inativa. Entre em contato com o suporte.")
    return usuario


# ============================================================
#  SCHEMAS PYDANTIC – validação de entrada e saída
# ============================================================

# ── Auth ────────────────────────────────────────────────────
class CadastroSchema(BaseModel):
    nome:      str
    email:     EmailStr
    senha:     str
    telefone:  Optional[str] = None
    cargo:     Optional[str] = None
    nome_ong:  str
    cnpj:      Optional[str] = None
    endereco:  Optional[str] = None
    plano:     PlanoEnum     = PlanoEnum.semente
    forma_pag: Optional[str] = None

    @field_validator("senha")
    @classmethod
    def senha_forte(cls, v):
        if len(v) < 8:
            raise ValueError("A senha deve ter no mínimo 8 caracteres.")
        if not any(c.isdigit() for c in v):
            raise ValueError("A senha deve conter ao menos um número.")
        return v

class TokenSchema(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    usuario_id:   int
    nome:         str
    nome_ong:     str
    plano:        str

class UsuarioPublico(BaseModel):
    id:       int
    nome:     str
    email:    str
    nome_ong: str
    plano:    str
    status:   str
    is_admin: bool
    class Config:
        from_attributes = True

# ── Doações ──────────────────────────────────────────────────
class DoacaoIn(BaseModel):
    doador:    str
    tipo:      str
    descricao: Optional[str] = None
    valor:     Optional[str] = None
    status:    Optional[str] = "pendente"

class DoacaoOut(DoacaoIn):
    id:         int
    usuario_id: int
    criado_em:  datetime
    class Config:
        from_attributes = True

# ── Voluntários ──────────────────────────────────────────────
class VoluntarioIn(BaseModel):
    nome:     str
    email:    Optional[str] = None
    telefone: Optional[str] = None
    area:     Optional[str] = None

class VoluntarioOut(VoluntarioIn):
    id:         int
    usuario_id: int
    ativo:      bool
    criado_em:  datetime
    class Config:
        from_attributes = True

# ── Eventos ──────────────────────────────────────────────────
class EventoIn(BaseModel):
    nome:      str
    tipo:      Optional[str] = None
    data:      str
    local:     Optional[str] = None
    descricao: Optional[str] = None

class EventoOut(EventoIn):
    id:         int
    usuario_id: int
    criado_em:  datetime
    class Config:
        from_attributes = True


# ============================================================
#  LIMITES E PERMISSÕES POR PLANO
# ============================================================

LIMITE_VOLUNTARIOS = {
    PlanoEnum.semente:       10,
    PlanoEnum.impacto:       25,
    PlanoEnum.transformacao: None,   # ilimitado
}
PLANOS_EVENTOS    = {PlanoEnum.impacto, PlanoEnum.transformacao}
PLANOS_RELATORIO  = {PlanoEnum.impacto, PlanoEnum.transformacao}

def checar_limite_voluntarios(usuario: Usuario, db: Session):
    limite = LIMITE_VOLUNTARIOS.get(usuario.plano)
    if limite is None:
        return
    total = db.query(Voluntario).filter(
        Voluntario.usuario_id == usuario.id,
        Voluntario.ativo == True
    ).count()
    if total >= limite:
        raise HTTPException(
            status_code=403,
            detail=f"Seu plano '{usuario.plano}' permite até {limite} voluntários. Faça upgrade para adicionar mais."
        )

def checar_plano_eventos(usuario: Usuario):
    if usuario.plano not in PLANOS_EVENTOS:
        raise HTTPException(
            status_code=403,
            detail="Calendário de Eventos disponível a partir do Plano Impacto."
        )

def checar_plano_relatorio(usuario: Usuario):
    if usuario.plano not in PLANOS_RELATORIO:
        raise HTTPException(
            status_code=403,
            detail="Relatórios disponíveis a partir do Plano Impacto."
        )


# ============================================================
#  APLICAÇÃO FASTAPI
# ============================================================

app = FastAPI(
    title       = "Hub Social API",
    description = "Sistema de gestão para ONGs – Hub Social",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)


# ============================================================
#  ROTAS – STATUS
# ============================================================

@app.get("/", tags=["Status"])
def root():
    return {"status": "online", "sistema": "Hub Social API", "docs": "/docs"}

@app.get("/health", tags=["Status"])
def health():
    return {"status": "ok"}


# ============================================================
#  ROTAS – AUTENTICAÇÃO
# ============================================================

@app.post("/auth/cadastro", response_model=TokenSchema, status_code=201, tags=["Autenticação"])
def cadastrar(dados: CadastroSchema, db: Session = Depends(get_db)):
    """Cria conta com senha criptografada (bcrypt) e retorna JWT."""
    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado. Tente fazer login.")

    novo = Usuario(
        nome       = dados.nome.strip(),
        email      = dados.email.lower().strip(),
        senha_hash = hash_senha(dados.senha),
        telefone   = dados.telefone,
        cargo      = dados.cargo,
        nome_ong   = dados.nome_ong.strip(),
        cnpj       = dados.cnpj,
        endereco   = dados.endereco,
        plano      = dados.plano,
        forma_pag  = dados.forma_pag,
        status     = StatusEnum.ativo,
        is_admin   = False,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)

    token = criar_token({"sub": novo.email, "plano": novo.plano})
    return TokenSchema(access_token=token, usuario_id=novo.id, nome=novo.nome, nome_ong=novo.nome_ong, plano=novo.plano)


@app.post("/auth/login", response_model=TokenSchema, tags=["Autenticação"])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login com e-mail e senha. Valida bcrypt e retorna JWT."""
    usuario = db.query(Usuario).filter(Usuario.email == form.username.lower().strip()).first()

    if not usuario or not verificar_senha(form.password, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.", headers={"WWW-Authenticate": "Bearer"})

    if usuario.status == StatusEnum.inativo:
        raise HTTPException(status_code=403, detail="Conta inativa.")

    token = criar_token({"sub": usuario.email, "plano": usuario.plano})
    return TokenSchema(access_token=token, usuario_id=usuario.id, nome=usuario.nome, nome_ong=usuario.nome_ong, plano=usuario.plano)


@app.get("/auth/me", response_model=UsuarioPublico, tags=["Autenticação"])
def meu_perfil(usuario: Usuario = Depends(get_usuario_atual)):
    """Retorna os dados do usuário autenticado."""
    return usuario


# ============================================================
#  ROTAS – DOAÇÕES  (todos os planos)
# ============================================================

@app.get("/doacoes/", response_model=List[DoacaoOut], tags=["Doações"])
def listar_doacoes(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    return db.query(Doacao).filter(Doacao.usuario_id == usuario.id).all()


@app.post("/doacoes/", response_model=DoacaoOut, status_code=201, tags=["Doações"])
def criar_doacao(dados: DoacaoIn, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    nova = Doacao(usuario_id=usuario.id, doador=dados.doador.strip(), tipo=dados.tipo,
                  descricao=dados.descricao, valor=dados.valor, status=dados.status or "pendente")
    db.add(nova); db.commit(); db.refresh(nova)
    return nova


@app.patch("/doacoes/{doacao_id}/status", tags=["Doações"])
def atualizar_status_doacao(doacao_id: int, novo_status: str, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    doacao = db.query(Doacao).filter(Doacao.id == doacao_id, Doacao.usuario_id == usuario.id).first()
    if not doacao:
        raise HTTPException(status_code=404, detail="Doação não encontrada.")
    if novo_status not in {"pendente", "confirmada", "cancelada"}:
        raise HTTPException(status_code=400, detail="Status inválido. Use: pendente, confirmada ou cancelada.")
    doacao.status = novo_status
    db.commit()
    return {"mensagem": f"Status atualizado para '{novo_status}'."}


@app.delete("/doacoes/{doacao_id}", status_code=204, tags=["Doações"])
def deletar_doacao(doacao_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    doacao = db.query(Doacao).filter(Doacao.id == doacao_id, Doacao.usuario_id == usuario.id).first()
    if not doacao:
        raise HTTPException(status_code=404, detail="Doação não encontrada.")
    db.delete(doacao); db.commit()


# ============================================================
#  ROTAS – VOLUNTÁRIOS  (com limite por plano)
# ============================================================

@app.get("/voluntarios/", response_model=List[VoluntarioOut], tags=["Voluntários"])
def listar_voluntarios(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    return db.query(Voluntario).filter(Voluntario.usuario_id == usuario.id).all()


@app.post("/voluntarios/", response_model=VoluntarioOut, status_code=201, tags=["Voluntários"])
def criar_voluntario(dados: VoluntarioIn, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    checar_limite_voluntarios(usuario, db)
    novo = Voluntario(usuario_id=usuario.id, nome=dados.nome.strip(),
                      email=dados.email, telefone=dados.telefone, area=dados.area, ativo=True)
    db.add(novo); db.commit(); db.refresh(novo)
    return novo


@app.patch("/voluntarios/{vol_id}/desativar", tags=["Voluntários"])
def desativar_voluntario(vol_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    vol = db.query(Voluntario).filter(Voluntario.id == vol_id, Voluntario.usuario_id == usuario.id).first()
    if not vol:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado.")
    vol.ativo = False; db.commit()
    return {"mensagem": "Voluntário desativado."}


@app.delete("/voluntarios/{vol_id}", status_code=204, tags=["Voluntários"])
def deletar_voluntario(vol_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    vol = db.query(Voluntario).filter(Voluntario.id == vol_id, Voluntario.usuario_id == usuario.id).first()
    if not vol:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado.")
    db.delete(vol); db.commit()


# ============================================================
#  ROTAS – EVENTOS  (Plano Impacto e Transformação)
# ============================================================

@app.get("/eventos/", response_model=List[EventoOut], tags=["Eventos"])
def listar_eventos(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    checar_plano_eventos(usuario)
    return db.query(Evento).filter(Evento.usuario_id == usuario.id).order_by(Evento.data).all()


@app.post("/eventos/", response_model=EventoOut, status_code=201, tags=["Eventos"])
def criar_evento(dados: EventoIn, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    checar_plano_eventos(usuario)
    novo = Evento(usuario_id=usuario.id, nome=dados.nome.strip(), tipo=dados.tipo,
                  data=dados.data, local=dados.local, descricao=dados.descricao)
    db.add(novo); db.commit(); db.refresh(novo)
    return novo


@app.put("/eventos/{evento_id}", response_model=EventoOut, tags=["Eventos"])
def editar_evento(evento_id: int, dados: EventoIn, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    checar_plano_eventos(usuario)
    evento = db.query(Evento).filter(Evento.id == evento_id, Evento.usuario_id == usuario.id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    for field, value in dados.model_dump().items():
        setattr(evento, field, value)
    db.commit(); db.refresh(evento)
    return evento


@app.delete("/eventos/{evento_id}", status_code=204, tags=["Eventos"])
def deletar_evento(evento_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    checar_plano_eventos(usuario)
    evento = db.query(Evento).filter(Evento.id == evento_id, Evento.usuario_id == usuario.id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")
    db.delete(evento); db.commit()


# ============================================================
#  ROTAS – RELATÓRIOS  (Plano Impacto e Transformação)
# ============================================================

@app.get("/relatorios/visao-geral", tags=["Relatórios"])
def relatorio_visao_geral(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    """Resumo completo da ONG: doações, voluntários e eventos."""
    checar_plano_relatorio(usuario)
    uid = usuario.id

    total_doacoes       = db.query(Doacao).filter(Doacao.usuario_id == uid).count()
    doacoes_confirmadas = db.query(Doacao).filter(Doacao.usuario_id == uid, Doacao.status == "confirmada").count()
    voluntarios_ativos  = db.query(Voluntario).filter(Voluntario.usuario_id == uid, Voluntario.ativo == True).count()
    total_eventos       = db.query(Evento).filter(Evento.usuario_id == uid).count()

    financeiras = db.query(Doacao).filter(
        Doacao.usuario_id == uid, Doacao.tipo == "financeira", Doacao.status == "confirmada"
    ).all()
    valor_total = sum(float(d.valor) for d in financeiras if d.valor and d.valor.replace(".", "").isdigit())

    return {
        "ong":   usuario.nome_ong,
        "plano": usuario.plano,
        "doacoes": {
            "total": total_doacoes,
            "confirmadas": doacoes_confirmadas,
            "valor_arrecadado": round(valor_total, 2),
        },
        "voluntarios": {
            "ativos": voluntarios_ativos,
            "limite_plano": {
                "semente": 10, "impacto": 25, "transformacao": "ilimitado"
            }.get(usuario.plano, "?"),
        },
        "eventos": {"total": total_eventos},
    }


@app.get("/relatorios/doacoes-por-tipo", tags=["Relatórios"])
def relatorio_doacoes_tipo(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_atual)):
    """Agrupa doações por tipo (financeira / especie)."""
    checar_plano_relatorio(usuario)
    from sqlalchemy import func as sqlfunc
    resultado = (
        db.query(Doacao.tipo, sqlfunc.count(Doacao.id).label("quantidade"))
        .filter(Doacao.usuario_id == usuario.id)
        .group_by(Doacao.tipo).all()
    )
    return [{"tipo": r.tipo, "quantidade": r.quantidade} for r in resultado]