-- Add user_table_configs table
CREATE TABLE IF NOT EXISTS user_table_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    table_key VARCHAR(64) NOT NULL,
    columns JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create unique constraint to ensure one config per user per table
ALTER TABLE user_table_configs 
ADD CONSTRAINT uq_user_table_config UNIQUE (user_id, table_key);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_table_configs_user_id ON user_table_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_table_configs_table_key ON user_table_configs(table_key);

-- Add trigger to automatically update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_table_configs_updated_at 
    BEFORE UPDATE ON user_table_configs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column(); 