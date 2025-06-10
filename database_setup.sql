-- Database schema voor Discord Gameserver Access Control Bot

-- Gebruikers tabel - koppelt Discord users aan game usernames
CREATE TABLE IF NOT EXISTS users (
    discord_id TEXT PRIMARY KEY,
    discord_username TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Game accounts tabel - opslag van game-specifieke usernames
CREATE TABLE IF NOT EXISTS game_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT NOT NULL,
    game_type TEXT NOT NULL,  -- 'minecraft', 'palworld', 'beamng', etc.
    game_username TEXT NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (discord_id) REFERENCES users(discord_id),
    UNIQUE(discord_id, game_type)  -- Een game username per game per gebruiker
);

-- Servers tabel - configuratie van alle game servers
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_name TEXT NOT NULL UNIQUE,
    game_type TEXT NOT NULL,
    log_path TEXT,
    rcon_host TEXT DEFAULT 'localhost',
    rcon_port INTEGER,
    rcon_password TEXT,
    required_level INTEGER DEFAULT 1,
    discord_channel_id TEXT,  -- Voor status updates
    active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Level requirements tabel - welk level is nodig voor welke server
CREATE TABLE IF NOT EXISTS level_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    required_level INTEGER NOT NULL DEFAULT 1,
    role_name TEXT,  -- Optioneel: specifieke Discord role
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id)
);

-- Activity log - log van alle bot acties
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id TEXT,
    server_id INTEGER,
    action TEXT NOT NULL,  -- 'join_attempt', 'kick', 'whitelist_add', etc.
    game_username TEXT,
    result TEXT,  -- 'success', 'failed', 'denied'
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (discord_id) REFERENCES users(discord_id),
    FOREIGN KEY (server_id) REFERENCES servers(id)
);

-- Discord level cache - cache Discord levels voor performance
CREATE TABLE IF NOT EXISTS discord_levels (
    discord_id TEXT PRIMARY KEY,
    current_level INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (discord_id) REFERENCES users(discord_id)
);

-- Indexes voor betere performance
CREATE INDEX IF NOT EXISTS idx_game_accounts_discord_game ON game_accounts(discord_id, game_type);
CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp ON activity_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_servers_game_type ON servers(game_type);
CREATE INDEX IF NOT EXISTS idx_discord_levels_level ON discord_levels(current_level);
