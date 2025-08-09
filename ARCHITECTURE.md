# Multi-Agent Commute Planning System - Architecture Specification

## Project Overview

### Primary Use Cases
1. **Daily Commute Planning**: Plan optimal commute timing and meeting attendance mode (remote vs in-office) to minimize disruption and maximize efficiency
2. **Errand Integration**: Optimize errand timing within daily schedule to minimize total travel time

### Core Requirements
- Read-only Google Calendar access initially
- Google Maps integration for travel time optimization
- Multi-agent AI system using LangChain/LangGraph
- Real-time progress updates via GraphQL subscriptions
- Enterprise-grade architecture ready for scaling

## System Architecture

### Technology Stack
- **Frontend**: React with TypeScript, Apollo Client for GraphQL
- **Gateway**: Node.js with Apollo Server, GraphQL Federation
- **Backend**: Go with gqlgen for GraphQL API
- **AI Service**: Python with LangChain/LangGraph
- **Database**: PostgreSQL
- **Deployment**: Docker containers, AWS/GCP

### Project Structure
```
enterprise-app/
├── services/
│   ├── frontend/           # React + TypeScript + Apollo Client
│   ├── gateway/           # Node.js + Apollo Server + Federation
│   ├── backend/           # Go + gqlgen + PostgreSQL
│   └── ai-service/        # Python + LangChain + LangGraph
├── shared/
│   ├── schemas/           # GraphQL schemas
│   └── types/             # Shared type definitions
├── database/
│   ├── migrations/
│   └── schemas/
└── infrastructure/
    └── docker/
```

## Multi-Agent AI Architecture

### Agent Specialization
```python
agents/
├── schedule_analyzer_agent.py      # Analyzes calendar patterns and events
├── meeting_classifier_agent.py     # Determines remote vs in-office requirements
├── office_presence_validator_agent.py  # Validates office time blocks against business rules
├── perception_optimizer_agent.py   # Considers workplace optics and professional impact
├── commute_optimizer_agent.py      # Travel time and route optimization
├── logistics_agent.py              # Parking, walking, setup time calculations
└── option_presenter_agent.py       # Formats and ranks recommendations

graphs/
├── daily_commute_planner.py        # Main workflow for use case #1
└── errand_optimizer.py             # Extended workflow for use case #2

tools/
├── google_calendar_tool.py         # Google Calendar API integration
├── google_maps_tool.py             # Google Maps/Routes API integration
├── database_tool.py                # Database operations
└── notification_tool.py            # Real-time progress updates
```

### LangGraph Workflow State
```python
class CommuteState(TypedDict):
    target_date: str
    calendar_events: List[dict]
    meeting_classifications: List[dict]      # remote vs office decisions
    office_presence_blocks: List[dict]       # valid office time windows
    perception_analysis: dict               # workplace optics analysis
    commute_options: List[dict]             # travel time calculations
    filtered_options: List[dict]            # options passing business rules
    recommendations: List[dict]             # final ranked recommendations
    progress_step: str                      # real-time progress updates
```

### Workflow Flow
```
fetch_calendar → classify_meetings → validate_office_blocks → 
analyze_perception → calculate_commute_windows → filter_viable_options → 
optimize_schedule → present_options
```

## Critical Business Rules

### Office Presence Requirements
1. **Minimum Stay**: 4+ hours to justify commute
2. **Arrival Patterns**: 
   - Before 10 AM (shows dedication) OR
   - After lunch (1 PM+) but MUST stay until at least 5 PM
3. **Departure Patterns**: Avoid leaving during "core hours" (10 AM - 4 PM) unless staying 4+ hours
4. **Lunch Pattern Avoidance**: Don't arrive 12-1 PM and leave 2-3 PM
5. **Core Collaboration Hours**: 10 AM - 4 PM presence preferred
6. **Perception Management**: Ensure visible presence during key collaboration hours

### Meeting Classification Logic
- **MUST be in-office**: Client meetings, presentations, team workshops, interviews, important stakeholder meetings
- **CAN be remote**: 1:1s, status updates, reviews, brainstorming calls, routine check-ins

### Safety and Efficiency Rules
- **No calls while driving**: 30-minute buffer before first office meeting after arrival
- **Parking/walking buffer**: 15 minutes for parking and walking to office
- **Traffic optimization**: Consider real-time and historical traffic patterns

## API Integrations

### Google Calendar API
- **OAuth 2.0 Authentication**: Standard OAuth flow for user consent
- **Read Operations**: Get events, availability, meeting details
- **Scopes**: `https://www.googleapis.com/auth/calendar.readonly`

### Google Maps Platform APIs
- **Routes API**: Time-based routing with departure/arrival time optimization
- **Real-time Traffic**: Current and predicted traffic conditions
- **Multiple Transport Modes**: Driving, walking, transit options

## Expected Output Format
```json
{
  "recommendations": [
    {
      "option_rank": 1,
      "type": "FULL_DAY_OFFICE|STRATEGIC_AFTERNOON|FULL_REMOTE_RECOMMENDED",
      "commute_start": "2025-08-08T07:45:00Z",
      "office_arrival": "2025-08-08T08:30:00Z", 
      "office_departure": "2025-08-08T17:15:00Z",
      "commute_end": "2025-08-08T18:00:00Z",
      "office_duration": "8 hours 45 minutes",
      "office_meetings": ["meeting-id-1", "meeting-id-2"],
      "remote_meetings": ["meeting-id-3"],
      "business_rule_compliance": {
        "minimum_stay": "✅ PASS (8h 45m > 4h required)",
        "arrival_pattern": "✅ PASS (8:30 AM - professional early arrival)",
        "departure_pattern": "✅ PASS (5:15 PM - end of business day)",
        "core_hours_presence": "✅ PASS (present 10 AM - 4 PM)",
        "lunch_pattern": "✅ PASS (no lunch-and-dash)"
      },
      "perception_analysis": {
        "professional_impact": "VERY_POSITIVE|NEUTRAL_TO_POSITIVE|NEUTRAL",
        "reasoning": "Early arrival shows dedication...",
        "team_visibility": "HIGH|MEDIUM|LOW"
      },
      "reasoning": "Detailed explanation of why this option is recommended",
      "trade_offs": {
        "pros": ["Strong professional presence", "..."],
        "cons": ["Longer total day including commute", "..."]
      }
    }
  ]
}
```

## Real-time Progress Updates

### GraphQL Subscription Schema
```graphql
subscription JobProgress($jobId: ID!) {
  jobProgress(jobId: $jobId) {
    id
    status
    progress
    currentStep
    result
  }
}
```

### Progress Steps
1. "Analyzing your calendar for tomorrow..."
2. "Analyzing which meetings require in-office attendance..."
3. "Validating office presence requirements..."
4. "Analyzing workplace perception factors..."
5. "Calculating optimal commute times..."
6. "Filtering options by business rules..."
7. "Optimizing your schedule options..."
8. "Preparing recommendations..."

## Development Phases

### Phase 1: Foundation
- Set up monorepo structure
- Implement basic GraphQL gateway
- Create Go backend with PostgreSQL
- Set up Docker development environment

### Phase 2: AI Service Core
- Implement LangChain/LangGraph framework
- Create basic agent structure
- Implement Google Calendar tool
- Implement Google Maps tool

### Phase 3: Business Logic
- Implement office presence validation
- Add perception optimization logic
- Create meeting classification algorithms
- Add commute optimization logic

### Phase 4: Integration
- Connect AI service to backend via GraphQL
- Implement real-time progress updates
- Create React frontend with Apollo Client
- Add authentication and user management

### Phase 5: Enhancement
- Add errand optimization feature
- Implement advanced filtering options
- Add user preferences and learning
- Performance optimization and caching

## Security and Privacy Considerations
- Secure OAuth token storage
- User data privacy compliance
- Rate limiting for external APIs
- Audit logging for AI decisions
- Error handling and graceful degradation

## Testing Strategy
- Unit tests for each agent
- Integration tests for LangGraph workflows
- End-to-end tests for complete user journeys
- Performance testing for AI response times
- API integration testing with mocked external services

## Deployment and Scaling
- Docker containerization for all services
- Kubernetes deployment configurations
- CI/CD pipeline setup
- Monitoring and observability
- Auto-scaling based on AI workload

---

This architecture specification provides the foundation for building an enterprise-grade multi-agent commute planning system that prioritizes safety, efficiency, and professional perception while leveraging cutting-edge AI technologies.