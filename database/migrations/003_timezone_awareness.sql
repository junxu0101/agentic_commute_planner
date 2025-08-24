-- Migration to add timezone awareness to the database
-- This ensures all timestamps are stored with timezone information

BEGIN;

-- Update calendar_events table to use timestamptz
ALTER TABLE calendar_events 
ALTER COLUMN start_time TYPE timestamptz USING start_time AT TIME ZONE 'UTC',
ALTER COLUMN end_time TYPE timestamptz USING end_time AT TIME ZONE 'UTC',
ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC',
ALTER COLUMN updated_at TYPE timestamptz USING updated_at AT TIME ZONE 'UTC';

-- Update jobs table to use timestamptz  
ALTER TABLE jobs
ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC',
ALTER COLUMN updated_at TYPE timestamptz USING updated_at AT TIME ZONE 'UTC';

-- Update users table to use timestamptz
ALTER TABLE users 
ALTER COLUMN created_at TYPE timestamptz USING created_at AT TIME ZONE 'UTC',
ALTER COLUMN updated_at TYPE timestamptz USING updated_at AT TIME ZONE 'UTC';

-- Update last_login if it exists
ALTER TABLE users 
ALTER COLUMN last_login TYPE timestamptz USING last_login AT TIME ZONE 'UTC';

-- Add timezone column to users table for storing user's preferred timezone
ALTER TABLE users ADD COLUMN preferred_timezone VARCHAR(50) DEFAULT 'UTC';

-- Add index on calendar_events start_time for better query performance
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_time_tz ON calendar_events (start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_date ON calendar_events (user_id, start_time);

COMMIT;