// ============================================================
// HUB SOCIAL – main.js
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

  // ---- Navbar scroll effect ----
  const navbar = document.getElementById('navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 40);
    });
  }

  // ---- Hamburger menu ----
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.getElementById('navLinks');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('open');
      navLinks.classList.toggle('open');
    });
    // Fecha ao clicar em um link
    navLinks.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        hamburger.classList.remove('open');
        navLinks.classList.remove('open');
      });
    });
  }

  // ---- Active nav link on scroll ----
  const sections = document.querySelectorAll('section[id]');
  const links = document.querySelectorAll('.nav-link');
  if (sections.length && links.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          links.forEach(l => l.classList.remove('active-link'));
          const active = document.querySelector(`.nav-link[href="#${entry.target.id}"]`);
          if (active) active.classList.add('active-link');
        }
      });
    }, { threshold: 0.45 });
    sections.forEach(s => observer.observe(s));
  }

  // ---- Scroll-reveal animations ----
  const reveal = document.querySelectorAll('.feat-card, .plan-card, .about-card');
  if (reveal.length) {
    const revealObs = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.style.opacity = '1';
            entry.target.style.transform = entry.target.classList.contains('plan-card') && entry.target.classList.contains('featured')
              ? 'scale(1.04)'
              : 'translateY(0)';
          }, i * 80);
          revealObs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    reveal.forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(24px)';
      el.style.transition = 'opacity .5s ease, transform .5s ease';
      revealObs.observe(el);
    });
  }

  // ---- Smooth plan card hover bars ----
  const bars = document.querySelectorAll('.db-bar');
  bars.forEach(bar => {
    bar.addEventListener('mouseenter', () => {
      bar.style.opacity = '.85';
    });
    bar.addEventListener('mouseleave', () => {
      bar.style.opacity = '1';
    });
  });

});

// ---- Active nav link style ----
const style = document.createElement('style');
style.textContent = `.nav-link.active-link { color: var(--white) !important; background: rgba(255,255,255,.12) !important; }`;
document.head.appendChild(style);

// api.js
// Conecta o front-end HTML com a API FastAPI (http://localhost:8000)
// Coloque este arquivo na mesma pasta do index.html

const API_URL = "http://localhost:8000";

// ── Helpers de token (localStorage) ─────────────────────────

function salvarToken(token, dados) {
  localStorage.setItem("hs_token",    token);
  localStorage.setItem("hs_nome",     dados.nome);
  localStorage.setItem("hs_nome_ong", dados.nome_ong);
  localStorage.setItem("hs_plano",    dados.plano);
  localStorage.setItem("hs_id",       dados.usuario_id);
}

function getToken()   { return localStorage.getItem("hs_token");    }
function getNome()    { return localStorage.getItem("hs_nome");     }
function getOng()     { return localStorage.getItem("hs_nome_ong"); }
function getPlano()   { return localStorage.getItem("hs_plano");    }
function estaLogado() { return !!getToken(); }

function logout() {
  localStorage.clear();
  window.location.href = "login.html";
}

// ── Request helper com JWT ───────────────────────────────────

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg = data.detail || `Erro ${res.status}`;
    throw new Error(Array.isArray(msg) ? msg.map(e => e.msg).join(", ") : msg);
  }
  return data;
}

// ── AUTH ─────────────────────────────────────────────────────

async function cadastrar(payload) {
  const data = await apiFetch("/auth/cadastro", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  salvarToken(data.access_token, data);
  return data;
}

async function login(email, senha) {
  // OAuth2PasswordRequestForm espera form-data, não JSON
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", senha);

  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Erro ao fazer login.");
  salvarToken(data.access_token, data);
  return data;
}

async function getMeuPerfil() {
  return apiFetch("/auth/me");
}

// ── DOAÇÕES ──────────────────────────────────────────────────

async function listarDoacoes()        { return apiFetch("/doacoes/"); }
async function criarDoacao(payload)   { return apiFetch("/doacoes/", { method: "POST", body: JSON.stringify(payload) }); }
async function deletarDoacao(id)      { return apiFetch(`/doacoes/${id}`, { method: "DELETE" }); }
async function atualizarStatusDoacao(id, status) {
  return apiFetch(`/doacoes/${id}/status?novo_status=${status}`, { method: "PATCH" });
}

// ── VOLUNTÁRIOS ──────────────────────────────────────────────

async function listarVoluntarios()       { return apiFetch("/voluntarios/"); }
async function criarVoluntario(payload)  { return apiFetch("/voluntarios/", { method: "POST", body: JSON.stringify(payload) }); }
async function deletarVoluntario(id)     { return apiFetch(`/voluntarios/${id}`, { method: "DELETE" }); }
async function desativarVoluntario(id)   { return apiFetch(`/voluntarios/${id}/desativar`, { method: "PATCH" }); }

// ── EVENTOS ──────────────────────────────────────────────────

async function listarEventos()          { return apiFetch("/eventos/"); }
async function criarEvento(payload)     { return apiFetch("/eventos/", { method: "POST", body: JSON.stringify(payload) }); }
async function editarEvento(id, dados)  { return apiFetch(`/eventos/${id}`, { method: "PUT",  body: JSON.stringify(dados) }); }
async function deletarEvento(id)        { return apiFetch(`/eventos/${id}`, { method: "DELETE" }); }

// ── RELATÓRIOS ───────────────────────────────────────────────

async function relatorioGeral()         { return apiFetch("/relatorios/visao-geral"); }
async function relatorioDoacoesTipo()   { return apiFetch("/relatorios/doacoes-por-tipo"); }

// ── Proteção de página: redireciona se não estiver logado ────

function exigirLogin() {
  if (!estaLogado()) {
    window.location.href = "login.html";
  }
}

// ── Preenche dados do usuário no dashboard ───────────────────

function preencherDashboard() {
  exigirLogin();
  const nome  = getNome()?.split(" ")[0] || "Usuário";
  const ong   = getOng()  || "Minha ONG";
  const plano = getPlano() || "semente";

  const elNome  = document.getElementById("dash-user-name");
  const elOng   = document.getElementById("sb-ong");
  const elTitulo= document.getElementById("dash-titulo");
  const elAvatar= document.getElementById("dash-avatar");
  const elPlano = document.getElementById("sb-plano");

  if (elNome)   elNome.textContent   = `Olá, ${nome}!`;
  if (elOng)    elOng.textContent    = ong;
  if (elTitulo) elTitulo.textContent = `Bem-vindo(a), ${nome} 👋`;
  if (elAvatar) elAvatar.textContent = nome[0].toUpperCase();
  if (elPlano)  elPlano.textContent  = `Plano ${plano.charAt(0).toUpperCase() + plano.slice(1)}`;
}