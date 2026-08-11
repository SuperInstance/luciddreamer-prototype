
-- Idea nodes table
CREATE TABLE IF NOT EXISTS ideas (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    idea_type TEXT,
    source_model TEXT,
    source_session TEXT,
    source_file TEXT,
    lineage TEXT,        -- JSON array of parent IDs
    status TEXT,
    tags TEXT,           -- JSON array
    timestamp REAL,
    metadata TEXT        -- JSON object
);

-- Connections (edges) table
CREATE TABLE IF NOT EXISTS connections (
    source_id TEXT,
    target_id TEXT,
    relationship TEXT,
    note TEXT,
    strength REAL,
    PRIMARY KEY (source_id, target_id, relationship)
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    date TEXT,
    source_file TEXT,
    session_type TEXT,
    participants TEXT,   -- JSON array
    description TEXT,
    timestamp REAL
);

-- Models table
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    name TEXT,
    alias TEXT,
    personality TEXT,
    strengths TEXT,      -- JSON array
    perspective TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ideas_type ON ideas(idea_type);
CREATE INDEX IF NOT EXISTS idx_ideas_model ON ideas(source_model);
CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(status);
CREATE INDEX IF NOT EXISTS idx_connections_source ON connections(source_id);
CREATE INDEX IF NOT EXISTS idx_connections_target ON connections(target_id);
CREATE INDEX IF NOT EXISTS idx_connections_rel ON connections(relationship);
