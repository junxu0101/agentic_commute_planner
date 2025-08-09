package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"time"

	"github.com/commute-planner/backend/pkg/database"
	"github.com/commute-planner/backend/pkg/models"
	"github.com/google/uuid"
)

// DemoHandler handles demo data generation
type DemoHandler struct {
	db *database.DB
}

// NewDemoHandler creates a new demo handler
func NewDemoHandler(db *database.DB) *DemoHandler {
	return &DemoHandler{db: db}
}

// DemoResponse represents the demo generation response
type DemoResponse struct {
	Success bool                    `json:"success"`
	Message string                  `json:"message"`
	Data    *DemoGenerationResult   `json:"data,omitempty"`
	Error   string                  `json:"error,omitempty"`
}

// DemoGenerationResult contains generated demo data stats
type DemoGenerationResult struct {
	CalendarEventsGenerated int                      `json:"calendarEventsGenerated"`
	Events                  []*models.CalendarEvent  `json:"events"`
	UserID                  string                   `json:"userId"`
	DateRange               string                   `json:"dateRange"`
}

// Meeting templates for realistic scenarios
type MeetingTemplate struct {
	Summary          string  `json:"summary"`
	MeetingType      string  `json:"meetingType"`
	AttendanceMode   string  `json:"attendanceMode"`
	DurationHours    float64 `json:"durationHours"`
	Attendees        int     `json:"attendees"`
	Description      string  `json:"description"`
}

// Smart meeting templates with business logic
var meetingTemplates = []MeetingTemplate{
	// Must be in-office meetings (high impact)
	{
		Summary:        "Q4 Client Presentation - Acme Corp",
		MeetingType:    "CLIENT_MEETING",
		AttendanceMode: "MUST_BE_IN_OFFICE", 
		DurationHours:  2.0,
		Attendees:      8,
		Description:    "Quarterly business review with Acme Corp leadership team",
	},
	{
		Summary:        "Product Demo - Enterprise Customer",
		MeetingType:    "PRESENTATION",
		AttendanceMode: "MUST_BE_IN_OFFICE",
		DurationHours:  1.5,
		Attendees:      6,
		Description:    "Live product demonstration for potential enterprise customer",
	},
	{
		Summary:        "Team Workshop - Sprint Planning",
		MeetingType:    "TEAM_WORKSHOP", 
		AttendanceMode: "MUST_BE_IN_OFFICE",
		DurationHours:  3.0,
		Attendees:      12,
		Description:    "In-person collaborative sprint planning session",
	},
	{
		Summary:        "Senior Engineer Interview",
		MeetingType:    "INTERVIEW",
		AttendanceMode: "MUST_BE_IN_OFFICE",
		DurationHours:  4.0,
		Attendees:      4,
		Description:    "On-site technical interview with candidate",
	},
	// Can be remote meetings (flexible)
	{
		Summary:        "Daily Standup",
		MeetingType:    "CHECK_IN",
		AttendanceMode: "CAN_BE_REMOTE",
		DurationHours:  0.5,
		Attendees:      8,
		Description:    "Daily team sync and progress update",
	},
	{
		Summary:        "1:1 with Manager",
		MeetingType:    "ONE_ON_ONE",
		AttendanceMode: "CAN_BE_REMOTE",
		DurationHours:  1.0,
		Attendees:      2,
		Description:    "Weekly one-on-one check-in",
	},
	{
		Summary:        "Code Review Session",
		MeetingType:    "REVIEW",
		AttendanceMode: "CAN_BE_REMOTE",
		DurationHours:  1.5,
		Attendees:      4,
		Description:    "Technical code review and discussion",
	},
	{
		Summary:        "Project Status Update",
		MeetingType:    "STATUS_UPDATE",
		AttendanceMode: "CAN_BE_REMOTE",
		DurationHours:  1.0,
		Attendees:      6,
		Description:    "Weekly project progress review",
	},
	// Brainstorming sessions
	{
		Summary:        "Feature Brainstorming - Mobile App",
		MeetingType:    "BRAINSTORMING",
		AttendanceMode: "FLEXIBLE",
		DurationHours:  2.0,
		Attendees:      5,
		Description:    "Creative session for new mobile features",
	},
}

// GenerateDemoData creates realistic calendar events for the authenticated user
func (h *DemoHandler) GenerateDemoData(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Get authenticated user from context
	user := GetUserFromContext(r.Context())
	if user == nil {
		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(DemoResponse{
			Success: false,
			Error:   "Authentication required",
		})
		return
	}

	// Clear existing calendar events for this user (demo data only)
	_, err := h.db.Exec("DELETE FROM calendar_events WHERE user_id = $1", user.ID)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(DemoResponse{
			Success: false,
			Error:   "Failed to clear existing events",
		})
		return
	}

	// Generate smart calendar events
	events, err := h.generateSmartCalendarEvents(r.Context(), user.ID)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(DemoResponse{
			Success: false,
			Error:   fmt.Sprintf("Failed to generate demo data: %v", err),
		})
		return
	}

	json.NewEncoder(w).Encode(DemoResponse{
		Success: true,
		Message: fmt.Sprintf("Generated %d realistic calendar events for demo purposes", len(events)),
		Data: &DemoGenerationResult{
			CalendarEventsGenerated: len(events),
			Events:                  events,
			UserID:                  user.ID,
			DateRange:               "Next 14 days with smart business scenarios",
		},
	})
}

// generateSmartCalendarEvents creates intelligent, realistic calendar scenarios
func (h *DemoHandler) generateSmartCalendarEvents(ctx context.Context, userID string) ([]*models.CalendarEvent, error) {
	var events []*models.CalendarEvent
	now := time.Now()
	
	// Generate events for next 14 days (realistic planning window)
	for dayOffset := 0; dayOffset < 14; dayOffset++ {
		targetDate := now.AddDate(0, 0, dayOffset)
		
		// Skip weekends for most business events
		if targetDate.Weekday() == time.Saturday || targetDate.Weekday() == time.Sunday {
			continue
		}
		
		// Smart event density based on day of week
		eventCount := h.getSmartEventCount(targetDate)
		
		dayEvents := h.generateDayEvents(ctx, userID, targetDate, eventCount)
		events = append(events, dayEvents...)
	}
	
	// Insert all events into database
	for _, event := range events {
		err := h.insertCalendarEvent(ctx, event)
		if err != nil {
			return nil, fmt.Errorf("failed to insert event: %w", err)
		}
	}
	
	return events, nil
}

// getSmartEventCount returns realistic number of meetings per day
func (h *DemoHandler) getSmartEventCount(date time.Time) int {
	switch date.Weekday() {
	case time.Monday, time.Tuesday: // Busy start of week
		return rand.Intn(4) + 3 // 3-6 events
	case time.Wednesday, time.Thursday: // Peak productivity
		return rand.Intn(3) + 4 // 4-6 events  
	case time.Friday: // Lighter Friday
		return rand.Intn(3) + 2 // 2-4 events
	default:
		return 0 // Weekends
	}
}

// generateDayEvents creates events for a specific day with business logic
func (h *DemoHandler) generateDayEvents(ctx context.Context, userID string, date time.Time, eventCount int) []*models.CalendarEvent {
	var dayEvents []*models.CalendarEvent
	usedTimes := make(map[int]bool) // Track used hour slots
	
	for i := 0; i < eventCount; i++ {
		// Smart time slot selection (business hours 8 AM - 6 PM)
		hour := h.getAvailableTimeSlot(usedTimes)
		if hour == -1 {
			break // No more available slots
		}
		
		// Select appropriate meeting template
		template := meetingTemplates[rand.Intn(len(meetingTemplates))]
		
		startTime := time.Date(date.Year(), date.Month(), date.Day(), hour, 0, 0, 0, time.UTC)
		endTime := startTime.Add(time.Duration(template.DurationHours * float64(time.Hour)))
		
		// Create realistic calendar event
		event := &models.CalendarEvent{
			ID:             uuid.New().String(),
			UserID:         userID,
			Summary:        template.Summary,
			Description:    &template.Description,
			StartTime:      startTime,
			EndTime:        endTime,
			Location:       h.getSmartLocation(template.AttendanceMode),
			Attendees:      h.getAttendeesJSON(template.Attendees),
			MeetingType:    models.MeetingType(template.MeetingType),
			AttendanceMode: models.AttendanceMode(template.AttendanceMode),
			IsAllDay:       false,
			IsRecurring:    rand.Float32() < 0.2, // 20% recurring
			GoogleEventID:  nil, // Demo data
			CreatedAt:      time.Now(),
			UpdatedAt:      time.Now(),
		}
		
		dayEvents = append(dayEvents, event)
		
		// Mark time slots as used
		duration := int(template.DurationHours)
		for j := 0; j <= duration; j++ {
			usedTimes[hour+j] = true
		}
	}
	
	return dayEvents
}

// getAvailableTimeSlot finds an available business hour
func (h *DemoHandler) getAvailableTimeSlot(usedTimes map[int]bool) int {
	businessHours := []int{8, 9, 10, 11, 13, 14, 15, 16, 17} // Skip lunch at 12
	
	// Shuffle for randomness
	rand.Shuffle(len(businessHours), func(i, j int) {
		businessHours[i], businessHours[j] = businessHours[j], businessHours[i]
	})
	
	for _, hour := range businessHours {
		if !usedTimes[hour] {
			return hour
		}
	}
	return -1 // No available slots
}

// getSmartLocation returns appropriate location based on attendance mode
func (h *DemoHandler) getSmartLocation(attendanceMode string) *string {
	locations := map[string][]string{
		"MUST_BE_IN_OFFICE": {"Conference Room A", "Boardroom", "Training Room", "Client Meeting Room"},
		"CAN_BE_REMOTE":     {"Zoom", "Google Meet", "Teams", "Conference Room B (optional)"},
		"FLEXIBLE":          {"Brainstorm Space", "Open Collaboration Area", "Zoom", "Innovation Lab"},
	}
	
	options := locations[attendanceMode]
	if len(options) == 0 {
		return nil
	}
	
	location := options[rand.Intn(len(options))]
	return &location
}

// getAttendeesJSON creates realistic attendees JSON
func (h *DemoHandler) getAttendeesJSON(count int) *string {
	attendees := make([]string, count)
	names := []string{"John Doe", "Jane Smith", "Mike Johnson", "Sarah Wilson", "David Brown", "Emily Davis", "Chris Martinez", "Lisa Anderson"}
	
	for i := 0; i < count && i < len(names); i++ {
		attendees[i] = names[i]
	}
	
	attendeesJSON, _ := json.Marshal(attendees)
	result := string(attendeesJSON)
	return &result
}

// insertCalendarEvent saves event to database
func (h *DemoHandler) insertCalendarEvent(ctx context.Context, event *models.CalendarEvent) error {
	query := `INSERT INTO calendar_events (id, user_id, summary, description, start_time, end_time, location, attendees, meeting_type, attendance_mode, is_all_day, is_recurring, google_event_id, created_at, updated_at)
	          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)`
	
	_, err := h.db.Exec(query,
		event.ID,
		event.UserID,
		event.Summary,
		event.Description,
		event.StartTime,
		event.EndTime,
		event.Location,
		event.Attendees,
		event.MeetingType,
		event.AttendanceMode,
		event.IsAllDay,
		event.IsRecurring,
		event.GoogleEventID,
		event.CreatedAt,
		event.UpdatedAt,
	)
	
	return err
}

// CheckDemoData returns whether user has existing calendar events
func (h *DemoHandler) CheckDemoData(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	if r.Method != "GET" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Get authenticated user from context
	user := GetUserFromContext(r.Context())
	if user == nil {
		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(DemoResponse{
			Success: false,
			Error:   "Authentication required",
		})
		return
	}

	// Count calendar events for this user
	var count int
	err := h.db.QueryRow("SELECT COUNT(*) FROM calendar_events WHERE user_id = $1", user.ID).Scan(&count)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(DemoResponse{
			Success: false,
			Error:   "Failed to check calendar events",
		})
		return
	}

	response := map[string]interface{}{
		"success": true,
		"hasData": count > 0,
		"eventCount": count,
	}

	json.NewEncoder(w).Encode(response)
}