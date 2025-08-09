-- Migration: Add OAuth support to users table
-- This prepares the schema for OAuth providers while maintaining JWT compatibility

-- Add OAuth provider support
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50) DEFAULT 'local';
ALTER TABLE users ADD COLUMN IF NOT EXISTS external_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_tokens JSONB;
ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_scopes TEXT[];
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;

-- Create unique constraint for external auth
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_provider_external_id 
ON users(auth_provider, external_id) 
WHERE auth_provider != 'local';

-- Update existing users to be 'local' auth provider
UPDATE users SET auth_provider = 'local' WHERE auth_provider IS NULL;

-- Comments for future OAuth integration
COMMENT ON COLUMN users.password_hash IS 'Hashed password for local auth, NULL for OAuth users';
COMMENT ON COLUMN users.auth_provider IS 'Auth provider: local, google, microsoft, etc.';
COMMENT ON COLUMN users.external_id IS 'User ID from external OAuth provider';
COMMENT ON COLUMN users.oauth_tokens IS 'OAuth access/refresh tokens for API calls';
COMMENT ON COLUMN users.oauth_scopes IS 'Granted OAuth scopes (e.g., calendar.readonly)';
COMMENT ON COLUMN users.google_calendar_token IS 'Legacy - will be merged into oauth_tokens';