-- 1. Table to store unique Configuration Files (The "Snapshots")
-- This table only grows when a TRULY unique configuration is created.
CREATE TABLE model_configs (
   config_hash CHAR(64) PRIMARY KEY,      -- The SHA-256 Hash of the content
   s3_key VARCHAR(255) NOT NULL,          -- Path to the file in S3
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   
   -- OPTIONAL: Store the YAML as searchable JSONB for querying parameters
   -- e.g., SELECT * FROM model_configs WHERE config_json->>'base_rate' > 500
   config_json JSONB                      
);

-- 2. Table to store the User Interactions (The "Audit Log")
-- This tracks who ran what, when, and any runtime specific metadata.
CREATE TABLE model_runs (
   run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
   user_id VARCHAR(50) NOT NULL,          -- Could be a Foreign Key to a Users table
   config_hash CHAR(64) NOT NULL,         -- Links back to the specific config used
   
   -- Metadata specific to this run (not the config itself)
   execution_time_ms INTEGER,             -- How long the model took to build
   status VARCHAR(20) DEFAULT 'SUCCESS',  -- SUCCESS, FAILED, PENDING
   run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

   FOREIGN KEY (config_hash) REFERENCES model_configs(config_hash)
);

-- Index for fast lookup of a specific user's history
CREATE INDEX idx_model_runs_user ON model_runs(user_id);
