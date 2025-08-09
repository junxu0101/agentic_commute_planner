-- Sample data for testing the commute planner application
-- Insert sample users
INSERT INTO users (id, email, name, user_preferences) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'john.doe@company.com', 'John Doe', 
     '{"commute_duration_minutes": 45, "preferred_arrival_time": "09:00", "home_location": "Brooklyn, NY"}'),
    ('550e8400-e29b-41d4-a716-446655440002', 'jane.smith@company.com', 'Jane Smith', 
     '{"commute_duration_minutes": 35, "preferred_arrival_time": "10:00", "home_location": "Queens, NY"}'),
    ('550e8400-e29b-41d4-a716-446655440003', 'mike.wilson@company.com', 'Mike Wilson', 
     '{"commute_duration_minutes": 60, "preferred_arrival_time": "08:30", "home_location": "New Jersey"}');

-- Insert sample jobs
INSERT INTO jobs (id, user_id, status, progress, current_step, target_date, input_data) VALUES
    ('650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'IN_PROGRESS', 0.75, 
     'Analyzing calendar events', '2025-08-15', 
     '{"analysis_type": "weekly", "preferences": {"max_commute_days": 3}}'),
    ('650e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 'COMPLETED', 1.0, 
     'Analysis complete', '2025-08-12', 
     '{"analysis_type": "daily", "preferences": {"flexible_hours": true}}'),
    ('650e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', 'PENDING', 0.0, 
     'Initializing', '2025-08-20', 
     '{"analysis_type": "weekly", "preferences": {"early_start": true}}');

-- Insert sample calendar events
INSERT INTO calendar_events (id, user_id, summary, description, start_time, end_time, location, attendees, meeting_type, attendance_mode, google_event_id) VALUES
    ('cal_event_001', '550e8400-e29b-41d4-a716-446655440001', 'Client Presentation - Q3 Results', 
     'Quarterly business review with key client', '2025-08-15 14:00:00-04:00', '2025-08-15 15:30:00-04:00', 
     'Conference Room A', '[{"email": "client@company.com", "name": "Client Rep"}]', 'CLIENT_MEETING', 'MUST_BE_IN_OFFICE', 'google_cal_001'),
    ('cal_event_002', '550e8400-e29b-41d4-a716-446655440001', 'Team Standup', 
     'Daily team sync', '2025-08-15 09:30:00-04:00', '2025-08-15 10:00:00-04:00', 
     'Zoom', '[{"email": "team@company.com", "name": "Development Team"}]', 'STATUS_UPDATE', 'CAN_BE_REMOTE', 'google_cal_002'),
    ('cal_event_003', '550e8400-e29b-41d4-a716-446655440002', 'Product Strategy Workshop', 
     'Planning session for new product features', '2025-08-12 10:00:00-04:00', '2025-08-12 12:00:00-04:00', 
     'Conference Room B', '[{"email": "product@company.com", "name": "Product Team"}]', 'TEAM_WORKSHOP', 'MUST_BE_IN_OFFICE', 'google_cal_003'),
    ('cal_event_004', '550e8400-e29b-41d4-a716-446655440002', 'One-on-One with Manager', 
     'Weekly check-in', '2025-08-12 16:00:00-04:00', '2025-08-12 16:30:00-04:00', 
     'Manager Office', '[{"email": "manager@company.com", "name": "Sarah Manager"}]', 'ONE_ON_ONE', 'FLEXIBLE', 'google_cal_004'),
    ('cal_event_005', '550e8400-e29b-41d4-a716-446655440003', 'Code Review Session', 
     'Review PRs from last sprint', '2025-08-20 11:00:00-04:00', '2025-08-20 12:00:00-04:00', 
     'Hybrid', '[{"email": "dev@company.com", "name": "Dev Team"}]', 'REVIEW', 'CAN_BE_REMOTE', 'google_cal_005'),
    ('cal_event_006', '550e8400-e29b-41d4-a716-446655440003', 'All Hands Meeting', 
     'Monthly company update', '2025-08-20 15:00:00-04:00', '2025-08-20 16:00:00-04:00', 
     'Main Auditorium', '[{"email": "all@company.com", "name": "All Staff"}]', 'STAKEHOLDER_MEETING', 'MUST_BE_IN_OFFICE', 'google_cal_006');

-- Insert sample commute recommendations
INSERT INTO commute_recommendations (id, job_id, option_rank, option_type, commute_start, office_arrival, office_departure, commute_end, office_duration, office_meetings, remote_meetings, business_rule_compliance, reasoning) VALUES
    (uuid_generate_v4(), '650e8400-e29b-41d4-a716-446655440002', 1, 'STRATEGIC_AFTERNOON', 
     '2025-08-12 12:15:00-04:00', '2025-08-12 13:00:00-04:00', '2025-08-12 17:00:00-04:00', '2025-08-12 17:45:00-04:00',
     '4 hours', 
     '[{"event_id": "cal_event_003", "summary": "Product Strategy Workshop", "attendance_required": true}]',
     '[{"event_id": "cal_event_004", "summary": "One-on-One with Manager", "can_be_remote": true}]',
     '{"minimum_stay": {"status": "PASS"}, "core_hours_presence": {"status": "PASS"}}',
     'Optimal for attending critical in-person workshop while maintaining flexibility for other meetings'),
    (uuid_generate_v4(), '650e8400-e29b-41d4-a716-446655440002', 2, 'FULL_REMOTE_RECOMMENDED', 
     NULL, NULL, NULL, NULL, NULL,
     '[]',
     '[{"event_id": "cal_event_003", "summary": "Product Strategy Workshop"}, {"event_id": "cal_event_004", "summary": "One-on-One with Manager"}]',
     '{"flexible_work": {"status": "PASS"}}',
     'All meetings can be handled remotely with proper coordination'),
    (uuid_generate_v4(), '650e8400-e29b-41d4-a716-446655440002', 3, 'FULL_DAY_OFFICE', 
     '2025-08-12 08:00:00-04:00', '2025-08-12 08:45:00-04:00', '2025-08-12 17:30:00-04:00', '2025-08-12 18:15:00-04:00',
     '8 hours 45 minutes', 
     '[{"event_id": "cal_event_003", "summary": "Product Strategy Workshop"}, {"event_id": "cal_event_004", "summary": "One-on-One with Manager"}]',
     '[]',
     '{"minimum_stay": {"status": "PASS"}, "core_hours_presence": {"status": "PASS"}, "extended_presence": {"status": "PASS"}}',
     'Maximum visibility and collaboration opportunity, ideal for important project days');