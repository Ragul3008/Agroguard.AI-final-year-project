# AgroGuard AI — Deployment Notes

## Render Backend Deployment

### Cold-Start Behavior (Free/Starter Tier)
**Important:** Render's free and starter tier web services **spin down after 15 minutes of inactivity**.

- **First request after spin-down**: Takes **30-60 seconds** to cold-start (container wake-up + model loading)
- **Subsequent requests**: Normal latency (~200-500ms for predictions)
- **This is expected behavior, NOT a bug**

### Mitigation Options
1. **Upgrade to Standard plan** ($25/mo) — always-on, no spin-down
2. **External cron ping** — Use a free cron service (cron-job.org, UptimeRobot) to hit `/health` every 10 minutes
3. **Frontend handling** — Show a "Waking up server..." message on first load (see `Chat.tsx` for implementation)

### Health Check Endpoint
- **Path**: `/health`
- **Response**: JSON with `status`, `version`, `model_loaded`, `database`
- **Used by**: Render health checks, external monitoring

### Environment Variables (Set in Render Dashboard)
| Variable | Required | Notes |
|----------|----------|-------|
| `DATABASE_URL` | ✅ | Auto-provided by Render PostgreSQL addon |
| `SECRET_KEY` | ✅ | Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `REFRESH_SECRET_KEY` | ✅ | Separate from SECRET_KEY |
| `GEMINI_API_KEY` | ✅ | Google AI Studio API key |
| `GEOAPIFY_API_KEY` | ✅ | Free tier: 3000 req/day |
| `GOOGLE_MAPS_API_KEY` | Optional | Backup geolocation |
| `GOOGLE_OAUTH_CLIENT_ID` | ✅ | Google Cloud Console OAuth credentials |
| `GOOGLE_OAUTH_CLIENT_SECRET` | ✅ | Keep secret! |
| `EMAIL_API_KEY` | ✅ | Resend/SendGrid/Postmark API key |
| `EMAIL_FROM_ADDRESS` | ✅ | Verified sender domain |
| `ALLOWED_ORIGINS` | ✅ | Comma-separated, supports `https://*.vercel.app` |
| `MODEL_PATH` | ✅ | Relative to working dir |
| `WHISPER_MODEL_SIZE` | ✅ | `medium` (1.5GB download on first run) |
| `DEBUG` | No | `false` for production |

### Model File
The `.pth` model file must be included in the repo or downloaded at build time.
- **Option A**: Commit to Git LFS (recommended for < 100MB)
- **Option B**: Download from S3/GCS in build script (for larger models)

### Build & Start Commands
```yaml
buildCommand: |
  pip install --upgrade pip
  pip install -r requirements.txt
startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Vercel Frontend Deployment

### Environment Variables (Set in Vercel Dashboard)
| Variable | Required | Notes |
|----------|----------|-------|
| `VITE_API_BASE_URL` | ✅ | Full backend URL + `/api/v1` (e.g., `https://agroguard-api.onrender.com/api/v1`) |
| `VITE_GOOGLE_OAUTH_CLIENT_ID` | ✅ | Same as backend |

### Build Configuration
- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

### Domains
- **Production**: `https://agroguard.vercel.app`
- **Preview Deployments**: `https://agroguard-<branch>-<hash>.vercel.app` (auto-allowed via `https://*.vercel.app` in CORS)

---

## Local Development

### Backend
```bash
cd backend
cp .env.example .env
# Edit .env with local values
# Start PostgreSQL locally or use Docker:
docker run -d --name postgres -e POSTGRES_PASSWORD=0308 -e POSTGRES_DB=agroguard_banana -p 5432:5432 postgres:16
# Run backend
source venv/bin/activate  # or python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
cp .env.example .env
# Edit .env with VITE_API_BASE_URL=http://localhost:8000/api/v1
npm install
npm run dev
```

### Google OAuth Local Testing
1. Add `http://localhost:5173` to authorized JavaScript origins in Google Cloud Console
2. Add `http://localhost:8000/api/v1/auth/google/callback` to authorized redirect URIs
3. Use same `GOOGLE_OAUTH_CLIENT_ID` in both frontend and backend `.env`

---

## Production Checklist

### Security
- [ ] All secrets in Render/Vercel dashboard (not in repo)
- [ ] `SECRET_KEY` and `REFRESH_SECRET_KEY` are unique, 32+ chars
- [ ] CORS `ALLOWED_ORIGINS` restricted to production domains only
- [ ] Google OAuth redirect URIs only include production URLs
- [ ] Email sender domain verified (SPF/DKIM/DMARC)
- [ ] Rate limits configured appropriately

### Database
- [ ] Render managed PostgreSQL provisioned
- [ ] Connection pooling via PgBouncer (configured in `DATABASE_URL`)
- [ ] Automated daily backups enabled
- [ ] Alembic migrations run on deploy (add to build command if needed)

### Monitoring
- [ ] `/health` endpoint returns `status: "ok"`
- [ ] External uptime monitoring (UptimeRobot, Better Uptime)
- [ ] Error tracking (Sentry DSN in env)
- [ ] Log aggregation (Render logs + optional Loki/Datadog)

### Performance
- [ ] Model file present and loading correctly
- [ ] Whisper model downloads on first request (expect 30-60s delay)
- [ ] Static assets served via Vercel CDN
- [ ] Image uploads compressed client-side before send

---

## Troubleshooting

### "Service Unavailable" on First Request
→ Render cold start. Wait 30-60s and retry. Check Render logs for "Starting service..." messages.

### CORS Errors
→ Verify `ALLOWED_ORIGINS` includes exact frontend URL (no trailing slash).
→ Check browser devtools Network tab for `Access-Control-Allow-Origin` header.

### Google OAuth "redirect_uri_mismatch"
→ Ensure redirect URI in Google Cloud Console matches exactly: `https://your-backend.onrender.com/api/v1/auth/google/callback`

### Database Connection Failed
→ Check `DATABASE_URL` format: `postgresql+asyncpg://user:pass@host:5432/db?sslmode=require`
→ Verify Render PostgreSQL is in same region as web service.

### Whisper Model Not Loading
→ First request triggers ~1.5GB download. Check logs for "Loading Whisper medium model...".
→ Ensure disk space available (Render starter: 10GB).

---

## Scaling Considerations

| Traffic Level | Backend Plan | Frontend | Notes |
|---------------|--------------|----------|-------|
| < 100 users/day | Starter (free) | Vercel Free | Cold starts acceptable |
| 100-1000 users/day | Standard ($25/mo) | Vercel Pro | Always-on, faster cold starts |
| 1000-10000 users/day | Standard + more instances | Vercel Pro | Horizontal scaling, add Redis cache |
| 10000+ users/day | Pro + dedicated DB | Vercel Enterprise | Read replicas, CDN, load testing |

---

## Support Contacts

- **Render**: https://render.com/docs/support
- **Vercel**: https://vercel.com/support
- **Google Cloud**: https://cloud.google.com/support
- **Resend (Email)**: https://resend.com/docs/support