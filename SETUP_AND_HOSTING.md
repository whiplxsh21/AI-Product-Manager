# PM Pilot — Setup & Hosting Guide

This guide walks you through running PM Pilot on your own machine and hosting it
for your team. It assumes **no prior experience** — every step is spelled out.
You'll get the app running locally first, then (optionally) deploy it as a shared,
login-protected app on the free **Streamlit Community Cloud**.

> **Important:** Right now the app may contain the original author's personal API
> keys and accounts. Before your team uses it, replace **every** key and secret
> with your own — this guide tells you exactly which ones and where. Nothing in
> the original author's accounts should remain.

**Contents**
1. [What you need](#1-what-you-need)
2. [Get your API keys](#2-get-your-api-keys)
3. [Run it locally](#3-run-it-locally)
4. [Host it on Streamlit Cloud](#4-host-it-on-streamlit-cloud)
5. [Set up the hosted database (Neon)](#5-set-up-the-hosted-database-neon)
6. [Turn on logins & accounts](#6-turn-on-logins--accounts)
7. [Optional: password-reset emails](#7-optional-password-reset-emails)
8. [Optional: live Jira push](#8-optional-live-jira-push)
9. [All settings reference](#9-all-settings-reference)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. What you need

- **A computer** with Python **3.11 or newer** installed.
  - Check by opening a terminal and running `python --version` (or `python3 --version`).
  - If you don't have it, download from [python.org](https://www.python.org/downloads/).
- **A free Groq API key** (this is the only thing required to run v1). Step 2 covers it.
- For hosting: a free **GitHub** account and a free **Streamlit Community Cloud** account.

Everything else (paid LLMs, a hosted database, email, Jira) is optional and only
needed for specific features.

---

## 2. Get your API keys

You only need the **first one** to get started. Get the rest when you want those
features.

### Groq (required — free)
1. Go to [console.groq.com](https://console.groq.com) and sign up.
2. Open **API Keys** → **Create API Key**.
3. Copy the key (starts with `gsk_...`). Keep it somewhere safe.

### OpenAI (optional — for "Pro" mode / paid generation)
1. Go to [platform.openai.com](https://platform.openai.com), sign up, add billing.
2. **API keys** → **Create new secret key**. Copy it (starts with `sk-...`).

### Anthropic / Google Gemini (optional — alternative providers)
- Anthropic: [console.anthropic.com](https://console.anthropic.com) → API keys.
- Gemini: [aistudio.google.com](https://aistudio.google.com) → Get API key.

You don't need all of these. Groq alone runs the whole app for free.

---

## 3. Run it locally

This gets the app running on your own computer in single-user mode (no login).

1. **Open a terminal** and go into the app folder:
   ```bash
   cd ai-pm
   ```

2. **Create your settings file** by copying the example:
   ```bash
   cp .env.example .env
   ```

3. **Add your Groq key.** Open the new `.env` file in any text editor and set:
   ```bash
   GROQ_API_KEY=gsk_your_key_here
   ```
   Save and close. (Leave everything else at its default for now.)

4. **Install the dependencies** (one time):
   ```bash
   pip install -r requirements.txt
   ```
   > If `pip` isn't found, try `pip3`. This downloads everything the app needs and
   > can take a few minutes.

5. **Start the app:**
   ```bash
   streamlit run app.py
   ```
   Your browser opens at **http://localhost:8501**. That's PM Pilot running.

6. **Try it:** create a project, upload a transcript (`.txt`) or PDF from the
   `TESTING DATA` folder, fill in the requirement details, and click **Run**.
   Watch the stages complete, then open the Results tab.

That's the full app, running for free, with no database or login setup.

---

## 4. Host it on Streamlit Cloud

To let your team use it from a browser, deploy it to **Streamlit Community Cloud**
(free). This publishes the app at a URL like `https://your-app.streamlit.app`.

1. **Put the code on GitHub.** Create a repository and push this project to it.
   (If it's already on GitHub, skip this.)

2. **Sign in to Streamlit Cloud** at [share.streamlit.io](https://share.streamlit.io)
   with your GitHub account.

3. **Create the app:** click **New app**, choose your repository and branch, and
   set:
   - **Main file path:** `ai-pm/app.py`
   - **Python version:** 3.11 or newer

4. **Add your secrets** (this is where keys go in hosting — *not* a `.env` file).
   In the app's **Settings → Secrets** box, paste your configuration. Use
   `ai-pm/.streamlit/secrets.toml.example` as the template. A minimal hosted
   config looks like this:
   ```toml
   AUTH_ENABLED = "true"
   APP_SECRET_KEY = "paste-a-long-random-string-here"
   APP_BASE_URL = "https://your-app.streamlit.app"

   LLM_PROVIDER = "groq"
   GROQ_API_KEY = "gsk_your_key_here"
   CLEANING_MODE = "local"
   ```
   Generate `APP_SECRET_KEY` by running this locally and pasting the output:
   ```bash
   python -c "import secrets;print(secrets.token_urlsafe(48))"
   ```

5. **Deploy.** Streamlit installs the requirements and launches the app at your
   public URL. Share that URL with your team.

> **Note on storage:** Streamlit Cloud has a temporary filesystem that resets on
> every restart. For a real hosted deployment, set `STORAGE_BACKEND = "db"` so
> uploaded files live in the database alongside everything else (see next step).
> The default `local` storage is only safe for running on your own machine.

---

## 5. Set up the hosted database (Neon)

Locally the app uses a SQLite file (`aipm.db`) automatically — no setup. For
hosting you want a real database so data survives restarts. **Neon** is a free
hosted PostgreSQL service that works perfectly here.

1. Sign up at [neon.tech](https://neon.tech) and create a project.
2. In the Neon dashboard, find the **connection string** for SQLAlchemy /
   psycopg2. It looks like:
   ```
   postgresql://user:password@host/dbname?sslmode=require
   ```
   > It **must** start with `postgresql://` (not `postgres://`) and keep
   > `?sslmode=require`.
3. Add it to your Streamlit secrets, along with database-backed file storage:
   ```toml
   DATABASE_URL = "postgresql://user:password@host/dbname?sslmode=require"
   STORAGE_BACKEND = "db"
   ```
4. Redeploy. The app creates all its tables automatically on first boot — there
   are no migration commands to run.

---

## 6. Turn on logins & accounts

With `AUTH_ENABLED = "true"`, the app requires a username/password login. Here's
how accounts work and how to create your first one.

1. **Seed the first admin account.** Add these to your secrets so an admin user is
   created automatically on first boot:
   ```toml
   SEED_ADMIN_USERNAME = "admin"
   SEED_ADMIN_EMAIL = "you@yourcompany.com"
   SEED_ADMIN_PASSWORD = "choose-a-strong-password"
   ```
   This is idempotent — it only creates the account if it doesn't already exist.
   **Log in and change this password after the first boot.**

2. **Choose how other people get accounts:**
   - `ALLOW_REGISTRATION = "true"` — anyone visiting the app can self-register a
     new account from a "Create account" tab.
   - `ALLOW_REGISTRATION = "false"` — no public signup; the admin creates every
     account from the in-app **Admin** page.

3. **As admin**, use the **Admin** page in the app to:
   - Create **organizations** (your client tenants).
   - Create users, assign them to an organization, and set each one's **role**
     (`user` or `admin`) and **plan** (`free` or `pro`).
   - Set the platform's shared LLM keys and define the Free/Pro tier models.

4. **How keys work per user:** each user can enter their own LLM API keys in the
   in-app **Settings** page. Those keys are encrypted at rest (using
   `APP_SECRET_KEY`). Anything a user leaves blank falls back to the shared keys
   you put in secrets — so a shared Groq key means the app works for everyone out
   of the box.

> **Replacing the original author's accounts:** if the database already contains
> the original author's admin user or keys, log in as your own seeded admin,
> delete the old accounts from the Admin page, and rotate any shared keys in the
> platform settings and in your Streamlit secrets.

---

## 7. Optional: password-reset emails

PM Pilot sends "forgot password" links by email using **Resend** (free tier).

1. Sign up at [resend.com](https://resend.com) and create an API key.
2. Add to secrets:
   ```toml
   RESEND_API_KEY = "re_your_key_here"
   EMAIL_FROM = "PM Pilot <onboarding@resend.dev>"
   ```
   (To send from your own domain, verify it in Resend and use an address on that
   domain in `EMAIL_FROM`.)

**Without** a Resend key, the feature still works — the reset link is simply shown
on screen instead of emailed. That's fine for small teams.

---

## 8. Optional: live Jira push

PM Pilot always produces a downloadable Jira export JSON. To push epics and
stories **directly into a real Jira project**:

1. In Jira, create an **API token** at
   [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens).
2. Each user connects their own Jira account from the in-app **Settings** page by
   entering:
   - **Site URL** — e.g. `https://yourcompany.atlassian.net`
   - **Email** — the Atlassian account email
   - **API token** — from step 1
   - **Project key** — e.g. `PROD`
3. These Jira credentials are encrypted at rest, just like the LLM keys.
4. On the Results page, use **Push to Jira**. Re-pushing the same run is safe —
   issues already created are skipped, never duplicated.

You can also set Jira defaults globally in secrets (`JIRA_BASE_URL`,
`JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`), but per-user
connection from Settings is the recommended path for a team.

---

## 9. All settings reference

These can be set in `.env` (local) or in Streamlit **Secrets** (hosted). The full
annotated list is in `ai-pm/.env.example`.

| Setting | What it does | Default |
|---|---|---|
| `GROQ_API_KEY` | Free Groq key — required to run anything. | — |
| `LLM_PROVIDER` | `groq` / `openai` / `anthropic` / `gemini` / `ollama`. | `groq` |
| `LLM_MODEL` | Override the model; blank = provider default. | (blank) |
| `LLM_FALLBACK_PROVIDER` / `LLM_FALLBACK_MODEL` | Auto-used if the primary is rate-limited/exhausted. | (blank) |
| `PAID` / `PAID_MODEL` | `PAID=true` runs every task on a premium OpenAI model. | `false` |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | Keys for those providers. | — |
| `CLEANING_MODE` | `local` (regex, no LLM) or `llm`. | `local` |
| `DATABASE_URL` | SQLite locally; PostgreSQL string for hosting. | SQLite file |
| `STORAGE_BACKEND` | `local` / `db` / `s3`. Use `db` for hosting. | `local` |
| `AUTH_ENABLED` | `true` requires login. | `false` |
| `ALLOW_REGISTRATION` | `true` allows public self-signup. | `true` |
| `APP_SECRET_KEY` | Encrypts users' stored keys. Long random string. **Required when auth is on.** | — |
| `APP_BASE_URL` | Public app URL (used in reset emails). | — |
| `SEED_ADMIN_USERNAME` / `_EMAIL` / `_PASSWORD` | Auto-create the first admin. | — |
| `RESEND_API_KEY` / `EMAIL_FROM` | Password-reset emails. | — |
| `JIRA_*` | Global Jira defaults (per-user Settings is preferred). | off |

> **Never commit real secrets.** `.env` and `.streamlit/secrets.toml` are
> git-ignored. The `.example` files are safe to commit because they contain only
> placeholders.

---

## 10. Troubleshooting

**`pip install` fails / wrong Python version.**
Confirm `python --version` is 3.11+. On Mac/Linux you may need `python3` and
`pip3` instead of `python` / `pip`.

**App starts but every run fails immediately.**
Your `GROQ_API_KEY` is missing or wrong. Check it in `.env` (local) or Secrets
(hosted). A blank or expired key is the most common cause.

**Hitting rate limits on the free Groq tier.**
Set a fallback (`LLM_FALLBACK_PROVIDER` / `LLM_FALLBACK_MODEL`), or switch heavy
users to Pro mode with an OpenAI key.

**Uploaded files / projects disappear after a hosted restart.**
You're on the default `local` storage on Streamlit Cloud's temporary disk. Set
`STORAGE_BACKEND = "db"` and a real `DATABASE_URL` (Neon). See sections 4–5.

**Password-reset emails don't arrive.**
If `RESEND_API_KEY` is blank, the link is shown on screen instead — that's
expected. If set, check the key and that `EMAIL_FROM` uses a verified domain (or
the default `onboarding@resend.dev`).

**Can't log in after enabling auth.**
Make sure `SEED_ADMIN_*` values are set, then restart so the admin account is
created. Also confirm `APP_SECRET_KEY` is set — auth won't work without it.

**The app is slow between pages on the hosted version.**
Some lag comes from round-trips to a remote database. This is normal on the free
tiers; it isn't an error.
