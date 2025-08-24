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
	// Must be in-person meetings (location-specific)
	{
		Summary:        "Onsite Client Presentation - Acme Corp Office",
		MeetingType:    "CLIENT_MEETING",
		AttendanceMode: "MUST_BE_IN_PERSON", 
		DurationHours:  2.0,
		Attendees:      8,
		Description:    "In-person quarterly review at client's downtown office",
	},
	{
		Summary:        "Onsite Interview - Senior Engineer",
		MeetingType:    "INTERVIEW",
		AttendanceMode: "MUST_BE_IN_PERSON",
		DurationHours:  1.5,
		Attendees:      4,
		Description:    "On-site technical interview with candidate",
	},
	{
		Summary:        "Hands-on Lab Session - Hardware Testing",
		MeetingType:    "WORKSHOP",
		AttendanceMode: "MUST_BE_IN_PERSON",
		DurationHours:  3.0,
		Attendees:      6,
		Description:    "Physical hardware testing requiring lab equipment",
	},
	// Remote meetings requiring video
	{
		Summary:        "Client Presentation - Remote Demo",
		MeetingType:    "CLIENT_MEETING",
		AttendanceMode: "REMOTE_WITH_VIDEO",
		DurationHours:  1.5,
		Attendees:      6,
		Description:    "Product demonstration via video conference",
	},
	{
		Summary:        "Remote Interview - Product Manager",
		MeetingType:    "INTERVIEW",
		AttendanceMode: "REMOTE_WITH_VIDEO",
		DurationHours:  1.0,
		Attendees:      3,
		Description:    "Video interview for product manager role",
	},
	{
		Summary:        "Team Workshop - Sprint Planning",
		MeetingType:    "TEAM_WORKSHOP", 
		AttendanceMode: "REMOTE_WITH_VIDEO",
		DurationHours:  2.0,
		Attendees:      8,
		Description:    "Interactive sprint planning session",
	},
	{
		Summary:        "1:1 with Manager",
		MeetingType:    "ONE_ON_ONE",
		AttendanceMode: "REMOTE_WITH_VIDEO",
		DurationHours:  1.0,
		Attendees:      2,
		Description:    "Weekly one-on-one check-in",
	},
	{
		Summary:        "Code Review Session",
		MeetingType:    "REVIEW",
		AttendanceMode: "REMOTE_WITH_VIDEO",
		DurationHours:  1.5,
		Attendees:      4,
		Description:    "Technical code review and discussion",
	},
	{
		Summary:        "Feature Brainstorming - Mobile App",
		MeetingType:    "BRAINSTORMING",
		AttendanceMode: "REMOTE_WITH_VIDEO",
		DurationHours:  1.5,
		Attendees:      5,
		Description:    "Creative session for new mobile features",
	},
	// Can join while commuting (passive listening)
	{
		Summary:        "All-Hands Meeting - Q3 Results",
		MeetingType:    "ALL_HANDS",
		AttendanceMode: "CAN_JOIN_WHILE_COMMUTING",
		DurationHours:  1.0,
		Attendees:      50,
		Description:    "Company-wide updates and announcements",
	},
	{
		Summary:        "Weekly Status Update",
		MeetingType:    "STATUS_UPDATE",
		AttendanceMode: "CAN_JOIN_WHILE_COMMUTING",
		DurationHours:  0.5,
		Attendees:      12,
		Description:    "Project progress review - mostly listening",
	},
	{
		Summary:        "Daily Standup",
		MeetingType:    "CHECK_IN",
		AttendanceMode: "CAN_JOIN_WHILE_COMMUTING",
		DurationHours:  0.25,
		Attendees:      8,
		Description:    "Brief team sync - can listen while commuting",
	},
}

// DemoRequest represents the request payload for demo data generation
type DemoRequest struct {
	UserTimezone string `json:"userTimezone,omitempty"`
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

	// Get user's preferred timezone from database first, then fall back to request
	var userPreferredTimezone string
	err := h.db.QueryRow("SELECT preferred_timezone FROM users WHERE id = $1", user.ID).Scan(&userPreferredTimezone)
	if err != nil {
		userPreferredTimezone = "UTC" // Default fallback
	}
	
	// Parse request body to get browser timezone (as backup)
	var demoReq DemoRequest
	if err := json.NewDecoder(r.Body).Decode(&demoReq); err != nil {
		demoReq.UserTimezone = userPreferredTimezone // Use DB preferred timezone
	}
	
	// Use user's preferred timezone from DB, fallback to browser timezone, then UTC
	timezoneToUse := userPreferredTimezone
	if timezoneToUse == "UTC" && demoReq.UserTimezone != "" && demoReq.UserTimezone != "UTC" {
		timezoneToUse = demoReq.UserTimezone
	}
	
	// Validate and parse timezone
	userLocation, err := time.LoadLocation(timezoneToUse)
	if err != nil {
		// Fallback to UTC if invalid timezone
		userLocation = time.UTC
	}

	// Clear existing calendar events for this user (demo data only)
	_, err = h.db.Exec("DELETE FROM calendar_events WHERE user_id = $1", user.ID)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(DemoResponse{
			Success: false,
			Error:   "Failed to clear existing events",
		})
		return
	}

	// Generate smart calendar events with user's timezone
	events, err := h.generateSmartCalendarEvents(r.Context(), user.ID, userLocation)
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
func (h *DemoHandler) generateSmartCalendarEvents(ctx context.Context, userID string, userLocation *time.Location) ([]*models.CalendarEvent, error) {
	var events []*models.CalendarEvent
	// Use current time in user's timezone as the base for date generation
	now := time.Now().In(userLocation)
	
	// Generate events for next 14 days (realistic planning window)
	for dayOffset := 0; dayOffset < 14; dayOffset++ {
		targetDate := now.AddDate(0, 0, dayOffset)
		
		// Skip weekends for most business events
		if targetDate.Weekday() == time.Saturday || targetDate.Weekday() == time.Sunday {
			continue
		}
		
		// Smart event density based on day of week
		eventCount := h.getSmartEventCount(targetDate)
		
		dayEvents := h.generateDayEvents(ctx, userID, targetDate, eventCount, userLocation)
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
func (h *DemoHandler) generateDayEvents(ctx context.Context, userID string, date time.Time, eventCount int, userLocation *time.Location) []*models.CalendarEvent {
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
		
		// Create time in user's timezone first
		localTime := time.Date(date.Year(), date.Month(), date.Day(), hour, 0, 0, 0, userLocation)
		// Convert to UTC explicitly to work around lib/pq timezone binding bug
		startTime := localTime.UTC()
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
		"MUST_BE_IN_PERSON":         {"Conference Room A", "Boardroom", "Training Room", "Client Meeting Room"},
		"REMOTE_WITH_VIDEO":         {"Zoom", "Google Meet", "Teams", "Conference Room B (optional)"},
		"CAN_JOIN_WHILE_COMMUTING": {"Zoom (audio only)", "Google Meet (audio)", "Teams (audio)", "Conference call"},
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