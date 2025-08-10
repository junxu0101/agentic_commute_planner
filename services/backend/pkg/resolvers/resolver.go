package resolvers

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/commute-planner/backend/pkg/database"
	"github.com/commute-planner/backend/pkg/models"
	"github.com/commute-planner/backend/pkg/redis"
	"github.com/google/uuid"
)

type Resolver struct {
	db          *database.DB
	redisClient *redis.Client
}

func NewResolver(db *database.DB, redisClient *redis.Client) *Resolver {
	return &Resolver{
		db:          db,
		redisClient: redisClient,
	}
}

// Implement ResolverRoot interface
func (r *Resolver) Query() QueryResolver {
	return r
}

func (r *Resolver) Mutation() MutationResolver {
	return r
}

// Define the resolver interfaces
type QueryResolver interface {
	Health(ctx context.Context) (string, error)
	User(ctx context.Context, id string) (*models.User, error)
	Users(ctx context.Context) ([]*models.User, error)
	Job(ctx context.Context, id string) (*models.Job, error)
	Jobs(ctx context.Context, userID *string) ([]*models.Job, error)
	CalendarEvents(ctx context.Context, userID string, targetDate *string) ([]*models.CalendarEvent, error)
	CommuteRecommendations(ctx context.Context, jobID string) ([]*models.CommuteRecommendation, error)
}

type MutationResolver interface {
	CreateUser(ctx context.Context, input CreateUserInput) (*models.User, error)
	UpdateUser(ctx context.Context, id string, input UpdateUserInput) (*models.User, error)
	DeleteUser(ctx context.Context, id string) (bool, error)
	CreateJob(ctx context.Context, input CreateJobInput) (*models.Job, error)
	UpdateJob(ctx context.Context, id string, input UpdateJobInput) (*models.Job, error)
	DeleteJob(ctx context.Context, id string) (bool, error)
}

// Health check
func (r *Resolver) Health(ctx context.Context) (string, error) {
	return "OK", nil
}

// QueueJob adds a job to the Redis queue for processing
func (r *Resolver) QueueJob(ctx context.Context, jobData map[string]interface{}) error {
	jobID := jobData["job_id"].(string)
	userID := jobData["user_id"].(string)
	targetDate := jobData["target_date"].(string)
	
	var inputData *string
	if data, exists := jobData["input_data"]; exists && data != nil {
		dataStr := data.(string)
		inputData = &dataStr
	}
	
	return r.redisClient.AddJobToQueue(ctx, jobID, userID, targetDate, inputData)
}

// User resolvers
func (r *Resolver) User(ctx context.Context, id string) (*models.User, error) {
	query := `SELECT id, email, name, user_preferences, created_at, updated_at FROM users WHERE id = $1`
	
	user := &models.User{}
	err := r.db.QueryRow(query, id).Scan(
		&user.ID,
		&user.Email,
		&user.Name,
		&user.UserPreferences,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("user not found")
		}
		return nil, fmt.Errorf("error fetching user: %w", err)
	}
	
	return user, nil
}

func (r *Resolver) Users(ctx context.Context) ([]*models.User, error) {
	query := `SELECT id, email, name, user_preferences, created_at, updated_at FROM users ORDER BY created_at DESC`
	
	rows, err := r.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("error fetching users: %w", err)
	}
	defer rows.Close()
	
	var users []*models.User
	for rows.Next() {
		user := &models.User{}
		err := rows.Scan(
			&user.ID,
			&user.Email,
			&user.Name,
			&user.UserPreferences,
			&user.CreatedAt,
			&user.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("error scanning user: %w", err)
		}
		users = append(users, user)
	}
	
	return users, nil
}

type CreateUserInput struct {
	Email           string  `json:"email"`
	Name            string  `json:"name"`
	UserPreferences *string `json:"userPreferences"`
}

func (r *Resolver) CreateUser(ctx context.Context, input CreateUserInput) (*models.User, error) {
	id := uuid.New().String()
	now := time.Now()
	
	query := `INSERT INTO users (id, email, name, user_preferences, created_at, updated_at) 
	          VALUES ($1, $2, $3, $4, $5, $6) 
	          RETURNING id, email, name, user_preferences, created_at, updated_at`
	
	user := &models.User{}
	err := r.db.QueryRow(query, id, input.Email, input.Name, input.UserPreferences, now, now).Scan(
		&user.ID,
		&user.Email,
		&user.Name,
		&user.UserPreferences,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	
	if err != nil {
		return nil, fmt.Errorf("error creating user: %w", err)
	}
	
	return user, nil
}

type UpdateUserInput struct {
	Email           *string `json:"email"`
	Name            *string `json:"name"`
	UserPreferences *string `json:"userPreferences"`
}

func (r *Resolver) UpdateUser(ctx context.Context, id string, input UpdateUserInput) (*models.User, error) {
	query := `UPDATE users SET updated_at = NOW()`
	args := []interface{}{}
	argIndex := 1
	
	if input.Email != nil {
		query += fmt.Sprintf(", email = $%d", argIndex)
		args = append(args, *input.Email)
		argIndex++
	}
	if input.Name != nil {
		query += fmt.Sprintf(", name = $%d", argIndex)
		args = append(args, *input.Name)
		argIndex++
	}
	if input.UserPreferences != nil {
		query += fmt.Sprintf(", user_preferences = $%d", argIndex)
		args = append(args, *input.UserPreferences)
		argIndex++
	}
	
	query += fmt.Sprintf(" WHERE id = $%d RETURNING id, email, name, user_preferences, created_at, updated_at", argIndex)
	args = append(args, id)
	
	user := &models.User{}
	err := r.db.QueryRow(query, args...).Scan(
		&user.ID,
		&user.Email,
		&user.Name,
		&user.UserPreferences,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("user not found")
		}
		return nil, fmt.Errorf("error updating user: %w", err)
	}
	
	return user, nil
}

func (r *Resolver) DeleteUser(ctx context.Context, id string) (bool, error) {
	query := `DELETE FROM users WHERE id = $1`
	
	result, err := r.db.Exec(query, id)
	if err != nil {
		return false, fmt.Errorf("error deleting user: %w", err)
	}
	
	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return false, fmt.Errorf("error getting rows affected: %w", err)
	}
	
	return rowsAffected > 0, nil
}

// Job resolvers
func (r *Resolver) Job(ctx context.Context, id string) (*models.Job, error) {
	query := `SELECT id, user_id, status, progress, current_step, target_date, input_data, result, error_message, created_at, updated_at 
	          FROM jobs WHERE id = $1`
	
	job := &models.Job{}
	err := r.db.QueryRow(query, id).Scan(
		&job.ID,
		&job.UserID,
		&job.Status,
		&job.Progress,
		&job.CurrentStep,
		&job.TargetDate,
		&job.InputData,
		&job.Result,
		&job.ErrorMessage,
		&job.CreatedAt,
		&job.UpdatedAt,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("job not found")
		}
		return nil, fmt.Errorf("error fetching job: %w", err)
	}
	
	return job, nil
}

func (r *Resolver) Jobs(ctx context.Context, userID *string) ([]*models.Job, error) {
	var query string
	var args []interface{}
	
	if userID != nil {
		query = `SELECT id, user_id, status, progress, current_step, target_date, input_data, result, error_message, created_at, updated_at 
		         FROM jobs WHERE user_id = $1 ORDER BY created_at DESC`
		args = append(args, *userID)
	} else {
		query = `SELECT id, user_id, status, progress, current_step, target_date, input_data, result, error_message, created_at, updated_at 
		         FROM jobs ORDER BY created_at DESC`
	}
	
	rows, err := r.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("error fetching jobs: %w", err)
	}
	defer rows.Close()
	
	var jobs []*models.Job
	for rows.Next() {
		job := &models.Job{}
		err := rows.Scan(
			&job.ID,
			&job.UserID,
			&job.Status,
			&job.Progress,
			&job.CurrentStep,
			&job.TargetDate,
			&job.InputData,
			&job.Result,
			&job.ErrorMessage,
			&job.CreatedAt,
			&job.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("error scanning job: %w", err)
		}
		jobs = append(jobs, job)
	}
	
	return jobs, nil
}

type CreateJobInput struct {
	UserID     string  `json:"userId"`
	TargetDate string  `json:"targetDate"`
	InputData  *string `json:"inputData"`
}

func (r *Resolver) CreateJob(ctx context.Context, input CreateJobInput) (*models.Job, error) {
	id := uuid.New().String()
	now := time.Now()
	
	// Handle JSON input data - pass JSON string directly to PostgreSQL
	var inputDataJSON interface{}
	if input.InputData != nil && *input.InputData != "" {
		// InputData is already a JSON string from frontend, pass it directly
		inputDataJSON = *input.InputData
	}
	
	query := `INSERT INTO jobs (id, user_id, status, progress, target_date, input_data, created_at, updated_at) 
	          VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
	          RETURNING id, user_id, status, progress, current_step, target_date, input_data, result, error_message, created_at, updated_at`
	
	job := &models.Job{}
	err := r.db.QueryRow(query, id, input.UserID, models.JobStatusPending, 0.0, input.TargetDate, inputDataJSON, now, now).Scan(
		&job.ID,
		&job.UserID,
		&job.Status,
		&job.Progress,
		&job.CurrentStep,
		&job.TargetDate,
		&job.InputData,
		&job.Result,
		&job.ErrorMessage,
		&job.CreatedAt,
		&job.UpdatedAt,
	)
	
	if err != nil {
		return nil, fmt.Errorf("error creating job: %w", err)
	}
	
	// Note: Job queueing to Redis is handled in main.go after successful GraphQL mutation
	// to avoid duplicate queueing
	
	return job, nil
}

type UpdateJobInput struct {
	Status       *string  `json:"status"`
	Progress     *float64 `json:"progress"`
	CurrentStep  *string  `json:"currentStep"`
	Result       *string  `json:"result"`
	ErrorMessage *string  `json:"errorMessage"`
}

func (r *Resolver) UpdateJob(ctx context.Context, id string, input UpdateJobInput) (*models.Job, error) {
	query := `UPDATE jobs SET updated_at = NOW()`
	args := []interface{}{}
	argIndex := 1
	
	if input.Status != nil {
		query += fmt.Sprintf(", status = $%d", argIndex)
		args = append(args, *input.Status)
		argIndex++
	}
	if input.Progress != nil {
		query += fmt.Sprintf(", progress = $%d", argIndex)
		args = append(args, *input.Progress)
		argIndex++
	}
	if input.CurrentStep != nil {
		query += fmt.Sprintf(", current_step = $%d", argIndex)
		args = append(args, *input.CurrentStep)
		argIndex++
	}
	if input.Result != nil {
		query += fmt.Sprintf(", result = $%d", argIndex)
		args = append(args, *input.Result)
		argIndex++
	}
	if input.ErrorMessage != nil {
		query += fmt.Sprintf(", error_message = $%d", argIndex)
		args = append(args, *input.ErrorMessage)
		argIndex++
	}
	
	query += fmt.Sprintf(" WHERE id = $%d RETURNING id, user_id, status, progress, current_step, target_date, input_data, result, error_message, created_at, updated_at", argIndex)
	args = append(args, id)
	
	job := &models.Job{}
	err := r.db.QueryRow(query, args...).Scan(
		&job.ID,
		&job.UserID,
		&job.Status,
		&job.Progress,
		&job.CurrentStep,
		&job.TargetDate,
		&job.InputData,
		&job.Result,
		&job.ErrorMessage,
		&job.CreatedAt,
		&job.UpdatedAt,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("job not found")
		}
		return nil, fmt.Errorf("error updating job: %w", err)
	}
	
	return job, nil
}

func (r *Resolver) DeleteJob(ctx context.Context, id string) (bool, error) {
	query := `DELETE FROM jobs WHERE id = $1`
	
	result, err := r.db.Exec(query, id)
	if err != nil {
		return false, fmt.Errorf("error deleting job: %w", err)
	}
	
	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return false, fmt.Errorf("error getting rows affected: %w", err)
	}
	
	return rowsAffected > 0, nil
}

// CalendarEvent resolvers
func (r *Resolver) CalendarEvents(ctx context.Context, userID string, targetDate *string) ([]*models.CalendarEvent, error) {
	var query string
	var args []interface{}
	
	if targetDate != nil {
		// Filter by specific date - events that start or occur on the target date
		// Parse the target date and match events that fall on that day
		query = `SELECT id, user_id, summary, description, start_time, end_time, location, attendees, meeting_type, attendance_mode, is_all_day, is_recurring, google_event_id, created_at, updated_at 
		         FROM calendar_events 
		         WHERE user_id = $1 AND DATE(start_time) = $2::date
		         ORDER BY start_time ASC`
		args = []interface{}{userID, (*targetDate)[:10]} // Extract just YYYY-MM-DD part
	} else {
		// No date filter - return all user events
		query = `SELECT id, user_id, summary, description, start_time, end_time, location, attendees, meeting_type, attendance_mode, is_all_day, is_recurring, google_event_id, created_at, updated_at 
		         FROM calendar_events WHERE user_id = $1 ORDER BY start_time ASC`
		args = []interface{}{userID}
	}
	
	rows, err := r.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("error fetching calendar events: %w", err)
	}
	defer rows.Close()
	
	var events []*models.CalendarEvent
	for rows.Next() {
		event := &models.CalendarEvent{}
		err := rows.Scan(
			&event.ID,
			&event.UserID,
			&event.Summary,
			&event.Description,
			&event.StartTime,
			&event.EndTime,
			&event.Location,
			&event.Attendees,
			&event.MeetingType,
			&event.AttendanceMode,
			&event.IsAllDay,
			&event.IsRecurring,
			&event.GoogleEventID,
			&event.CreatedAt,
			&event.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("error scanning calendar event: %w", err)
		}
		events = append(events, event)
	}
	
	return events, nil
}

// CommuteRecommendation resolvers
func (r *Resolver) CommuteRecommendations(ctx context.Context, jobID string) ([]*models.CommuteRecommendation, error) {
	query := `SELECT id, job_id, option_rank, option_type, commute_start, office_arrival, office_departure, commute_end, office_duration, office_meetings, remote_meetings, business_rule_compliance, perception_analysis, reasoning, trade_offs, created_at 
	          FROM commute_recommendations WHERE job_id = $1 ORDER BY option_rank ASC`
	
	rows, err := r.db.Query(query, jobID)
	if err != nil {
		return nil, fmt.Errorf("error fetching commute recommendations: %w", err)
	}
	defer rows.Close()
	
	var recommendations []*models.CommuteRecommendation
	for rows.Next() {
		rec := &models.CommuteRecommendation{}
		err := rows.Scan(
			&rec.ID,
			&rec.JobID,
			&rec.OptionRank,
			&rec.OptionType,
			&rec.CommuteStart,
			&rec.OfficeArrival,
			&rec.OfficeDeparture,
			&rec.CommuteEnd,
			&rec.OfficeDuration,
			&rec.OfficeMeetings,
			&rec.RemoteMeetings,
			&rec.BusinessRuleCompliance,
			&rec.PerceptionAnalysis,
			&rec.Reasoning,
			&rec.TradeOffs,
			&rec.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("error scanning commute recommendation: %w", err)
		}
		recommendations = append(recommendations, rec)
	}
	
	return recommendations, nil
}