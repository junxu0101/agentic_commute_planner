-- Migration: 001_initial_setup
-- Description: Initial database schema setup with all core tables and types
-- Created: 2025-08-07

-- Create enum types
CREATE TYPE job_status AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED');
CREATE TYPE commute_option_type AS ENUM ('FULL_DAY_OFFICE', 'STRATEGIC_AFTERNOON', 'FULL_REMOTE_RECOMMENDED');
CREATE TYPE professional_impact AS ENUM ('VERY_POSITIVE', 'NEUTRAL_TO_POSITIVE', 'NEUTRAL', 'SLIGHTLY_NEGATIVE', 'NEGATIVE');
CREATE TYPE team_visibility AS ENUM ('HIGH', 'MEDIUM', 'LOW');
CREATE TYPE meeting_type AS ENUM ('CLIENT_MEETING', 'PRESENTATION', 'TEAM_WORKSHOP', 'INTERVIEW', 'STAKEHOLDER_MEETING', 'ONE_ON_ONE', 'STATUS_UPDATE', 'REVIEW', 'BRAINSTORMING', 'CHECK_IN', 'UNKNOWN');
CREATE TYPE attendance_mode AS ENUM ('MUST_BE_IN_OFFICE', 'CAN_BE_REMOTE', 'FLEXIBLE');

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    google_calendar_token JSONB,
    user_preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs table for tracking commute analysis jobs
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status job_status DEFAULT 'PENDING',
    progress FLOAT DEFAULT 0.0,
    current_step VARCHAR(255),
    target_date DATE NOT NULL,
    input_data JSONB,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calendar events table
CREATE TABLE calendar_events (
    id VARCHAR(255) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    summary VARCHAR(500) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(255),
    attendees JSONB DEFAULT '[]',
    meeting_type meeting_type DEFAULT 'UNKNOWN',
    attendance_mode attendance_mode DEFAULT 'FLEXIBLE',
    is_all_day BOOLEAN DEFAULT FALSE,
    is_recurring BOOLEAN DEFAULT FALSE,
    google_event_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Commute recommendations table
CREATE TABLE commute_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    option_rank INTEGER NOT NULL,
    option_type commute_option_type NOT NULL,
    commute_start TIMESTAMP WITH TIME ZONE,
    office_arrival TIMESTAMP WITH TIME ZONE,
    office_departure TIMESTAMP WITH TIME ZONE,
    commute_end TIMESTAMP WITH TIME ZONE,
    office_duration INTERVAL,
    office_meetings JSONB DEFAULT '[]',
    remote_meetings JSONB DEFAULT '[]',
    business_rule_compliance JSONB,
    perception_analysis JSONB,
    reasoning TEXT,
    trade_offs JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_target_date ON jobs(target_date);
CREATE INDEX idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX idx_calendar_events_start_time ON calendar_events(start_time);
CREATE INDEX idx_calendar_events_meeting_type ON calendar_events(meeting_type);
CREATE INDEX idx_commute_recommendations_job_id ON commute_recommendations(job_id);
CREATE INDEX idx_commute_recommendations_rank ON commute_recommendations(option_rank);