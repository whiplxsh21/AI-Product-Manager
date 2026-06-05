# Deploying PM Pilot (free, shareable link)

This hosts PM Pilot on **Streamlit Community Cloud** with a **Neon** Postgres
database (which also stores uploaded files) and optional **Resend** email for
password resets. All three are free. End result: a `https://<your-app>.streamlit.app`
link you can send to anyone.

## Architecture in hosted mode

| Concern | Hosted setup |
|---|---|
| App | Streamlit Community Cloud (auto-deploys from GitHub) |
| Database | Neon serverless Postgres (`DATABASE_URL`) |
| Uploaded files | Stored as rows in the same Postgres DB (`STORAGE_BACKEND=db`) |
| Login | Per-user accounts, bcrypt passwords (`AUTH_ENABLED=true`) |
| LLM keys | Each user sets their own in the in-app **Settings** page, encrypted at rest |
| Password reset | Email via Resend (or on-screen link if email not configured) |

Locally nothing changes: leave `AUTH_ENABLED=false` and `STORAGE_BACKEND=local`
and the app runs exactly as before.

---

## Step-by-step (≈20 min)

### 1. Put the code on GitHub
Push the **`ai-pm/` folder as the repository root** (so `app.py` and
`requirements.txt` sit at the top level — Streamlit Cloud expects this).

### 2. Create a Neon database
1. Sign up at https://neon.tech (free).
2. Create a project → open **Connection Details**.
3. Copy the connection string. Make sure it begins with `postgresql://`
   (change `postgres://` → `postgresql://` if needed) and keeps `?sslmode=require`.

### 3. (Optional) Create a Resend account for reset emails
1. Sign up at https://resend.com (free).
2. Create an API key. For a quick start you can send from `onboarding@resend.dev`;
   to send from your own domain, verify it in Resend first.
3. Skip this entirely and password-reset links will just be shown on screen.

### 4. Deploy on Streamlit Community Cloud
1. Sign in at https://share.streamlit.io with GitHub.
2. **New app** → pick your repo/branch → main file path `app.py`.
3. Open **Advanced settings → Secrets** and paste a filled-in copy of
   [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example):
   - `DATABASE_URL` — your Neon string
   - `STORAGE_BACKEND = "db"`
   - `AUTH_ENABLED = "true"`
   - `APP_SECRET_KEY` — generate with
     `python -c "import secrets;print(secrets.token_urlsafe(48))"`
   - `APP_BASE_URL` — your `https://<app>.streamlit.app` URL (set after first deploy)
   - `SEED_ADMIN_USERNAME` / `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` — your first login
   - `RESEND_API_KEY` / `EMAIL_FROM` — only if using email
4. **Deploy.** First boot creates the tables and seeds your admin account.

### 5. First login
- Open the app URL, sign in with the seeded admin credentials.
- Go to **Settings** → change your password, and add your LLM provider + API key
  (a free Groq key from https://console.groq.com works).
- Send the link to your boss. Create her a login (seed a second account via secrets,
  or share the admin until per-invite signup is added).

---

## Notes & limits

- **Persistence:** projects, documents, and outputs all live in Neon, so they
  survive app restarts/redeploys. Streamlit's own disk is ephemeral — that's fine
  because we store nothing important there.
- **Neon free tier:** ~0.5 GB. Uploads are small (transcripts KBs, decks a few MB),
  so that's plenty for a small team; prune old projects if it fills up.
- **Sleeping:** free apps sleep after inactivity and wake on the next visit
  (a few seconds). A pipeline run in progress won't survive a sleep — re-run if so.
- **API-key security:** keys are encrypted at rest with `APP_SECRET_KEY`. The app
  operator (whoever holds the secrets) can technically decrypt them — true
  zero-operator-access would need a managed KMS. Fine for an internal tool.
  If you rotate `APP_SECRET_KEY`, users must re-enter their keys.
