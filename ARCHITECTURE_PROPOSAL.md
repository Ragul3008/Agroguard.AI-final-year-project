# AgroGuard AI — Proposed Production Architecture

**Version:** 2.0  
**Date:** 2026-08-17  
**Status:** Proposal — Awaiting Stakeholder Review

---

## 1. Architectural Principles

| Principle | Decision |
|-----------|----------|
| **Rural-first** | Optimize for 2G/3G, low-end devices, intermittent connectivity |
| **Cost-conscious** | Prefer managed services over self-hosted; avoid over-engineering |
| **Incremental migration** | No big-bang rewrite; each phase ships value independently |
| **Security by default** | Secrets in vault, least-privilege, defense in depth |
| **Observability first** | Structured logs, metrics, traces from Day 1 |
| **Model-data separation** | Decouple inference from API for independent scaling |

---

## 2. Target Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    EXTERNAL CLIENTS                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ Farmer PWA  │  │ Admin Dash  │  │ Mobile App  │  │ 3rd Party   │  (Future)       │
│  │ (React+SW)  │  │ (Next.js)   │  │ (React Nat.)│  │  Integrations│                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
└─────────┼────────────────┼────────────────┼────────────────┼─────────────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY / LOAD BALANCER                            │
│                    (Cloudflare / AWS ALB / Nginx / Traefik)                         │
│  • TLS termination  • WAF  • Rate limiting  • Request routing  • Caching           │
└────────────────────────────────────┬────────────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  API SERVICE     │      │  MODEL SERVICE   │      │  WORKER SERVICE  │
│  (FastAPI)       │      │  (TorchServe/    │      │  (Celery/Arq)    │
│  • Auth          │      │   Triton)        │      │  • Gemini LLM    │
│  • CRUD          │      │  • ConvNeXt      │      │  • Whisper STT   │
│  • Location      │      │  • Batch infer   │      │  • Image optim.  │
│  • Geo lookup    │      │  • GPU autoscale │      │  • Notifications │
│  • Rate limit    │      │  • Model version │      │  • Email/SMS     │
└────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  POSTGRESQL      │      │  REDIS CLUSTER   │      │  OBJECT STORAGE  │
│  (Primary +      │      │  • Session cache │      │  (S3/R2/MinIO)   │
│   Read Replica)  │      │  • Advisory cache│      │  • Model artifacts│
│  • PgBouncer     │      │  • Geo cache     │      │  • Upload images  │
│  • Alembic       │      │  • Rate limit    │      │  • Audio files    │
│  • Backups       │      │  • Celery broker │      │  • CDN origin     │
└──────────────────┘      └──────────────────┘      └──────────────────┘
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  OBSERVABILITY   │      │  SECRETS MGMT    │      │  CI/CD           │
│  • OpenTelemetry │      │  (AWS Secrets    │      │  (GitHub Actions)│
│  • Prometheus    │      │   Manager /      │      │  • Lint, type    │
│  • Grafana       │      │   Doppler /      │      │  • Test (unit,   │
│  • Sentry        │      │   Infisical)     │      │    integration)  │
│  • Structured    │      │  • Key rotation  │      │  • Security scan │
│    logging       │      │                  │      │  • Build + push  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## 3. Technology Choices & Justification

### 3.1 Model Serving: TorchServe (Recommended)

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **TorchServe** | Native PyTorch, batching, GPU/CPU, model versioning, metrics, K8s integration | Learning curve; Java-based | ✅ **Recommended** — Best fit for PyTorch models |
| Triton Inference Server | Multi-framework, high throughput, model repository | Overkill for single model; complex config | ❌ Too heavy |
| Dedicated FastAPI microservice | Simple, same stack | No batching, no native GPU scaling, reinventing wheel | ⚠️ Fallback only |
| **In-process (current)** | Simplest | Blocks event loop, no horizontal scale, memory pressure | ❌ Not production |

**TorchServe Configuration:**
```yaml
# config.properties
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
metrics_address=http://0.0.0.0:8082
model_store=/models
number_of_netty_threads=4
job_queue_size=100
default_workers_per_model=2
```

**Model Archive (`.mar`):**
```
agroguard_convnext.mar/
├── model.py           # Handler with preprocess/inference/postprocess
├── index_to_name.json # Class mapping
├── config.yaml        # Thresholds, input shape
└── saved_models/
    └── agroguard_banana_convnext_v3.pth
```

### 3.2 Async Task Processing: Celery + Redis (Recommended)

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Celery + Redis** | Mature, battle-tested, monitoring (Flower), retry/backoff, priority queues | Extra component; Redis memory | ✅ **Recommended** |
| Arq (asyncio-native) | Lightweight, native async, no separate worker process | Less ecosystem; no Flower equivalent | ⚠️ Good alternative |
| FastAPI BackgroundTasks | Zero deps | No persistence, no retry, no scaling | ❌ Not for production |
| Dramatiq | Simple, Redis/RabbitMQ | Less monitoring | ⚠️ Alternative |

**Queue Design:**
```
celery queues:
├── high-priority   → auth, predict (sync path)
├── llm-advisory    → Gemini calls (rate limited, 10/min)
├── speech-stt      → Whisper transcription (heavy, 1-2 concurrent)
├── image-opt       → Compression, thumbnails, CDN upload
├── notifications   → Email, SMS, push
└── low-priority    → Analytics, cleanup, reports
```

### 3.3 Caching: Redis Cluster

| Cache Layer | TTL | Invalidation | Size Est. |
|-------------|-----|--------------|-----------|
| **Advisory cache** | 24h | On model version change | ~500 KB (7 diseases × 4 severities × 23 langs) |
| **Geo lookup cache** | 7d | Manual / API key rotation | ~2 MB (district-level centers) |
| **Session/Auth tokens** | 30d | On logout/password change | ~1 KB per active farmer |
| **Rate limit counters** | 1m/1h | Auto-expiry | Negligible |
| **Model metadata** | 1h | On model reload | Negligible |

### 3.4 Database: PostgreSQL + PgBouncer + Read Replica

| Component | Configuration |
|-----------|---------------|
| **Primary** | `db.t3.medium` (2 vCPU, 4 GB) — write path |
| **Read Replica** | `db.t3.small` — stats, history, analytics queries |
| **PgBouncer** | Transaction pooling, `pool_mode=transaction`, `max_client_conn=500`, `default_pool_size=25` |
| **Migrations** | Alembic (required before Phase 2) |
| **Backups** | Daily snapshots + WAL archiving (RPO < 1h, RTO < 4h) |
| **Indexes** | Add on `predictions(farmer_id, created_at)`, `predictions(disease)`, `farmers(phone)` |

### 3.5 API Gateway / Observability

| Tool | Purpose | Cost (Est. Monthly) |
|------|---------|---------------------|
| **Cloudflare** (Free tier) | TLS, WAF, DDoS, CDN, rate limiting at edge | $0 |
| **OpenTelemetry SDK** | Auto-instrumentation (FastAPI, SQLAlchemy, Redis, httpx) | Free (self-hosted) |
| **Prometheus + Grafana** | Metrics, dashboards, alerting | $0 (self-hosted on t3.small) |
| **Sentry** (Free tier) | Error tracking, performance monitoring | $0 (5k events/mo) |
| **Structured Logging** | JSON logs → Loki/CloudWatch | $0-10 |

**Key Metrics to Track:**
- `http_requests_total` by endpoint, status, latency (p50/p95/p99)
- `model_inference_duration_seconds` (TorchServe)
- `celery_task_duration_seconds` by queue
- `db_query_duration_seconds`
- `cache_hit_ratio`
- `active_farmers` (daily/weekly/monthly)
- `prediction_accuracy` (feedback loop — future)

### 3.6 Containerization & Orchestration

**Recommendation: Docker Compose (local) → AWS ECS Fargate (production)**

| Environment | Orchestration | Rationale |
|-------------|---------------|-----------|
| **Local Dev** | Docker Compose | Zero cost, mirrors prod topology |
| **Staging** | ECS Fargate (1 task each) | Serverless containers, pay-per-use |
| **Production** | ECS Fargate + ALB | Auto-scaling, no EC2 management, integrates with AWS secrets |

**Alternative (simpler): Fly.io / Render / Railway**
- If team has no AWS experience, **Fly.io** is excellent: global Anycast, native Postgres/Redis, secrets, auto-scaling, Docker-native, generous free tier.

**Service Definitions (ECS/Fly):**
```
Services (each independently scalable):
├── api-gateway     (nginx/traefik)      → 1-3 tasks
├── api-service     (FastAPI)            → 2-10 tasks (CPU)
├── model-service   (TorchServe)         → 1-4 tasks (GPU optional)
├── worker-service  (Celery)             → 1-8 tasks per queue
├── frontend        (Nginx + static)     → 2-5 tasks
└── cron            (Alembic, backups)   → Scheduled tasks
```

### 3.7 CI/CD: GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  lint-type-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Backend lint (ruff)
      - name: Backend type-check (mypy)
      - name: Backend test (pytest + coverage)
      - name: Frontend lint (eslint)
      - name: Frontend type-check (tsc)
      - name: Frontend test (vitest)
      - name: Frontend build (vite)
      - name: Security scan (trivy/snyk)
      - name: Dependency audit (pip-audit, npm audit)
  build-push:
    needs: lint-type-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - Build multi-arch Docker images
      - Push to GHCR/ECR
      - Sign images (cosign)
  deploy-staging:
    needs: build-push
    runs-on: ubuntu-latest
    steps:
      - Deploy to ECS staging (blue/green)
      - Run smoke tests
  deploy-prod:
    needs: deploy-staging
    environment: production
    runs-on: ubuntu-latest
    steps:
      - Manual approval gate
      - Deploy to ECS production (rolling)
      - Health checks
      - Notify team
```

### 3.8 Testing Strategy

| Layer | Tool | Target Coverage | Critical Paths |
|-------|------|-----------------|----------------|
| **Unit (Backend)** | pytest + httpx + pytest-asyncio | 80% | Auth, guardrails, advisory logic, location parsing |
| **Integration (Backend)** | pytest + testcontainers (Postgres, Redis) | 60% | Full `/predict` flow, `/auth/*`, `/speech/*` |
| **Contract** | pact / schemathesis | 100% | OpenAPI spec validation |
| **E2E (Frontend)** | Playwright | 50% | Login → Upload → Result → TTS → Map |
| **Visual Regression** | Playwright + pixelmatch | Key pages | Chat, Analysis card, Map modal |
| **Load Test** | k6 / Locust | N/A | 100 concurrent farmers, 10 RPS predict |

### 3.9 Security Hardening

| Measure | Implementation |
|---------|----------------|
| **Secrets** | AWS Secrets Manager / Doppler / Infisical — **never in `.env` or code** |
| **JWT** | Access token 15 min + Refresh token 30 days (rotating, stored in httpOnly cookie) |
| **Rate Limiting** | Per-user (authenticated) + per-IP (anonymous); Redis-backed; tiered limits |
| **Image Upload** | MIME + magic bytes validation; ClamAV scan (async); resize/compress before processing |
| **CORS** | `allow_origins=["https://agroguard.ai", "https://staging.agroguard.ai"]` |
| **Security Headers** | `CSP`, `HSTS`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin` |
| **Dependency Scanning** | `pip-audit`, `npm audit`, `trivy fs .` in CI; fail on HIGH/CRITICAL |
| **SSRF Protection** | Allowlist for outbound HTTP (Gemini, Geoapify, Google Maps only) |
| **Audit Logging** | Structured logs for auth events, prediction requests, admin actions |

### 3.10 Frontend: Vite SPA → PWA + Optional Next.js for Public Pages

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Stay Vite SPA + PWA** | Zero rewrite, Service Worker for offline, smaller bundle, full control | No SSR for SEO | ✅ **Recommended** — PWA critical for rural users |
| **Migrate to Next.js** | SSR/SSG for landing/about, better SEO, image optimization | Major rewrite, heavier client bundle, more complex deployment | ❌ Not worth it for this use case |
| **Hybrid** | Next.js for public pages, Vite SPA for app | Complex routing, two build systems | ⚠️ Over-engineering |

**PWA Requirements (Non-negotiable for rural users):**
- `manifest.json` — installable, offline-first
- Service Worker (Workbox) — cache shell + API responses (stale-while-revalidate)
- Background Sync — queue predictions when offline, submit when online
- Image compression **before upload** (client-side canvas resize to 1024px max, JPEG 0.8)
- **Bundle budget**: < 300 KB gzipped initial JS (code-split heavy components)

**CDN Strategy for Uploads:**
- Direct-to-S3 presigned PUT (bypasses API, reduces latency)
- CloudFront / Cloudflare Images for automatic WebP/AVIF, resizing
- Thumbnail generation in worker queue

### 3.11 Cost/Infra Tradeoffs (Rural-First)

| Decision | Cost Impact | Rural UX Impact |
|----------|-------------|-----------------|
| **TorchServe on CPU (t3.medium)** | ~$30/mo vs GPU $200+/mo | Acceptable latency (~300ms) |
| **Whisper in worker (not API)** | Same infra | API stays fast; STT async |
| **Gemini caching (24h)** | Reduces API calls 80%+ | Faster advisory, lower cost |
| **Geoapify caching (7d)** | Eliminates 95% API calls | Instant map, free tier safe |
| **PWA + SW** | Dev effort only | **Critical** — works offline, low data |
| **Client-side image compress** | Dev effort only | **Critical** — 10MB → 500KB upload |
| **Read replica (db.t3.small)** | ~$15/mo | Faster history/stats, HA |
| **Sentry free tier** | $0 | Error visibility |
| **Cloudflare free tier** | $0 | TLS, WAF, CDN, edge rate limit |

**Estimated Monthly Production Cost (AWS, us-east-1):**
```
ECS Fargate (API: 2 tasks × 0.5 vCPU × 1 GB)     $15
ECS Fargate (Model: 1 task × 1 vCPU × 2 GB)      $25  (CPU only)
ECS Fargate (Worker: 2 tasks × 0.5 vCPU × 1 GB)  $15
ECS Fargate (Frontend: 2 tasks)                   $10
RDS PostgreSQL (Primary + Replica, db.t3.medium)  $60
ElastiCache Redis (cache.t3.micro)                $15
S3 + CloudFront (storage + transfer)              $10
Cloudflare / Monitoring / Secrets                 $0-10
────────────────────────────────────────────────────
**Total: ~$150/month** (scales to ~$400 at 10x traffic)
```

---

## 4. API Versioning Strategy

| Version | Status | Breaking Changes |
|---------|--------|------------------|
| `/api/v1/` | Current (stable) | — |
| `/api/v2/` | Planned (Phase 3) | • JWT in httpOnly cookie (not header)<br>• Refresh token rotation<br>• Standardized error envelope<br>• Pagination on all list endpoints<br>• WebSocket for real-time prediction updates |

**Migration Rule:** `/api/v1/` supported for 12 months after `/api/v2/` GA. Deprecation headers on v1 responses.

---

## 5. Data Migration Strategy

| Data | Strategy |
|------|----------|
| **Farmers** | No migration — same schema, add `refresh_token_hash` column (Phase 2) |
| **Predictions** | No migration — add `model_version`, `inference_latency_ms` columns (Phase 2) |
| **Model Artifacts** | Versioned in S3: `s3://agroguard-models/v3.0.0/agroguard_banana_convnext_v3.pth` |
| **Advisory Cache** | Flush on model version change (automated via CI) |

---

## 6. Rollback Strategy Per Component

| Component | Rollback Mechanism | RTO |
|-----------|-------------------|-----|
| **API Service** | ECS rolling deploy (previous task definition) | < 2 min |
| **Model Service** | TorchServe model versioning (`/models/{name}/versions/{ver}`) | < 30 sec |
| **Worker Service** | ECS rolling deploy; drain queues first | < 5 min |
| **Frontend** | CloudFront cache invalidation + previous build | < 1 min |
| **Database** | Alembic `downgrade` (tested in staging) | < 10 min |
| **Secrets** | Previous version in Secrets Manager | < 1 min |

---

## 7. Open Questions for Stakeholder Alignment

Before finalizing, I need your input on:

1. **Cloud Provider Preference**: AWS (ECS/Fargate) vs Fly.io vs Render vs Railway vs self-hosted K8s?
2. **Expected Scale**: Farmers/day (100? 1,000? 10,000? 100,000?) — affects instance sizing
3. **Budget Ceiling**: Monthly infra budget? (Current est. ~$150/mo)
4. **GPU Requirement**: Is CPU inference latency (~300ms) acceptable, or is GPU mandatory?
5. **Domain/SSL**: Do you own `agroguard.ai` or similar? Cloudflare setup needs domain.
6. **Team AWS Experience**: If low, Fly.io/Render strongly recommended over ECS.
7. **Data Residency**: Must data stay in India? (AWS Mumbai / Fly.io Mumbai region)
8. **Monitoring Preference**: Self-hosted Prometheus/Grafana vs managed (Datadog, Grafana Cloud)?
9. **CI/CD Secrets**: Where to store Docker registry creds, AWS keys? (GitHub Environments + OIDC)
10. **Offline/PWA Priority**: Confirm PWA + background sync is non-negotiable for Phase 1.

---

## 8. Appendix: Current → Target Mapping

| Current | Target | Phase |
|---------|--------|-------|
| Single FastAPI (sync inference) | API Service + TorchServe + Celery Workers | 2 |
| `.env` secrets | AWS Secrets Manager / Doppler | 1 |
| No tests | pytest (unit+int) + Playwright (E2E) | 1-2 |
| No CI/CD | GitHub Actions (lint, test, build, scan, deploy) | 1 |
| NullPool DB | PgBouncer + Read Replica + Alembic | 2 |
| No caching | Redis (advisory, geo, sessions, rate limit) | 2 |
| Basic logging | OpenTelemetry + Prometheus + Grafana + Sentry | 2 |
| Single Dockerfile | Multi-stage (api, model, worker, frontend) | 1 |
| CORS `*` | Restricted origins + CSP/HSTS headers | 1 |
| 30-day JWT only | Access (15m) + Refresh (30d, rotating, httpOnly) | 2 |
| Sync Geoapify/ Gemini | Cached + async (worker) | 2 |
| Vite SPA | Vite SPA + PWA (SW, background sync, image compress) | 1 |
| No image optimization | Client compress + direct-to-S3 + CDN | 2 |
| No Alembic | Alembic migrations | 2 |
| No load balancing | Cloudflare / ALB | 1 |