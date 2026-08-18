# AgroGuard AI — Production Audit Report

**Date:** 2026-08-17  
**Auditor:** Senior Full-Stack Architect & DevOps Engineer  
**Project:** B.E. CSE (AI & ML) Capstone — Annamalai University

---

## 1. Architecture & Dependency Graph

### 1.1 Backend Architecture (FastAPI Monolith)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Application (app/main.py)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ /api/v1/auth │  │ /api/v1/     │  │ /api/v1/     │  │ /health      │    │
│  │ • register   │  │ predict      │  │ speech/      │  │ (unversioned)│    │
│  │ • login      │  │ • POST       │  │ • transcribe │  └──────────────┘    │
│  │ • /me        │  │   predict    │  │ • process    │                     │
│  └──────────────┘  │   history    │  └──────────────┘                     │
│                     │   stats      │                                      │
│                     └──────────────┘                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  Services     │          │  ML Models    │          │  External     │
│  • Prediction │◄────────►│  • ConvNeXt   │          │  • Gemini 2.5 │
│  • Advisory   │          │    Small      │          │    Flash      │
│  • Location   │          │  • Whisper    │          │  • Geoapify   │
│  • Speech     │          │    medium     │          │    Places API │
│  • Auth       │          │  • Severity   │          │  • Google     │
│  • Guardrail  │          │    Estimator  │          │    Maps (bkp) │
└───────────────┘          └───────────────┘          └───────────────┘
        │
        ▼
┌───────────────┐          ┌───────────────┐
│  Database     │          │  Utilities    │
│  • PostgreSQL │          │  • Rate Limit │
│  • SQLAlchemy │          │  • Logger     │
│  • Async      │          │  • Image      │
│    (asyncpg)  │          │    Preprocess │
└───────────────┘          └───────────────┘
```

### 1.2 Key Dependencies (Backend)

| Category | Packages | Version |
|----------|----------|---------|
| Web Framework | fastapi, uvicorn, starlette | 0.115.0, 0.30.6 |
| Database | sqlalchemy, asyncpg, psycopg2-binary | 2.0.35, 0.29.0 |
| ML/Inference | torch, torchvision, openai-whisper, opencv-python-headless | 2.3.1, 0.18.1 |
| Auth | python-jose[cryptography], passlib[bcrypt], bcrypt | 4.0.1 |
| LLM | google-genai | latest |
| HTTP | httpx | latest |
| Rate Limiting | slowapi | latest |
| Config | pydantic, pydantic-settings, python-dotenv | 2.9.1, 2.5.2 |
| Utils | pillow, numpy<2 | 10.4.0, 1.26.4 |

### 1.3 Frontend Architecture (React 18 + Vite SPA)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            React 18 SPA (Vite 6)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Login/Register│  │ Chat (Main)  │  │ History      │  │ About/Dev    │    │
│  │ (Root)        │  │ • Image up   │  │ (localStorage)│  └──────────────┘    │
│  └──────────────┘  │ • Whisper STT│  └──────────────┘                     │
│                     │ • Browser STT│                                      │
│                     │ • TTS (both) │                                      │
│                     │ • Language   │                                      │
│                     │ • Nearby Ctrs│                                      │
│                     └──────────────┘                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────┐   ┌──────────────┐ ┌────────────┐
            │ API Layer│   │ UI Components│ │ State Mgmt │
            │ (api.ts) │   │ (Radix UI +  │ │ (useState, │
            │          │   │  Tailwind v4)│ │  useRef)   │
            └──────────┘   └──────────────┘ └────────────┘
```

---

## 2. Security Vulnerabilities

### 2.1 Critical Issues

| # | Vulnerability | Location | Severity | Impact |
|---|---------------|----------|----------|--------|
| 1 | **Hardcoded default SECRET_KEY** | `config.py:28` | 🔴 Critical | JWT tokens can be forged; full account takeover |
| 2 | **Plain `.env` with secrets** | `backend/.env` | 🔴 Critical | API keys, DB password committed to git (check .gitignore) |
| 3 | **CORS `allow_origins=["*"]`** | `config.py:39` | 🔴 Critical | CSRF, data exfiltration from any origin |
| 4 | **No refresh token rotation** | `auth_service.py` | 🟠 High | Long-lived access tokens (30 days) cannot be revoked |
| 5 | **SSRF risk in LLM/image pipeline** | `advisory_service.py`, `location_service.py` | 🟠 High | External API calls without URL validation/allowlist |
| 6 | **No input sanitization on advisory text** | `advisory_service.py:1070-1148` | 🟡 Medium | Prompt injection via `message` parameter in chat |

### 2.2 High/Medium Issues

| # | Vulnerability | Location | Severity |
|---|---------------|----------|----------|
| 7 | Rate limiting by IP only (no user-based) | `rate_limiter.py` | 🟠 High |
| 8 | No password complexity requirements | `auth.py:27-30` | 🟡 Medium |
| 9 | No account lockout after failed logins | `auth_service.py:144-180` | 🟡 Medium |
| 10 | JWT `exp` only, no `nbf`/`jti` for revocation | `auth_service.py:48-69` | 🟡 Medium |
| 11 | Model file loaded from local path without integrity check | `model_loader.py:67-80` | 🟡 Medium |
| 12 | Audio file upload lacks MIME validation | `speech.py:71-85` | 🟡 Medium |
| 13 | No security headers (CSP, HSTS, X-Frame-Options) | `main.py` | 🟡 Medium |
| 14 | Dependency vulnerabilities (scan needed) | `requirements.txt` | 🟡 Medium |

### 2.3 .gitignore Check Required

The `.env` file exists at `backend/.env` (398 bytes). **Verify it's in `.gitignore`** — if committed, rotate all secrets immediately.

---

## 3. Performance Bottlenecks

### 3.1 Synchronous Blocking in Async Context

| Location | Issue | Impact |
|----------|-------|--------|
| `prediction_service.py:72` | `self._classifier.predict(tensor)` — **blocking PyTorch inference** in async function | Blocks event loop; ~200-500ms per request; prevents horizontal scaling |
| `advisory_service.py:1079-1084` | `model.models.generate_content()` — **blocking Gemini API call** | 2-10s latency; blocks event loop; no timeout configured |
| `speech_service.py:236-242` | `model.transcribe()` — **blocking Whisper inference** (1.5GB model) | 5-30s per audio file; completely blocks worker |
| `location_service.py:214-217` | `httpx.Client()` — **sync HTTP client** in async service | Blocks event loop during Geoapify API calls |
| `guardrail_service.py:103-166` | OpenCV/CV2 operations — **CPU-intensive sync processing** | 50-200ms per image; blocks event loop |

### 3.2 Database Issues

| Issue | Location | Impact |
|-------|----------|--------|
| **NullPool** (no connection pooling) | `db.py:25` | New connection per request; high latency under load |
| **No read replicas** | Architecture | All reads/writes to single PG instance |
| **N+1 potential in history** | `routes.py:217-230` | Loads all predictions without pagination |
| **No Alembic migrations** | Missing | Schema changes require manual SQL |

### 3.3 Frontend Bundle Size

| Chunk | Size (est.) | Concern |
|-------|-------------|---------|
| `vendor-mui` | ~400 KB | MUI + Emotion heavy; only few components used |
| `vendor-radix` | ~200 KB | Many Radix components imported but not all used |
| `vendor-charts` | ~150 KB | Recharts for simple charts? |
| **Total JS** | **~1.2 MB+ gzipped** | Heavy for rural 2G/3G networks |

### 3.4 Model Serving

- **Single-process inference**: Model loaded in FastAPI worker memory
- **No batching**: Each request processes individually
- **No GPU utilization detection/logging**: `model_loader.py:37` detects CUDA but no metrics
- **No model versioning**: `model_version` hardcoded in response

---

## 4. Code Quality Issues

### 4.1 Typing Gaps

| File | Issue |
|------|-------|
| `prediction_service.py:36-45` | `Optional[float]` for lat/lng but treated as required in some paths |
| `advisory_service.py:980-1148` | `generate_chat_response` returns `str` but can return error strings — no `Result` type |
| `speech_service.py:192-274` | `transcribe_audio` raises `RuntimeError` and `ValueError` — not in signature |
| `location_service.py:190-231` | `_call_places_api` returns `list[dict]` but dict structure undocumented |

### 4.2 Error Handling

| Issue | Example |
|-------|---------|
| Broad `except Exception` | `routes.py:135-137`, `speech.py:102-104` |
| Inconsistent error responses | Some return `detail`, others custom envelopes |
| No structured logging context | `logger.info` with raw strings, no structured fields |
| Whisper temp file cleanup | `speech_service.py:280-283` — `finally` block but race condition possible |

### 4.3 Test Coverage

- **Current: ~0%** — No `tests/` directory, no `pytest` configuration
- **Critical paths untested**: `/predict`, `/auth/*`, `/speech/*`, advisory generation, guardrails

### 4.4 Code Duplication

- Three `/nearby-centres` aliases in `routes.py:143-199` — same logic, different URL patterns
- Language resolution duplicated in `routes.py:43-49` and `advisory_service.py:104-128`

---

## 5. Scalability Ceilings

| Component | Current Limit | Bottleneck |
|-----------|---------------|------------|
| **API Workers** | 1 (Dockerfile: `--workers 1`) | Single process; no horizontal scaling |
| **Model Inference** | ~2-5 req/s (CPU) | Blocking PyTorch in event loop |
| **Whisper Transcription** | 1 concurrent (singleton model) | 1.5GB model in memory; no queue |
| **Gemini Advisory** | Rate limited by Google (RPM) | No caching; every request calls API |
| **Database** | ~100 conn (NullPool) | New connection per request |
| **Geoapify API** | 3000/day free tier | No caching; every lookup calls API |
| **Frontend** | Static SPA | No SSR, no CDN, no service worker |

### Projected Traffic (Estimates)
- **Target**: 1,000-10,000 farmers/day (rural India)
- **Peak**: ~50-200 concurrent during morning/evening
- **Image uploads**: ~2-5 MB each; 10/min rate limit = 14,400/day theoretical max

---

## 6. Missing Production Infrastructure

| Component | Status | Required for Production |
|-----------|--------|------------------------|
| Containerization | ❌ Single Dockerfile (no multi-stage) | Multi-stage backend/frontend/model-server |
| CI/CD | ❌ None | GitHub Actions: lint, test, build, scan, deploy |
| Observability | ❌ Basic logging only | OpenTelemetry, Prometheus, Grafana, Sentry |
| Secrets Management | ❌ Plain `.env` | Vault/Secrets Manager/Doppler/Infisical |
| Caching | ❌ None | Redis for advisory, geo, sessions, rate limits |
| Background Jobs | ❌ All sync | Celery/Arq + Redis for Gemini, Whisper, email |
| Model Serving | ❌ In-process | TorchServe/Triton/separate microservice |
| Database Migrations | ❌ `create_all()` only | Alembic |
| Load Balancing | ❌ None | Nginx/Traefik/Cloud LB |
| CDN/Image Optimization | ❌ None | CloudFront/Cloudflare for uploads |
| Backup/DR | ❌ None | PG backup, model artifact versioning |
| API Versioning Strategy | ⚠️ `/api/v1/` only | `/api/v2/` plan for breaking changes |

---

## 7. Frontend-Specific Issues

| Issue | Impact |
|-------|--------|
| **No PWA/Service Worker** | Offline support critical for rural low-bandwidth users |
| **No image compression before upload** | 10MB raw uploads on 2G = 30-60s upload time |
| **Bundle not optimized for low-end devices** | 1.2MB+ JS; many farmers use budget Android phones |
| **Hardcoded `BASE_URL = localhost:8000`** | `api.ts:1` — not configurable for staging/prod |
| **No error boundary** | Crash = white screen; no fallback UI |
| **LocalStorage for history** | Limited to 5MB; no sync across devices |
| **No i18n framework** | Language strings scattered; hard to maintain |
| **Web Speech API fallback only** | Whisper endpoint not wired for synthesis (`/speech/synthesize` missing) |

---

## 8. Dependency Vulnerability Scan (Preliminary)

Run `pip-audit` / `snyk test` / `trivy fs .` on `requirements.txt` and `package-lock.json`. Known concerns:

- `torch==2.3.1` — check for CVE-2024-xxxx in PyTorch
- `opencv-python-headless==4.9.0.80` — older version
- `python-jose` — ensure cryptography backend is used
- `slowapi` — check for rate limit bypass CVEs
- Frontend: `vite@6.3.5`, `react@18.3.1` — check for supply chain issues

---

## 9. Summary: Production Readiness Score

| Category | Score | Notes |
|----------|-------|-------|
| **Security** | 3/10 | Critical secrets, CORS, auth gaps |
| **Performance** | 4/10 | Sync blocking, no caching, no pooling |
| **Reliability** | 3/10 | No tests, no health checks beyond `/health`, no circuit breakers |
| **Scalability** | 2/10 | Single process, no queue, no horizontal scale |
| **Observability** | 2/10 | Basic logging only |
| **Deployability** | 4/10 | Dockerfile exists but not multi-stage; no CI/CD |
| **Maintainability** | 5/10 | Good structure but typing gaps, duplication |

**Overall: 3.3/10** — **Not production-ready** without significant upgrades.

---

## 10. Immediate Action Items (Before Any Deployment)

1. **Rotate all secrets** — `.env` may be in git history
2. **Fix CORS** — Restrict to known frontend origins
3. **Add connection pooling** — PgBouncer or SQLAlchemy pool
4. **Move blocking ops to thread pool** — `run_in_executor` for PyTorch, Whisper, OpenCV
5. **Add Alembic** — Schema migration tooling
6. **Write critical path tests** — Auth, predict, advisory
7. **Configure timeouts** — HTTP clients, Gemini, Whisper
8. **Add security headers** — CSP, HSTS, X-Frame-Options
9. **Make BASE_URL configurable** — Environment variable in frontend
10. **Add PWA manifest + service worker** — Offline support for rural users