CREATE TABLE IF NOT EXISTS drivers (
  driver_id TEXT PRIMARY KEY,
  driver_code TEXT,
  driver_name TEXT
);

CREATE TABLE IF NOT EXISTS constructors (
  constructor_id TEXT PRIMARY KEY,
  constructor_name TEXT
);

CREATE TABLE IF NOT EXISTS races (
  race_id SERIAL PRIMARY KEY,
  season INT,
  round INT,
  race_name TEXT,
  circuit_id TEXT,
  race_date DATE
);

CREATE TABLE IF NOT EXISTS results (
  result_id SERIAL PRIMARY KEY,
  season INT,
  round INT,
  driver_id TEXT,
  constructor_id TEXT,
  grid INT,
  finish_position INT,
  points NUMERIC,
  status TEXT
);