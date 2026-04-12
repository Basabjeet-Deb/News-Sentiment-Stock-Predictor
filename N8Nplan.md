# n8n integration plan (free, local, no domain or paid hosting)

## What you get from n8n in *this* project

1. **Hands-off refresh + briefing** — On a schedule (e.g. before market open), n8n can check pipeline status, trigger a refresh when appropriate, then call `POST /api/v1/chat/` with prompts like `top picks` or a ticker so you get a ready-made text summary without opening the app every time.

2. **Visual orchestration of your API** — Chain `GET /api/v1/pipeline/status` → conditional run → `POST /api/v1/chat/` → optional `GET` predictions/news endpoints in one flow, with branches, retries, and error paths—no one-off scripts to maintain for each routine.

3. **Proactive alerts** — Watch pipeline `last_result` / error states and notify you (local log, Telegram, Discord, email) when a run fails, stalls, or when fresh predictions land, instead of discovering stale data when you manually check.

4. **Scheduled exports and archives** — Pull predictions or news from `/api/v1/predictions/`, `/api/v1/news/`, etc., transform to CSV or JSON, and write files under a folder you choose—useful for backups, spreadsheets, or comparing runs over time.

5. **Optional “chat from anywhere” glue** — Keep the same deterministic chat logic in FastAPI, but let n8n relay messages from a free channel (e.g. Telegram) to `POST /api/v1/chat/` and send the `response` back—your ticker and “top picks” intents become reachable without building a separate bot service.

---

This document describes how to connect **n8n** to your **News Sentiment Stock Predictor** chatbot and REST API so you can **automate recurring tasks** (pipeline refresh, summaries, alerts) without paying for hosting, a custom domain, or a managed n8n subscription.

Your backend already exposes:

| Purpose | Method | Path |
|--------|--------|------|
| Chat (natural-language style queries) | `POST` | `/api/v1/chat/` |
| Chat health | `GET` | `/api/v1/chat/health` |
| Pipeline status | `GET` | `/api/v1/pipeline/status` |
| Pipeline run (async) | `POST` | `/api/v1/pipeline/run` (see OpenAPI `/docs` for query/body) |
| Predictions / news / stocks | Various | `/api/v1/...` |

Base URL when everything runs on your PC: **`http://127.0.0.1:8000`** (or `http://localhost:8000`).

Chat request body (JSON):

```json
{ "message": "top picks" }
```

Chat response shape:

```json
{ "response": "...", "timestamp": "..." }
```

---

## 1. Design goals (foolproof constraints)

1. **$0 recurring cost** — no VPS, no custom DNS, no paid n8n Cloud tier required.
2. **Runs on your machine** — same Windows box where you already run the FastAPI app (e.g. port `8000`).
3. **No public URL required** for most automations — use **Schedule** and **local HTTP** calls only.
4. **Predictable failures** — every workflow has error handling, retries where safe, and a “human notification” path (optional: local file, OS notification, or a free channel you already use).
5. **Rate limits** — your app uses rate limiting; automation should stay under your configured cap (default `60` requests/minute via `RATE_LIMIT_PER_MINUTE`).

---

## 2. Recommended free architecture

**Components**

- **n8n (local):** workflow engine on your PC; issues HTTP requests to your API.
- **FastAPI on port 8000:** chat (`/api/v1/chat/`), pipeline, predictions, news, and health routes.

**How they connect**

- n8n talks to the app over **HTTP on localhost** (or `host.docker.internal` from Docker). No diagram or graph syntax is required in this doc—only these roles and URLs.

**Triggers that keep you off the public internet**

- **Schedule** — run flows on a calendar or interval (e.g. weekday morning).
- **Manual** — run once from the n8n UI (“Execute workflow”).
- **Optional later:** Telegram/Discord triggers still keep n8n local; only the messenger APIs are outbound.

**What you are *not* relying on here**

- No mandatory public webhook URL, no paid VPS, and no custom domain for the core plan.

### 2.1 Where n8n runs (pick one)

| Option | Cost | Notes |
|--------|------|--------|
| **Docker Desktop** (Windows) + n8n image | Free for personal use | n8n container calls API via `http://host.docker.internal:8000` |
| **`npx n8n`** (Node.js on host) | Free | Calls API via `http://127.0.0.1:8000` (simplest networking) |

Avoid depending on a **public webhook** until you explicitly need inbound triggers from the internet; that usually implies a tunnel or hosted URL.

### 2.2 “No domain” networking rules

- **n8n on host, API on host:** use `http://127.0.0.1:8000`.
- **n8n in Docker, API on host:** use `http://host.docker.internal:8000` (Docker Desktop on Windows).
- **Both in Docker on same compose network:** use the API service name, e.g. `http://api:8000` (only if you later add Compose; not required for this plan).

---

## 3. Integration patterns (what to automate)

### Pattern A — Scheduled “morning brief” (no inbound webhook)

**Trigger:** Schedule (e.g. every weekday 07:30).

**Steps (conceptual):**

1. **HTTP Request** → `GET /api/v1/pipeline/status` — skip heavy work if `is_running` is true.
2. **IF** data stale or you want a refresh → **HTTP Request** → `POST /api/v1/pipeline/run` (respect your API’s semantics; poll status if you add a wait loop).
3. **HTTP Request** → `POST /api/v1/chat/` with body `{ "message": "top picks" }`.
4. **Deliver result** (choose free outputs):
   - **Write Binary File** / append to a local log under your project `logs/`.
   - **Telegram** / **Discord** bot (free; needs bot token — still no hosting for n8n).
   - **Email** via SMTP you already have (Gmail app password, etc.) — optional.

**Why it is foolproof:** no exposure to the public internet; failures are contained to your PC; easy to re-run manually in n8n.

### Pattern B — “Ask the bot” from a messenger (optional, still free)

**Trigger:** Telegram Trigger / Discord Trigger (free accounts).

**Flow:** incoming message → **HTTP Request** to `POST /api/v1/chat/` with the user text (trim length to ≤ 2000 chars to match `ChatRequest`) → reply with `response` field.

**Guardrails:**

- Sanitize input (strip control characters).
- Map errors: if API returns 429, reply “try again in a minute.”
- Do not forward raw stack traces to end users.

### Pattern C — Alert when pipeline fails

**Trigger:** Schedule every N minutes.

**Flow:**

1. `GET /api/v1/pipeline/status`
2. **IF** `last_result.status` (or error fields your API returns) indicates failure → notify (file / Telegram / Discord).

### Pattern D — Data export for spreadsheets (free)

**Trigger:** Schedule weekly.

**Flow:** `GET /api/v1/predictions/` (or summary endpoints) → **Convert to File** (CSV) → save under `exports/` or attach via email.

---

## 4. Concrete n8n node recipes

### 4.1 Call the chatbot

- **Node:** HTTP Request  
- **Method:** POST  
- **URL:** `http://127.0.0.1:8000/api/v1/chat/` (or `host.docker.internal` from Docker)  
- **Body Content Type:** JSON  
- **Body:** `{ "message": "top picks" }`  
- **Response:** read `body.response` for the human-readable string.

### 4.2 Health check before a heavy chain

- **GET** `http://127.0.0.1:8000/api/v1/chat/health`  
- **GET** `http://127.0.0.1:8000/health`

If either fails, branch to **Error Workflow** or a **NoOp** + notification node.

### 4.3 Error handling (minimum bar)

For every HTTP node:

- Enable **Retry On Fail** with conservative settings (e.g. 2 retries, 5 s apart) for transient errors only.
- Add an **Error Trigger** workflow (n8n) that logs: workflow name, node name, error message, timestamp.
- For **429** responses, do not tight-loop; use **Wait** node (e.g. 60 s) then single retry.

---

## 5. Security and abuse resistance (local-first)

1. **Do not expose n8n’s UI to `0.0.0.0` on public Wi-Fi** without authentication. Prefer:
   - n8n listening on `127.0.0.1` only, or
   - Basic auth / n8n’s user management (if you enable it).
2. **Secrets:** store Telegram/Discord tokens in **n8n Credentials**, not in the workflow JSON you share.
3. **Your FastAPI rate limit:** batch scheduled jobs (e.g. one “daily brief” instead of every-minute polling).
4. **Optional hardening (code change, later):** add an `X-Automation-Key` header checked in middleware for routes called only by n8n. Not required for localhost-only use.

---

## 6. “Free but needs internet” (only if you must)

If you later need **inbound** webhooks (Zapier-like triggers from SaaS), typical options are:

- **Cloudflare Tunnel** (free tier exists; still “no paid VPS,” but it is an external edge — use only if you accept that model).
- **Tailscale** (free personal use) to reach your machine privately without a public domain you pay for.

This plan **does not require** any of that for Patterns A/C/D.

---

## 7. Implementation checklist (step-by-step)

1. **Confirm API works:** open `http://127.0.0.1:8000/docs`, try `POST /api/v1/chat/` with `{ "message": "top picks" }`.
2. **Install n8n locally** (Docker or `npx`).
3. **Create workflow “Daily brief”** (linear order):
   1. Schedule trigger  
   2. HTTP Request: pipeline status  
   3. IF node (branch as needed)  
   4. HTTP Request: chat  
   5. Output node (file, log, or messenger)
4. **Execute once manually**; verify the chat text in the last node’s output.
5. **Add Error Workflow** and link it.
6. **Document in your own notes:** base URL, whether n8n is Docker or host (affects hostname).
7. **Optional:** add Telegram/Discord for delivery; retest rate limits.

---

## 8. Testing matrix (what “done” looks like)

| Test | Expected |
|------|----------|
| API down | Error branch fires; no infinite retries |
| Chat with `top picks` | Non-empty `response` or pipeline guidance message |
| Pipeline running | Status node shows `is_running`; workflow waits or exits cleanly |
| Rapid re-runs | No sustained 429s; backoff works |

---

## 9. Future enhancement (optional, not required for n8n)

To let the **chatbot initiate** automation (reverse direction), you could add a FastAPI endpoint or background hook that **POSTs to an n8n Webhook URL** on `localhost` when certain intents fire. That keeps n8n on the same machine and remains domain-free. Only implement if you need true “chat-driven” orchestration beyond what n8n can schedule or receive from messengers.

---

## 10. Summary

- **Cheapest foolproof path:** n8n on your PC + **Schedule** triggers + **HTTP Request** nodes to `http://127.0.0.1:8000/api/v1/chat/` and pipeline endpoints.  
- **No hosting, no domain:** keep everything on **localhost** / **host.docker.internal**.  
- **Reliability:** health checks, error workflow, respect rate limits, conservative retries.

This matches your current chat contract (`ChatRequest` / `response` + `timestamp`) and scales to optional messenger triggers without changing the core app.
