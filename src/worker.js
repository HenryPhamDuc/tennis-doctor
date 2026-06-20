/**
 * Tennis-Doctor — Cloudflare Worker (main entry)
 * ===============================================
 * Serves the static site + provides the /api/chat endpoint for the RAG chatbot.
 *
 * RAG pipeline:
 *   1. Embed user question via @cf/baai/bge-small-en-v1.5 (384 dims)
 *   2. Query Vectorize index for top-8 most relevant chunks
 *   3. Build prompt: system msg + retrieved context + chat history
 *   4. Stream @cf/meta/llama-3.1-8b-instruct response as SSE
 *
 * Bindings (configured in wrangler.toml):
 *   - AI: Workers AI binding
 *   - VECTORIZE: Vectorize index binding
 *   - ASSETS: Pages asset binding (for static site)
 */

// ---------------------------------------------------------------------------
// System prompt — sets the persona + behaviour for the chat bot
// ---------------------------------------------------------------------------
const SYSTEM_PROMPT = `You are **Tennis Doctor**, an expert tennis coach and biomechanics specialist.
You answer questions about tennis using ONLY the provided context below.
Your knowledge base comes from Henry Pham's Vietnamese tennis research vault
(over 350 articles on technique, biomechanics, tactics, mental game, fitness,
and pro player analysis) plus translated English excerpts.

# Your personality
- Clear, structured, friendly coach voice
- Use bullet points, numbered lists, and tables when appropriate
- Cite sources by [1], [2] etc. — the source numbers are provided in context
- Match the user's language: if they ask in Vietnamese, respond in Vietnamese.
  If they ask in English, respond in English (translating any Vietnamese
  context you receive).
- Be concise but thorough — give the "what" and the "why"
- For technique questions, include: setup → execution → key cue → common errors
- For injury/safety questions, add age-related disclaimers (esp. 40+ players)

# Important rules
1. Base your answer ONLY on the provided context. If the context doesn't contain
   the answer, say: "I don't have specific information on that in the tennis vault.
   Could you rephrase or ask a related question?"
2. Do NOT make up specific stats, dates, or quotes that aren't in the context.
3. Always cite at least one source when answering a factual question.
4. Keep responses focused — typically 150-400 words unless the user asks for detail.
5. If the question is outside tennis, politely redirect: "I'm specialised in
   tennis — let me know if you have a tennis question!"
`;

// ---------------------------------------------------------------------------
// CORS headers — allow our site + localhost dev
// ---------------------------------------------------------------------------
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

// ---------------------------------------------------------------------------
// Main fetch handler
// ---------------------------------------------------------------------------
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    // API routes
    if (path === '/api/health') {
      return jsonResponse({
        status: 'ok',
        service: 'tennis-doctor',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
      });
    }

    if (path === '/api/chat' && request.method === 'POST') {
      return handleChat(request, env);
    }

    if (path === '/api/search' && request.method === 'POST') {
      return handleSearch(request, env);
    }

    if (path === '/api/info') {
      return jsonResponse({
        name: 'Tennis Doctor',
        description: 'AI tennis coach powered by Henry Pham research vault',
        models: {
          embedding: '@cf/baai/bge-m3 (multilingual, 1024-dim)',
          llm: '@cf/meta/llama-3.1-8b-instruct',
        },
        knowledgeBase: {
          articles: '350+ from Henry Pham tennis research vault',
          languages: ['Vietnamese (original)', 'English (translated summaries)'],
        },
        limits: {
          topK: 8,
          maxContextChars: 8000,
          maxHistoryMessages: 10,
        },
        languages: ['en', 'vi'],
      });
    }

    // Everything else → static assets (ASSETS binding in wrangler.toml)
    // The Assets binding handles 404s and index.html fallbacks automatically
    return env.ASSETS.fetch(request);
  },
};

// ---------------------------------------------------------------------------
// /api/chat — main RAG endpoint with streaming
// ---------------------------------------------------------------------------
async function handleChat(request, env) {
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid JSON body' }, 400);
  }

  const { question, history = [], stream = true } = body;
  if (!question || typeof question !== 'string' || question.length < 3) {
    return jsonResponse({ error: 'Question must be at least 3 characters' }, 400);
  }
  if (question.length > 1000) {
    return jsonResponse({ error: 'Question too long (max 1000 chars)' }, 400);
  }

  // 1. Embed the question (bge-m3 multilingual, 1024-dim)
  let queryVector;
  try {
    const embeddingResult = await env.AI.run('@cf/baai/bge-m3', {
      text: [question],
    });
    // bge-m3 returns { embeddings: [[...]], ... } or similar shape
    queryVector = embeddingResult.data?.[0] || embeddingResult.embedding?.[0] || embeddingResult[0];
    if (!queryVector || !Array.isArray(queryVector)) {
      throw new Error('Unexpected embedding shape: ' + JSON.stringify(Object.keys(embeddingResult)));
    }
  } catch (e) {
    return jsonResponse({ error: 'Embedding failed: ' + e.message }, 500);
  }

  // 2. Query Vectorize for top-K matches
  let matches = [];
  try {
    const vectorResults = await env.VECTORIZE.query(queryVector, {
      topK: 8,
      returnMetadata: 'all',
    });
    matches = vectorResults.matches || [];
  } catch (e) {
    // If vectorize index doesn't exist yet (first deploy), return gracefully
    return jsonResponse({
      answer: "I'm still loading my knowledge base — please try again in a few minutes!",
      sources: [],
      warning: 'vectorize_unavailable',
    });
  }

  // 3. Build the context block
  const context = buildContext(matches);
  const sources = matches.map((m, i) => ({
    id: i + 1,
    title: m.metadata?.title || 'Untitled',
    slug: m.metadata?.slug || '',
    section: m.metadata?.section || '',
    score: m.score,
    snippet: (m.metadata?.text || '').slice(0, 200) + (m.metadata?.text?.length > 200 ? '…' : ''),
  }));

  // 4. Build the messages array
  const messages = [
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'system', content: `Knowledge base context:\n\n${context}` },
  ];
  // Trim history to last 10 exchanges
  const trimmedHistory = history.slice(-10);
  for (const msg of trimmedHistory) {
    if (msg.role && msg.content && ['user', 'assistant'].includes(msg.role)) {
      messages.push({ role: msg.role, content: msg.content.slice(0, 2000) });
    }
  }
  messages.push({ role: 'user', content: question });

  // 5. Generate response — stream or batch
  if (stream) {
    return streamChat(messages, sources, env);
  } else {
    return batchChat(messages, sources, env);
  }
}

// ---------------------------------------------------------------------------
// Streaming chat (Server-Sent Events)
// ---------------------------------------------------------------------------
function streamChat(messages, sources, env) {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        // Send sources first as a "sources" event
        controller.enqueue(encoder.encode(`event: sources\ndata: ${JSON.stringify(sources)}\n\n`));

        // Then stream the LLM response token by token
        const aiResponse = await env.AI.run(
          '@cf/meta/llama-3.1-8b-instruct',
          {
            messages,
            stream: true,
            max_tokens: 800,
            temperature: 0.7,
            top_p: 0.9,
          }
        );

        for await (const chunk of aiResponse) {
          const token = chunk.response || '';
          if (token) {
            controller.enqueue(encoder.encode(`event: token\ndata: ${JSON.stringify(token)}\n\n`));
          }
        }

        // Done event
        controller.enqueue(encoder.encode(`event: done\ndata: [DONE]\n\n`));
        controller.close();
      } catch (e) {
        controller.enqueue(encoder.encode(`event: error\ndata: ${JSON.stringify({ error: e.message })}\n\n`));
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      ...CORS_HEADERS,
    },
  });
}

// ---------------------------------------------------------------------------
// Batch (non-streaming) chat — fallback or for testing
// ---------------------------------------------------------------------------
async function batchChat(messages, sources, env) {
  try {
    const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
      messages,
      max_tokens: 800,
      temperature: 0.7,
      top_p: 0.9,
    });
    return jsonResponse({
      answer: response.response || '',
      sources,
    });
  } catch (e) {
    return jsonResponse({ error: 'Generation failed: ' + e.message }, 500);
  }
}

// ---------------------------------------------------------------------------
// /api/search — pure semantic search (no LLM, just top chunks)
// ---------------------------------------------------------------------------
async function handleSearch(request, env) {
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid JSON body' }, 400);
  }
  const { query, topK = 5 } = body;
  if (!query) {
    return jsonResponse({ error: 'Missing query' }, 400);
  }
  try {
    const embeddingResult = await env.AI.run('@cf/baai/bge-m3', {
      text: [query],
    });
    const queryVector = embeddingResult.data?.[0] || embeddingResult.embedding?.[0] || embeddingResult[0];
    const results = await env.VECTORIZE.query(queryVector, {
      topK: Math.min(topK, 20),
      returnMetadata: 'all',
    });
    return jsonResponse({
      results: (results.matches || []).map(m => ({
        title: m.metadata?.title,
        slug: m.metadata?.slug,
        section: m.metadata?.section,
        text: m.metadata?.text,
        score: m.score,
      })),
    });
  } catch (e) {
    return jsonResponse({ error: e.message }, 500);
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function buildContext(matches) {
  if (!matches.length) return '(no relevant context found)';
  let totalChars = 0;
  const MAX = 8000;
  const parts = [];
  for (let i = 0; i < matches.length; i++) {
    const m = matches[i];
    const text = (m.metadata?.text || '').trim();
    const title = m.metadata?.title || `Source ${i + 1}`;
    const section = m.metadata?.section ? ` [${m.metadata.section}]` : '';
    const block = `[${i + 1}] ${title}${section}\n${text}`;
    if (totalChars + block.length > MAX) break;
    parts.push(block);
    totalChars += block.length;
  }
  return parts.join('\n\n---\n\n');
}

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...CORS_HEADERS,
    },
  });
}