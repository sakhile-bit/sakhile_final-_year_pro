# Deploying to Render (Free Tier)

## Prerequisites
- GitHub account
- Render account (free) — sign up at https://render.com

---

## Step 1 — Push the latest code to GitHub

Open a terminal in the project root and run:

```powershell
git add .
git commit -m "Add Render deployment config"
git push origin main
```

---

## Step 2 — Create a Render account

1. Go to **https://render.com**
2. Click **Get Started for Free**
3. Sign up with your GitHub account (easiest — gives Render access to your repos)

---

## Step 3 — Deploy using render.yaml (Blueprint)

The project already has a `render.yaml` file that configures everything automatically.

1. From your Render dashboard click **New → Blueprint**
2. Connect your GitHub repo: **sakhile-bit/sakhile_final-_year_pro**
3. Render will detect `render.yaml` and show you a preview:
   - **Web Service:** `zambia-digital-hygiene`
   - **PostgreSQL Database:** `zdh-db` (free)
4. Click **Apply** — Render creates both and links them automatically

> The `SECRET_KEY` is generated automatically by Render. `DATABASE_URL` is
> injected from the free PostgreSQL database.

---

## Step 4 — Wait for the build

The first build takes 3–5 minutes. You can watch the logs live in the Render dashboard.

When you see:

```
==> Your service is live 🎉
```

Your app is running at:

```
https://zambia-digital-hygiene.onrender.com
```

---

## Step 5 — First login

The default admin account is created automatically on first startup:

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `Admin@12345!` |

> **Change this password immediately** after first login via Profile → Change Password.

---

## Environment variables (already set by render.yaml)

| Variable | Value | Set by |
|----------|-------|--------|
| `SECRET_KEY` | Auto-generated random string | Render |
| `DATABASE_URL` | PostgreSQL connection string | Render (from zdh-db) |
| `SESSION_COOKIE_SECURE` | `true` | render.yaml |
| `LOG_LEVEL` | `INFO` | render.yaml |
| `PYTHON_VERSION` | `3.11.0` | render.yaml |

If you need to add or change any variable, go to:
**Render Dashboard → zambia-digital-hygiene → Environment**

---

## Free tier limits

| Resource | Free limit |
|----------|-----------|
| Web service | Spins down after 15 min of inactivity (first request is slow ~30s) |
| PostgreSQL | 1 GB storage, expires after 90 days |
| Bandwidth | 100 GB/month |
| Build minutes | 500/month |

> To keep it from sleeping, use a free uptime monitor like **UptimeRobot** (https://uptimerobot.com) to ping `/health` every 5 minutes.

---

## Upgrading the database after 90 days

Render's free PostgreSQL expires after 90 days. Before it expires:

1. Go to **Dashboard → zdh-db → Backups** and download a backup
2. Create a new free database
3. Update the `DATABASE_URL` environment variable on the web service to point to the new database

---

## Redeploying after code changes

Every push to the `main` branch on GitHub automatically triggers a new deploy on Render (auto-deploy is enabled by default).

To deploy manually:
**Render Dashboard → zambia-digital-hygiene → Manual Deploy → Deploy latest commit**

---

## Checking logs

**Render Dashboard → zambia-digital-hygiene → Logs**

Or use the Render CLI:
```bash
render logs --service zambia-digital-hygiene --tail
```

---

## Custom domain (optional)

1. Go to **Dashboard → zambia-digital-hygiene → Settings → Custom Domains**
2. Add your domain (e.g. `app.yourdomain.zm`)
3. Add the CNAME record shown to your DNS provider
4. Render auto-provisions an SSL certificate via Let's Encrypt

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails — `psycopg2` error | Ensure `psycopg2-binary>=2.9.0` is in `requirements.txt` |
| `DATABASE_URL` not found | Check Environment tab — make sure `zdh-db` is linked |
| 500 error on first visit | Check Logs — usually a missing env var or DB not ready yet |
| Login fails | Confirm `SESSION_COOKIE_SECURE=true` is set and you are on HTTPS |
| App sleeps too often | Set up UptimeRobot to ping `/health` every 5 minutes |
