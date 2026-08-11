-- ============================================================
-- LucidDreamer.AI — Master D1 Schema
-- Database: luciddreamer-db
-- ============================================================
-- This file is the canonical schema. It creates all tables for
-- the main worker (tracks, feedback, sessions, now_playing) and
-- the knowledge base (ideas, relationships, models) and the
-- gallery (ghosts). All tables use IF NOT EXISTS so re-running
-- is safe.
-- ============================================================

-- ─── Tracks ──────────────────────────────────────────────────
-- Every piece of audio content the station has produced.
CREATE TABLE IF NOT EXISTS tracks (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    source_model TEXT,
    duration     INTEGER,           -- seconds
    audio_key    TEXT,              -- R2 object key
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    tags         TEXT DEFAULT '[]'  -- JSON array
);
CREATE INDEX IF NOT EXISTS idx_tracks_created   ON tracks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tracks_model     ON tracks(source_model);
CREATE INDEX IF NOT EXISTS idx_tracks_tags      ON tracks(tags);

-- ─── Feedback ────────────────────────────────────────────────
-- Listener feedback submitted from the web player.
CREATE TABLE IF NOT EXISTS feedback (
    id          TEXT PRIMARY KEY,
    track_id    TEXT,
    text        TEXT NOT NULL,
    sentiment   TEXT DEFAULT 'neutral',   -- positive | neutral | negative
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    session_id  TEXT,
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);
CREATE INDEX IF NOT EXISTS idx_feedback_track   ON feedback(track_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);

-- ─── Sessions ────────────────────────────────────────────────
-- Creative sessions that produced content (Tap sessions, solo
-- agent sessions, collaborative rounds, etc.)
CREATE TABLE IF NOT EXISTS sessions (
    id             TEXT PRIMARY KEY,
    character_json TEXT,              -- JSON: participating agents/personas
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    status         TEXT DEFAULT 'active'   -- active | completed | archived
);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);

-- ─── Now Playing ─────────────────────────────────────────────
-- Current and historical broadcast state.
CREATE TABLE IF NOT EXISTS now_playing (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id       TEXT,
    started_at     TEXT NOT NULL DEFAULT (datetime('now')),
    listener_count INTEGER DEFAULT 0,
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);
CREATE INDEX IF NOT EXISTS idx_nowplaying_started ON now_playing(started_at DESC);

-- ─── Ideas ───────────────────────────────────────────────────
-- The atomic unit of the knowledge base: an insight, question,
-- risk, vision, or other creative/intellectual artifact.
CREATE TABLE IF NOT EXISTS ideas (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    content         TEXT,
    type            TEXT NOT NULL DEFAULT 'insight',  -- insight | risk | vision | question | decision
    source_model    TEXT,
    session         TEXT,
    status          TEXT NOT NULL DEFAULT 'seed',     -- seed | growing | mature | archived
    embedding_id    TEXT,                              -- Vectorize vector ID
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ideas_type    ON ideas(type);
CREATE INDEX IF NOT EXISTS idx_ideas_model   ON ideas(source_model);
CREATE INDEX IF NOT EXISTS idx_ideas_status  ON ideas(status);
CREATE INDEX IF NOT EXISTS idx_ideas_session ON ideas(session);

-- ─── Relationships ───────────────────────────────────────────
-- Typed edges between ideas.
CREATE TABLE IF NOT EXISTS relationships (
    from_id    TEXT NOT NULL,
    to_id      TEXT NOT NULL,
    type       TEXT NOT NULL,            -- evolves_from | contradicts | supports | converges_with
    note       TEXT,
    PRIMARY KEY (from_id, to_id, type),
    FOREIGN KEY (from_id) REFERENCES ideas(id),
    FOREIGN KEY (to_id)   REFERENCES ideas(id)
);
CREATE INDEX IF NOT EXISTS idx_rel_from ON relationships(from_id);
CREATE INDEX IF NOT EXISTS idx_rel_to   ON relationships(to_id);
CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(type);

-- ─── Models ──────────────────────────────────────────────────
-- AI models that participate in the fleet.
CREATE TABLE IF NOT EXISTS models (
    id          TEXT PRIMARY KEY,
    name        TEXT,
    alias       TEXT,
    personality TEXT,
    perspective TEXT
);

-- ─── Ghosts (Gallery) ────────────────────────────────────────
-- Compressed session records for the Ghost Ledger gallery.
CREATE TABLE IF NOT EXISTS ghosts (
    id                     TEXT PRIMARY KEY,
    title                  TEXT NOT NULL,
    date                   TEXT NOT NULL,
    models_present         TEXT NOT NULL DEFAULT '[]',
    key_quotes             TEXT NOT NULL DEFAULT '[]',
    napkin_drawing         TEXT,
    barnacles_distillation TEXT,
    essence                TEXT,
    full_text              TEXT,
    audio_url              TEXT,
    themes                 TEXT NOT NULL DEFAULT '[]',
    created_at             TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at             TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ghosts_date   ON ghosts(date DESC);
CREATE INDEX IF NOT EXISTS idx_ghosts_models ON ghosts(models_present);
