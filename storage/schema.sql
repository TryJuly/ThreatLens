CREATE TABLE IF NOT EXISTS events (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMP NOT NULL,
    sensor      TEXT NOT NULL,
    event       TEXT NOT NULL,
    src_ip      INET NOT NULL,
    src_port    INT NOT NULL,
    username    TEXT NOT NULL,
    password    TEXT NOT NULL,
    data    JSONB
);

CREATE INDEX IF NOT EXISTS idx_events_ip ON events (src_ip);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events (ts);
CREATE INDEX IF NOT EXISTS idx_events_event ON events (event);

CREATE TABLE IF NOT EXISTS ip_info (
    ip  INET PRIMARY KEY,
    country TEXT,
    city TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    asn INTEGER,
    org TEXT,
    abuse_score INTEGER,
    checked_at TIMESTAMPTZ
);