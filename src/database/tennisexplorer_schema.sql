-- TennisExplorer Database Schema
-- ===================================
-- PostgreSQL schema for storing TennisExplorer scraped data
-- 
-- Usage:
--   psql -U username -d database_name -f tennisexplorer_schema.sql
--   Or use SQLite for MVP: sqlite3 tennisexplorer.db < tennisexplorer_schema.sql

-- Main matches table
CREATE TABLE IF NOT EXISTS tennisexplorer_matches (
    match_id VARCHAR(100) PRIMARY KEY,
    player_a VARCHAR(200) NOT NULL,
    player_b VARCHAR(200) NOT NULL,
    tournament VARCHAR(200),
    tournament_tier VARCHAR(20),  -- W15, W25, W35, W50, W75, W100, Challenger
    surface VARCHAR(20),  -- Hard, Clay, Grass
    current_score VARCHAR(50),
    match_status VARCHAR(20),  -- 'live', 'scheduled', 'finished'
    match_url TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Odds history table (tracks odds movements)
CREATE TABLE IF NOT EXISTS odds_history (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(100) REFERENCES tennisexplorer_matches(match_id) ON DELETE CASCADE,
    odds_a DECIMAL(5,2),
    odds_b DECIMAL(5,2),
    bookmaker VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, bookmaker, timestamp)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_odds_history_match_id ON odds_history(match_id);
CREATE INDEX IF NOT EXISTS idx_odds_history_timestamp ON odds_history(timestamp);

-- H2H records table
CREATE TABLE IF NOT EXISTS h2h_records (
    id SERIAL PRIMARY KEY,
    player_a VARCHAR(200) NOT NULL,
    player_b VARCHAR(200) NOT NULL,
    surface VARCHAR(20),  -- NULL for overall, 'Hard', 'Clay', 'Grass' for surface-specific
    wins_a INTEGER DEFAULT 0,
    wins_b INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_a, player_b, surface)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_h2h_players ON h2h_records(player_a, player_b);
CREATE INDEX IF NOT EXISTS idx_h2h_surface ON h2h_records(surface);

-- Player form table (recent W-L records)
CREATE TABLE IF NOT EXISTS player_form (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(200) NOT NULL,
    surface VARCHAR(20),  -- NULL for overall, 'Hard', 'Clay', 'Grass' for surface-specific
    last_5_wins INTEGER DEFAULT 0,
    last_5_losses INTEGER DEFAULT 0,
    last_10_wins INTEGER DEFAULT 0,
    last_10_losses INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_name, surface)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_player_form_name ON player_form(player_name);
CREATE INDEX IF NOT EXISTS idx_player_form_surface ON player_form(surface);

-- Player ELO ratings table
CREATE TABLE IF NOT EXISTS player_elo_ratings (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(200) NOT NULL UNIQUE,
    overall_elo DECIMAL(6,2) DEFAULT 1500.0,
    hard_elo DECIMAL(6,2) DEFAULT 1500.0,
    clay_elo DECIMAL(6,2) DEFAULT 1500.0,
    grass_elo DECIMAL(6,2) DEFAULT 1500.0,
    career_high_elo DECIMAL(6,2) DEFAULT 1500.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_elo_player_name ON player_elo_ratings(player_name);

-- Match weather data table
CREATE TABLE IF NOT EXISTS match_weather (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(100) REFERENCES tennisexplorer_matches(match_id) ON DELETE CASCADE,
    temperature_celsius DECIMAL(4,1),
    wind_speed_kmh DECIMAL(5,2),
    humidity_percent DECIMAL(4,1),
    rain_probability DECIMAL(4,1),
    weather_conditions VARCHAR(50),  -- 'sunny', 'cloudy', 'rain', etc.
    forecast_time TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, forecast_time)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_weather_match_id ON match_weather(match_id);

-- Player service/return stats table
CREATE TABLE IF NOT EXISTS player_stats (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(200) NOT NULL,
    surface VARCHAR(20),  -- NULL for overall, 'Hard', 'Clay', 'Grass'
    period VARCHAR(20),  -- 'career', 'last_10', 'last_30'
    aces_per_match DECIMAL(4,2) DEFAULT 0.0,
    double_faults_per_match DECIMAL(4,2) DEFAULT 0.0,
    hold_percentage DECIMAL(5,2) DEFAULT 0.0,  -- Service games won %
    break_percentage DECIMAL(5,2) DEFAULT 0.0,  -- Return games won %
    second_serve_win_percentage DECIMAL(5,2) DEFAULT 0.0,
    break_points_saved_percentage DECIMAL(5,2) DEFAULT 0.0,
    break_points_converted_percentage DECIMAL(5,2) DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_name, surface, period)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_player_stats_name ON player_stats(player_name);
CREATE INDEX IF NOT EXISTS idx_player_stats_surface ON player_stats(surface);

-- Tiebreak and deciding set records
CREATE TABLE IF NOT EXISTS player_tiebreak_stats (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(200) NOT NULL,
    period VARCHAR(20),  -- 'career', 'last_12_months'
    tiebreak_wins INTEGER DEFAULT 0,
    tiebreak_losses INTEGER DEFAULT 0,
    tiebreak_win_percentage DECIMAL(5,2) DEFAULT 0.0,
    deciding_set_wins INTEGER DEFAULT 0,
    deciding_set_losses INTEGER DEFAULT 0,
    deciding_set_win_percentage DECIMAL(5,2) DEFAULT 0.0,
    clutch_factor DECIMAL(5,2) DEFAULT 0.0,  -- Performance under pressure score
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_name, period)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_tiebreak_player_name ON player_tiebreak_stats(player_name);

-- Travel and recovery data
CREATE TABLE IF NOT EXISTS player_recovery (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(200) NOT NULL,
    match_id VARCHAR(100) REFERENCES tennisexplorer_matches(match_id) ON DELETE CASCADE,
    days_since_last_match DECIMAL(4,1),
    travel_distance_km DECIMAL(8,2),
    timezone_difference_hours INTEGER,
    fatigue_risk_score INTEGER,  -- 0-100
    last_tournament_location VARCHAR(200),
    current_tournament_location VARCHAR(200),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_name, match_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_recovery_player_name ON player_recovery(player_name);
CREATE INDEX IF NOT EXISTS idx_recovery_match_id ON player_recovery(match_id);

-- Tournament history at venue
CREATE TABLE IF NOT EXISTS tournament_history (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(200) NOT NULL,
    tournament VARCHAR(200) NOT NULL,
    year INTEGER,
    result VARCHAR(50),  -- 'W', 'F', 'SF', 'QF', 'R16', etc.
    round_reached VARCHAR(20),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_name, tournament, year)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_tournament_history_player ON tournament_history(player_name);
CREATE INDEX IF NOT EXISTS idx_tournament_history_tournament ON tournament_history(tournament);

-- Court speed index mapping
CREATE TABLE IF NOT EXISTS venue_court_speed (
    id SERIAL PRIMARY KEY,
    venue_name VARCHAR(200) NOT NULL UNIQUE,
    court_speed_index INTEGER,  -- 35-55 scale (35=slow, 45=medium, 55=fast)
    surface VARCHAR(20),
    notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_venue_name ON venue_court_speed(venue_name);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_tennisexplorer_matches_updated_at BEFORE UPDATE ON tennisexplorer_matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_h2h_records_updated_at BEFORE UPDATE ON h2h_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_form_updated_at BEFORE UPDATE ON player_form
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_elo_ratings_updated_at BEFORE UPDATE ON player_elo_ratings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_stats_updated_at BEFORE UPDATE ON player_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_tiebreak_stats_updated_at BEFORE UPDATE ON player_tiebreak_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries

-- View: Recent matches with basic info
CREATE OR REPLACE VIEW recent_matches_view AS
SELECT 
    m.match_id,
    m.player_a,
    m.player_b,
    m.tournament,
    m.tournament_tier,
    m.surface,
    m.current_score,
    m.match_status,
    m.scraped_at
FROM tennisexplorer_matches m
WHERE m.scraped_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY m.scraped_at DESC;

-- View: Player form summary
CREATE OR REPLACE VIEW player_form_summary_view AS
SELECT 
    pf.player_name,
    pf.surface,
    pf.last_5_wins,
    pf.last_5_losses,
    ROUND(100.0 * pf.last_5_wins / NULLIF(pf.last_5_wins + pf.last_5_losses, 0), 2) AS last_5_win_pct,
    pf.last_10_wins,
    pf.last_10_losses,
    ROUND(100.0 * pf.last_10_wins / NULLIF(pf.last_10_wins + pf.last_10_losses, 0), 2) AS last_10_win_pct,
    pf.updated_at
FROM player_form pf;

-- View: H2H summary
CREATE OR REPLACE VIEW h2h_summary_view AS
SELECT 
    h.player_a,
    h.player_b,
    h.surface,
    h.wins_a,
    h.wins_b,
    h.wins_a + h.wins_b AS total_matches,
    ROUND(100.0 * h.wins_a / NULLIF(h.wins_a + h.wins_b, 0), 2) AS player_a_win_pct,
    h.last_updated
FROM h2h_records h;

