# 🎾 Tennis Doctor

> **AI-powered tennis coach** — ask anything about tennis technique, biomechanics, tactics, mental game, fitness, or pro players.
> Answers come from a knowledge base of **350+ articles** by Henry Phạm's Vietnamese tennis research vault, with multilingual retrieval (Vietnamese + English).

[![Built with Cloudflare Workers](https://img.shields.io/badge/Cloudflare-Workers-orange)](https://workers.cloudflare.com/)
[![Workers AI](https://img.shields.io/badge/Powered_by-Workers_AI-blue)](https://developers.cloudflare.com/workers-ai/)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

## 🌟 What it does

You ask a tennis question → Tennis Doctor retrieves the most relevant chunks from the vault → passes them as context to Llama 3.1 8B → streams the answer back.

**Example questions it can answer:**
- "How does Carlos Alcaraz generate power on his forehand?"
- "What is the kinetic chain and why does it matter?"
- "I'm 52 and my knees hurt after playing — what should I do?"
- "Explain the 70% rule"
- "How can I improve my split step?"
- (Vietnamese) "Kỹ thuật volley đúng cách là gì?"

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  Browser (henryphamduc.github.io/tennis-doctor)      │
│  - Vanilla JS chat widget with streaming SSE        │
│  - Bilingual UI + language toggle                   │
└─────────────────────────────────────────────────────┘
                            │ POST /api/chat (SSE)
                            ▼
┌─────────────────────────────────────────────────────┐
│  Cloudflare Worker (src/worker.js)                  │
│  1. Embed question via @cf/baai/bge-m3 (1024-dim)   │
│  2. Query Vectorize → top 8 chunks                  │
│  3. Build prompt (system + context + history)       │
│  4. Stream @cf/meta/llama-3.1-8b-instruct response  │
└─────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────┐
│  Cloudflare Vectorize (tennis-doctor-embeddings)    │
│  - 1,113 chunks × 1024 dims (bge-m3 multilingual)   │
│  - Stored metadata: title, slug, section, lang      │
└─────────────────────────────────────────────────────┘
```

### Why these choices?

| Decision | Reason |
|---|---|
| **Cloudflare Workers** (not Vercel/Render) | Free tier: 100k requests/day, edge-deployed, no cold starts |
| **Workers AI** (not OpenAI/Anthropic) | Free Llama 3.1 8B + bge-m3 embeddings, no API keys, billed per-second |
| **Vectorize** (not Pinecone) | Free tier: 30M vector dims, 30M queries/month, integrated with Workers |
| **bge-m3** (not OpenAI embeddings) | Multilingual (Vietnamese + English), 1024-dim, free via Workers AI |
| **Llama 3.1 8B** (not larger) | Free tier, fast, sufficient for Q&A with good context |
| **Streaming SSE** (not polling) | Better UX, real-time response, lower server load |
| **Vanilla JS** (not React/Vue) | No build step, ~15 KB total, runs anywhere |
| **Pass-through translation** (not full LLM translate) | 348 articles × 35s/article = too slow; bge-m3 finds VI content even from EN queries |

## 🚀 Deploy to your own Cloudflare account

### Prerequisites
- Node.js 18+ installed
- A Cloudflare account (free, sign up at [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up))
- A GitHub account (for hosting the static part + the worker code)

### Step 1 — Clone and install

```bash
git clone https://github.com/HenryPhamDuc/tennis-doctor.git
cd tennis-doctor
npm install
```

### Step 2 — Get Cloudflare credentials

1. Find your **Account ID**: Cloudflare dashboard → right sidebar → "Account ID" → copy
2. Create an **API Token** with these permissions:
   - Account → Workers Scripts → Edit
   - Account → Workers AI → Read
   - Account → Vectorize → Edit
   - User → User Details → Read
3. Save both as env vars:
   ```bash
   export CF_ACCOUNT_ID="your-account-id-here"
   export CF_API_TOKEN="your-api-token-here"
   ```

You can also put them in a `.env` file in the `scripts/` directory:
```
CF_ACCOUNT_ID=your-account-id-here
CF_API_TOKEN=your-api-token-here
```

### Step 3 — Authenticate wrangler (for deploy)

```bash
npx wrangler login
```
This opens a browser to OAuth-authorize wrangler with your Cloudflare account.

### Step 4 — Create the Vectorize index

```bash
npm run deploy:setup
```
This creates the `tennis-doctor-embeddings` index (1024-dim, cosine metric) with metadata indexes for `section`, `slug`, `lang`.

### Step 5 — Generate embeddings and upload

```bash
python scripts/translate_to_english.py   # creates docs-source/_manifest.json
python scripts/generate_embeddings.py    # embeds + uploads to Vectorize
```
This takes ~30 seconds (Cloudflare Workers AI is fast).

### Step 6 — Deploy the worker + static site

```bash
npx wrangler deploy
```
This deploys both the Worker (API) and the static assets (chat UI, landing page) to Cloudflare's global edge.

### Step 7 — Custom domain (optional)

In `wrangler.toml`, uncomment the `routes` block and set your domain. Then in Cloudflare DNS, add a CNAME record pointing your subdomain to `tennis-doctor.<account-subdomain>.workers.dev`.

## 🛠️ Local development

```bash
# Local worker dev (requires wrangler login or env vars)
npx wrangler dev

# Visit:
# http://localhost:8787              → landing page
# http://localhost:8787/chat/       → chat page
# http://localhost:8787/api/health  → health check

# Without Vectorize, the chat will return a "still loading" message.
# Once you've run the embedding pipeline in production, /api/chat will work.
```

## 📁 Project structure

```
tennis-doctor/
├── src/
│   └── worker.js                     # Cloudflare Worker: RAG chat API
├── docs/                             # Static site (served by the worker)
│   ├── index.html                    # Landing page with embedded chat
│   ├── chat/index.html               # Standalone chat page
│   └── assets/
│       ├── chat.css                  # All styles
│       ├── chat.js                   # Vanilla JS chat widget
│       └── logo.svg                  # 🎾 logo
├── scripts/
│   ├── translate_to_english.py       # MD → chunks manifest (pass-through)
│   └── generate_embeddings.py        # bge-m3 embed + Vectorize upsert
├── wrangler.toml                     # Cloudflare config
├── package.json                      # npm scripts
└── README.md                         # This file
```

## 🌍 Bilingual setup

The site is **English** by default. The language toggle (top-right of nav) sets a cookie and redirects to:

- **English** → Tennis Doctor (this site)
- **Vietnamese** → Tennis-WIKI at [henryphamduc.github.io/tennis-wiki](https://henryphamduc.github.io/tennis-wiki/)

The chat bot is **bilingual-aware**:
- Embeddings use bge-m3 (multilingual) — works equally for VI and EN queries
- LLM responds in the same language as the question
- Knowledge base contains Vietnamese originals + English summaries in frontmatter

## 🧪 Testing the API

```bash
# Health check
curl https://your-domain.com/api/health

# Search (raw semantic search, no LLM)
curl -X POST https://your-domain.com/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"kinetic chain tennis","topK":3}'

# Chat (streaming SSE)
curl -X POST https://your-domain.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the kinetic chain?","stream":false}'
```

## 📊 Performance & limits

| | Free tier | Your usage |
|---|---|---|
| Workers requests | 100,000/day | ~1,000 chats/day |
| Workers AI (Llama 3.1 8B) | 10,000 neurons/day | ~2,000 chats/day |
| Workers AI (bge-m3) | Same | ~3,000 queries/day |
| Vectorize storage | 30M dims | 1.14M dims (1,113 × 1024) |
| Vectorize queries | 30M/month | ~30k/month |

You're well within all free tiers.

## 🔒 Security & privacy

- **No user data stored**: chat history is in-memory only; nothing persisted server-side
- **No auth required**: this is a public research/demo site
- **CORS open**: `Access-Control-Allow-Origin: *` for the API (so you can build other frontends on top)
- **Rate limit**: not implemented yet; can add via Cloudflare WAF rules

## 🤝 Contributing

The Vietnamese source content lives in the original [tennis-wiki repo](https://github.com/HenryPhamDuc/tennis-wiki). Improvements to the corpus flow through there.

For the chatbot code itself (Worker, frontend, embedding pipeline):
1. Fork this repo
2. Create a branch: `git checkout -b feature/improve-retrieval`
3. Make changes, test locally with `wrangler dev`
4. Open a PR

## 📜 License

- **Content** (the source articles): CC BY-SA 4.0 — Henry Phạm
- **Code** (Worker, frontend, scripts): MIT

## 📞 Links

- **Live site**: https://tennis-doctor.example.com (replace with your actual URL after deploy)
- **Vietnamese wiki**: https://henryphamduc.github.io/tennis-wiki/
- **GitHub**: https://github.com/HenryPhamDuc/tennis-doctor
- **Henry's blog**: https://tennis-for-everyone.blogspot.com/

---

🎾 Tennis Doctor &copy; 2026 Henry Phạm — Built with ❤️ on Cloudflare's free edge platform.