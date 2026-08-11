/**
 * The Ghost Ledger — Cloudflare Worker
 * Gallery API for LucidDreamer.AI session ghosts
 *
 * Routes:
 *   GET  /api/sessions        → list all session ghosts
 *   GET  /api/sessions/:id    → full session detail
 *   POST /api/sessions        → create new ghost
 *   GET  /audio/:key          → serve audio from R2
 *   OPTIONS *                 → CORS preflight
 *
 * Storage:
 *   D1 (GHOST_DB)  — session ghost metadata + full text
 *   R2  (GHOST_AUDIO) — audio files
 *
 * Also serves gallery.html at /
 */

// ---- CORS headers ----
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

function corsify(response) {
  const r = new Response(response.body, response);
  for (const [k, v] of Object.entries(CORS_HEADERS)) {
    r.headers.set(k, v);
  }
  return r;
}

// ---- SQL ----
const SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS ghosts (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  date TEXT NOT NULL,
  models_present TEXT NOT NULL DEFAULT '[]',
  key_quotes TEXT NOT NULL DEFAULT '[]',
  napkin_drawing TEXT,
  barnacles_distillation TEXT,
  essence TEXT,
  full_text TEXT,
  audio_url TEXT,
  themes TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ghosts_date ON ghosts(date DESC);
CREATE INDEX IF NOT EXISTS idx_ghosts_models ON ghosts(models_present);
`;

// ---- Helpers ----
function parseModels(text) {
  // Extract model names from various formats
  if (!text) return [];
  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) return parsed;
  } catch {}
  return [];
}

function ghostFromRow(row) {
  if (!row) return null;
  return {
    id: row.id,
    title: row.title,
    date: row.date,
    models_present: parseModels(row.models_present),
    key_quotes: parseModels(row.key_quotes),
    napkin_drawing: row.napkin_drawing,
    barnacles_distillation: row.barnacles_distillation,
    essence: row.essence,
    full_text: row.full_text,
    audio_url: row.audio_url,
    themes: parseModels(row.themes),
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function ghostSummary(row) {
  // Lighter version for list view (no full_text)
  const g = ghostFromRow(row);
  if (!g) return null;
  delete g.full_text;
  return g;
}

function generateId(title, date) {
  const slug = (title || 'ghost')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 50);
  const datePart = (date || new Date().toISOString().substring(0, 10)).replace(/-/g, '');
  return `${datePart}-${slug}`;
}

// ---- Main handler ----
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    // CORS preflight
    if (method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    // ---- Ensure schema ----
    if (env.GHOST_DB) {
      try {
        await env.GHOST_DB.prepare(SCHEMA_SQL).run();
      } catch (e) {
        // Schema might already exist, that's fine
      }
    }

    // ---- Static routes ----
    if (path === '/' || path === '/gallery.html') {
      // Serve gallery.html (in production, this would be Pages)
      return new Response(GALLERY_HTML, {
        headers: { 'Content-Type': 'text/html; charset=utf-8' },
      });
    }

    // ---- API routes ----
    if (path === '/api/sessions' && method === 'GET') {
      return handleListSessions(request, env);
    }

    if (path === '/api/sessions' && method === 'POST') {
      return handleCreateSession(request, env);
    }

    const sessionMatch = path.match(/^\/api\/sessions\/(.+)$/);
    if (sessionMatch && method === 'GET') {
      return handleGetSession(sessionMatch[1], env);
    }

    // ---- Audio from R2 ----
    const audioMatch = path.match(/^\/audio\/(.+)$/);
    if (audioMatch && method === 'GET' && env.GHOST_AUDIO) {
      const key = decodeURIComponent(audioMatch[1]);
      const object = await env.GHOST_AUDIO.get(key);
      if (!object) {
        return corsify(new Response('Audio not found', { status: 404 }));
      }
      const headers = new Headers();
      object.writeHttpMetadata(headers);
      headers.set('Cache-Control', 'public, max-age=86400');
      headers.set('Accept-Ranges', 'bytes');
      return corsify(new Response(object.body, { headers }));
    }

    // ---- 404 ----
    return corsify(new Response('Not found', { status: 404 }));
  },
};

// ---- GET /api/sessions ----
async function handleListSessions(request, env) {
  if (!env.GHOST_DB) {
    return corsify(Response.json({ sessions: [], note: 'D1 not configured — gallery running in static mode' }));
  }

  const url = new URL(request.url);
  const model = url.searchParams.get('model');
  const date = url.searchParams.get('date');
  const theme = url.searchParams.get('theme');
  const limit = Math.min(parseInt(url.searchParams.get('limit') || '100'), 500);

  let sql = 'SELECT * FROM ghosts';
  const conditions = [];
  const params = [];

  if (model) {
    conditions.push('models_present LIKE ?');
    params.push(`%${model}%`);
  }
  if (date) {
    conditions.push('date LIKE ?');
    params.push(`${date}%`);
  }
  if (theme) {
    conditions.push('themes LIKE ?');
    params.push(`%${theme}%`);
  }

  if (conditions.length > 0) {
    sql += ' WHERE ' + conditions.join(' AND ');
  }
  sql += ' ORDER BY date DESC LIMIT ?';
  params.push(limit);

  try {
    const result = await env.GHOST_DB.prepare(sql).bind(...params).all();
    const sessions = (result.results || []).map(ghostSummary);
    return corsify(Response.json({ sessions, count: sessions.length }));
  } catch (e) {
    return corsify(Response.json({ sessions: [], error: e.message }, { status: 500 }));
  }
}

// ---- GET /api/sessions/:id ----
async function handleGetSession(id, env) {
  if (!env.GHOST_DB) {
    return corsify(Response.json({ error: 'D1 not configured' }, { status: 503 }));
  }

  try {
    const result = await env.GHOST_DB.prepare('SELECT * FROM ghosts WHERE id = ?').bind(id).first();
    if (!result) {
      return corsify(Response.json({ error: 'Ghost not found' }, { status: 404 }));
    }
    return corsify(Response.json(ghostFromRow(result)));
  } catch (e) {
    return corsify(Response.json({ error: e.message }, { status: 500 }));
  }
}

// ---- POST /api/sessions ----
async function handleCreateSession(request, env) {
  if (!env.GHOST_DB) {
    return corsify(Response.json({ error: 'D1 not configured' }, { status: 503 }));
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return corsify(Response.json({ error: 'Invalid JSON' }, { status: 400 }));
  }

  // Validate required fields
  if (!body.title || !body.date) {
    return corsify(Response.json({ error: 'title and date are required' }, { status: 400 }));
  }

  const id = body.id || generateId(body.title, body.date);
  const models = JSON.stringify(body.models_present || []);
  const quotes = JSON.stringify(body.key_quotes || []);
  const themes = JSON.stringify(body.themes || []);

  try {
    await env.GHOST_DB.prepare(`
      INSERT INTO ghosts (id, title, date, models_present, key_quotes, napkin_drawing, barnacles_distillation, essence, full_text, audio_url, themes, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
      ON CONFLICT(id) DO UPDATE SET
        title = excluded.title,
        date = excluded.date,
        models_present = excluded.models_present,
        key_quotes = excluded.key_quotes,
        napkin_drawing = excluded.napkin_drawing,
        barnacles_distillation = excluded.barnacles_distillation,
        essence = excluded.essence,
        full_text = excluded.full_text,
        audio_url = excluded.audio_url,
        themes = excluded.themes,
        updated_at = datetime('now')
    `).bind(
      id,
      body.title,
      body.date,
      models,
      quotes,
      body.napkin_drawing || null,
      body.barnacles_distillation || null,
      body.essence || null,
      body.full_text || null,
      body.audio_url || null,
      themes
    ).run();

    // Return the created ghost
    const result = await env.GHOST_DB.prepare('SELECT * FROM ghosts WHERE id = ?').bind(id).first();
    return corsify(Response.json(ghostFromRow(result), { status: 201 }));
  } catch (e) {
    return corsify(Response.json({ error: e.message }, { status: 500 }));
  }
}

// ---- Minimal HTML fallback (when not served via Pages) ----
const GALLERY_HTML = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>The Ghost Ledger</title><meta http-equiv="refresh" content="0; url=./gallery.html"></head><body>Redirecting to <a href="./gallery.html">gallery.html</a></body></html>`;
