CREATE TABLE IF NOT EXISTS prefixes (
    guild_id INTEGER NOT NULL PRIMARY KEY,
    prefix TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS unbans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    unban_time TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS join_gate (
    guild_id INTEGER NOT NULL PRIMARY KEY,
    age TEXT DEFAULT NULL,
    avatar INTEGER DEFAULT 0,
    action TEXT DEFAULT 'kick',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS antinuke (
    guild_id INTEGER NOT NULL,
    module TEXT NOT NULL,
    threshold TEXT NOT NULL DEFAULT '3',
    punishment TEXT NOT NULL DEFAULT 'kick',
    enabled BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, module)
);