-- Migration: 002_functions_and_triggers
-- Description: Database functions and triggers for automated operations
-- Created: 2025-08-08

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at columns
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_calendar_events_updated_at
    BEFORE UPDATE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to validate business rules for commute options
CREATE OR REPLACE FUNCTION validate_commute_option(
    office_arrival TIMESTAMP WITH TIME ZONE,
    office_departure TIMESTAMP WITH TIME ZONE
) RETURNS JSONB AS $$
DECLARE
    duration INTERVAL;
    arrival_hour INTEGER;
    departure_hour INTEGER;
    validation_result JSONB;
BEGIN
    -- Calculate office duration
    duration := office_departure - office_arrival;
    
    -- Extract hours for validation
    arrival_hour := EXTRACT(HOUR FROM office_arrival);
    departure_hour := EXTRACT(HOUR FROM office_departure);
    
    -- Initialize validation result
    validation_result := jsonb_build_object();
    
    -- Minimum stay validation (4+ hours)
    IF duration >= INTERVAL '4 hours' THEN
        validation_result := validation_result || jsonb_build_object(
            'minimum_stay', 
            jsonb_build_object(
                'status', 'PASS',
                'message', format('Duration %s meets minimum 4 hours', duration)
            )
        );
    ELSE
        validation_result := validation_result || jsonb_build_object(
            'minimum_stay', 
            jsonb_build_object(
                'status', 'FAIL',
                'message', format('Duration %s below minimum 4 hours', duration)
            )
        );
    END IF;
    
    -- Arrival pattern validation
    IF arrival_hour < 10 THEN
        validation_result := validation_result || jsonb_build_object(
            'arrival_pattern',
            jsonb_build_object(
                'status', 'PASS',
                'message', 'Early arrival shows dedication'
            )
        );
    ELSIF arrival_hour >= 13 THEN
        validation_result := validation_result || jsonb_build_object(
            'arrival_pattern',
            jsonb_build_object(
                'status', 'PASS',
                'message', 'Post-lunch arrival acceptable'
            )
        );
    ELSE
        validation_result := validation_result || jsonb_build_object(
            'arrival_pattern',
            jsonb_build_object(
                'status', 'WARNING',
                'message', 'Mid-morning arrival less optimal'
            )
        );
    END IF;
    
    -- Core hours presence validation (10 AM - 4 PM)
    IF arrival_hour <= 10 AND departure_hour >= 16 THEN
        validation_result := validation_result || jsonb_build_object(
            'core_hours_presence',
            jsonb_build_object(
                'status', 'PASS',
                'message', 'Present during core collaboration hours'
            )
        );
    ELSE
        validation_result := validation_result || jsonb_build_object(
            'core_hours_presence',
            jsonb_build_object(
                'status', 'WARNING',
                'message', 'Limited core hours presence'
            )
        );
    END IF;
    
    RETURN validation_result;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate commute metrics
CREATE OR REPLACE FUNCTION calculate_commute_metrics(
    commute_start TIMESTAMP WITH TIME ZONE,
    office_arrival TIMESTAMP WITH TIME ZONE,
    office_departure TIMESTAMP WITH TIME ZONE,
    commute_end TIMESTAMP WITH TIME ZONE
) RETURNS JSONB AS $$
DECLARE
    total_commute_time INTERVAL;
    office_duration INTERVAL;
    total_day_duration INTERVAL;
    metrics JSONB;
BEGIN
    -- Calculate intervals
    total_commute_time := (office_arrival - commute_start) + (commute_end - office_departure);
    office_duration := office_departure - office_arrival;
    total_day_duration := commute_end - commute_start;
    
    -- Build metrics object
    metrics := jsonb_build_object(
        'total_commute_time', EXTRACT(EPOCH FROM total_commute_time) / 60, -- minutes
        'office_duration', EXTRACT(EPOCH FROM office_duration) / 60, -- minutes
        'total_day_duration', EXTRACT(EPOCH FROM total_day_duration) / 60, -- minutes
        'commute_to_office_ratio', 
            ROUND((EXTRACT(EPOCH FROM total_commute_time) / EXTRACT(EPOCH FROM office_duration))::NUMERIC, 2),
        'efficiency_score',
            ROUND((EXTRACT(EPOCH FROM office_duration) / EXTRACT(EPOCH FROM total_day_duration))::NUMERIC, 2)
    );
    
    RETURN metrics;
END;
$$ LANGUAGE plpgsql;

-- Function to update job progress
CREATE OR REPLACE FUNCTION update_job_progress(
    job_uuid UUID,
    new_status job_status DEFAULT NULL,
    new_progress FLOAT DEFAULT NULL,
    new_current_step VARCHAR(255) DEFAULT NULL,
    error_msg TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE jobs
    SET 
        status = COALESCE(new_status, status),
        progress = COALESCE(new_progress, progress),
        current_step = COALESCE(new_current_step, current_step),
        error_message = COALESCE(error_msg, error_message),
        updated_at = NOW()
    WHERE id = job_uuid;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- View for job progress monitoring
CREATE OR REPLACE VIEW job_progress_view AS
SELECT 
    j.id,
    j.user_id,
    j.status,
    j.progress,
    j.current_step,
    j.target_date,
    j.created_at,
    j.updated_at,
    u.email as user_email,
    u.name as user_name,
    COUNT(cr.id) as recommendation_count
FROM jobs j
LEFT JOIN users u ON j.user_id = u.id
LEFT JOIN commute_recommendations cr ON j.id = cr.job_id
GROUP BY j.id, u.email, u.name;