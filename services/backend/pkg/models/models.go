package models

import (
	"time"
)

type JobStatus string

const (
	JobStatusPending    JobStatus = "PENDING"
	JobStatusInProgress JobStatus = "IN_PROGRESS"
	JobStatusCompleted  JobStatus = "COMPLETED"
	JobStatusFailed     JobStatus = "FAILED"
)

type CommuteOptionType string

const (
	CommuteOptionFullDayOffice           CommuteOptionType = "FULL_DAY_OFFICE"
	CommuteOptionStrategicAfternoon      CommuteOptionType = "STRATEGIC_AFTERNOON"
	CommuteOptionFullRemoteRecommended   CommuteOptionType = "FULL_REMOTE_RECOMMENDED"
)

type MeetingType string

const (
	MeetingTypeClientMeeting     MeetingType = "CLIENT_MEETING"
	MeetingTypePresentation      MeetingType = "PRESENTATION"
	MeetingTypeTeamWorkshop      MeetingType = "TEAM_WORKSHOP"
	MeetingTypeInterview         MeetingType = "INTERVIEW"
	MeetingTypeStakeholderMeeting MeetingType = "STAKEHOLDER_MEETING"
	MeetingTypeOneOnOne          MeetingType = "ONE_ON_ONE"
	MeetingTypeStatusUpdate      MeetingType = "STATUS_UPDATE"
	MeetingTypeReview            MeetingType = "REVIEW"
	MeetingTypeBrainstorming     MeetingType = "BRAINSTORMING"
	MeetingTypeCheckIn           MeetingType = "CHECK_IN"
	MeetingTypeUnknown           MeetingType = "UNKNOWN"
)

type AttendanceMode string

const (
	AttendanceMustBeInOffice AttendanceMode = "MUST_BE_IN_OFFICE"
	AttendanceCanBeRemote    AttendanceMode = "CAN_BE_REMOTE"
	AttendanceFlexible       AttendanceMode = "FLEXIBLE"
)

type User struct {
	ID              string     `json:"id" db:"id"`
	Email           string     `json:"email" db:"email"`
	Name            string     `json:"name" db:"name"`
	UserPreferences *string    `json:"userPreferences" db:"user_preferences"`
	
	// Auth fields - OAuth ready
	AuthProvider     *string    `json:"authProvider" db:"auth_provider"`
	ExternalID       *string    `json:"externalId" db:"external_id"`
	IsEmailVerified  *bool      `json:"isEmailVerified" db:"is_email_verified"`
	OAuthScopes      []string   `json:"oauthScopes" db:"oauth_scopes"`
	LastLogin        *time.Time `json:"lastLogin" db:"last_login"`
	
	CreatedAt       time.Time  `json:"createdAt" db:"created_at"`
	UpdatedAt       time.Time  `json:"updatedAt" db:"updated_at"`
}

type Job struct {
	ID           string     `json:"id" db:"id"`
	UserID       string     `json:"userId" db:"user_id"`
	Status       JobStatus  `json:"status" db:"status"`
	Progress     float64    `json:"progress" db:"progress"`
	CurrentStep  *string    `json:"currentStep" db:"current_step"`
	TargetDate   string     `json:"targetDate" db:"target_date"`
	InputData    *string    `json:"inputData" db:"input_data"`
	Result       *string    `json:"result" db:"result"`
	ErrorMessage *string    `json:"errorMessage" db:"error_message"`
	CreatedAt    time.Time  `json:"createdAt" db:"created_at"`
	UpdatedAt    time.Time  `json:"updatedAt" db:"updated_at"`
	User         *User      `json:"user,omitempty"`
	Recommendations []*CommuteRecommendation `json:"recommendations,omitempty"`
}

type CalendarEvent struct {
	ID             string         `json:"id" db:"id"`
	UserID         string         `json:"userId" db:"user_id"`
	Summary        string         `json:"summary" db:"summary"`
	Description    *string        `json:"description" db:"description"`
	StartTime      time.Time      `json:"startTime" db:"start_time"`
	EndTime        time.Time      `json:"endTime" db:"end_time"`
	Location       *string        `json:"location" db:"location"`
	Attendees      *string        `json:"attendees" db:"attendees"`
	MeetingType    MeetingType    `json:"meetingType" db:"meeting_type"`
	AttendanceMode AttendanceMode `json:"attendanceMode" db:"attendance_mode"`
	IsAllDay       bool           `json:"isAllDay" db:"is_all_day"`
	IsRecurring    bool           `json:"isRecurring" db:"is_recurring"`
	GoogleEventID  *string        `json:"googleEventId" db:"google_event_id"`
	CreatedAt      time.Time      `json:"createdAt" db:"created_at"`
	UpdatedAt      time.Time      `json:"updatedAt" db:"updated_at"`
	User           *User          `json:"user,omitempty"`
}

type CommuteRecommendation struct {
	ID                     string            `json:"id" db:"id"`
	JobID                  string            `json:"jobId" db:"job_id"`
	OptionRank             int               `json:"optionRank" db:"option_rank"`
	OptionType             CommuteOptionType `json:"optionType" db:"option_type"`
	CommuteStart           *time.Time        `json:"commuteStart" db:"commute_start"`
	OfficeArrival          *time.Time        `json:"officeArrival" db:"office_arrival"`
	OfficeDeparture        *time.Time        `json:"officeDeparture" db:"office_departure"`
	CommuteEnd             *time.Time        `json:"commuteEnd" db:"commute_end"`
	OfficeDuration         *string           `json:"officeDuration" db:"office_duration"`
	OfficeMeetings         *string           `json:"officeMeetings" db:"office_meetings"`
	RemoteMeetings         *string           `json:"remoteMeetings" db:"remote_meetings"`
	BusinessRuleCompliance *string           `json:"businessRuleCompliance" db:"business_rule_compliance"`
	PerceptionAnalysis     *string           `json:"perceptionAnalysis" db:"perception_analysis"`
	Reasoning              *string           `json:"reasoning" db:"reasoning"`
	TradeOffs              *string           `json:"tradeOffs" db:"trade_offs"`
	CreatedAt              time.Time         `json:"createdAt" db:"created_at"`
	Job                    *Job              `json:"job,omitempty"`
}