package main

import (
	"encoding/json"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/commute-planner/backend/internal/config"
	"github.com/commute-planner/backend/pkg/auth"
	"github.com/commute-planner/backend/pkg/database"
	"github.com/commute-planner/backend/pkg/handlers"
	"github.com/commute-planner/backend/pkg/redis"
	"github.com/commute-planner/backend/pkg/resolvers"
	"github.com/gorilla/mux"
	"github.com/rs/cors"
)

type GraphQLRequest struct {
	Query     string                 `json:"query"`
	Variables map[string]interface{} `json:"variables"`
}

type GraphQLResponse struct {
	Data   interface{} `json:"data,omitempty"`
	Errors []string    `json:"errors,omitempty"`
}

func main() {
	cfg := config.Load()

	db, err := database.NewConnection()
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	// Initialize Redis client
	log.Printf("Initializing Redis client...")
	redisClient := redis.NewClient("redis:6379")
	defer redisClient.Close()
	log.Printf("Redis client initialized")

	resolver := resolvers.NewResolver(db, redisClient)

	// Initialize OAuth-ready auth system (starts with JWT, migrates to OAuth easily)
	jwtSecret := "your-jwt-secret-key-change-in-production" // TODO: Move to env var
	authProvider := auth.NewJWTProvider(db, jwtSecret)
	authHandler := handlers.NewAuthHandler(authProvider)
	demoHandler := handlers.NewDemoHandler(db)

	router := mux.NewRouter()

	// Apply auth middleware to all routes FIRST (parses JWT and sets user in context)
	router.Use(authHandler.AuthMiddleware)

	// Auth endpoints - OAuth ready architecture
	router.HandleFunc("/auth/signup", authHandler.Signup).Methods("POST")
	router.HandleFunc("/auth/login", authHandler.Login).Methods("POST")
	router.HandleFunc("/auth/me", authHandler.Me).Methods("GET")
	
	// Demo data endpoints (protected - requires authentication)
	router.Handle("/demo/generate", handlers.RequireAuth(http.HandlerFunc(demoHandler.GenerateDemoData))).Methods("POST")
	router.Handle("/demo/check", handlers.RequireAuth(http.HandlerFunc(demoHandler.CheckDemoData))).Methods("GET")
	
	// Future OAuth endpoints (ready for Google Calendar integration)
	// router.HandleFunc("/auth/google", authHandler.GoogleOAuth).Methods("GET")
	// router.HandleFunc("/auth/google/callback", authHandler.GoogleOAuthCallback).Methods("GET")

	// Health check endpoint
	router.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status": "OK", "timestamp": "` + time.Now().UTC().Format(time.RFC3339) + `"}`))
	}).Methods("GET")

	// Simple GraphQL endpoint for basic queries
	router.HandleFunc("/graphql", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		
		if r.Method == "GET" {
			// GraphQL playground HTML
			playground := `
<!DOCTYPE html>
<html>
<head>
	<meta charset=utf-8/>
	<title>GraphQL Playground</title>
	<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css"/>
	<script src="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>
</head>
<body>
	<div id="root">
		<style>body { background-color: rgb(23, 42, 58); font-family: Open Sans, sans-serif; height: 90vh; }</style>
		<div style="color: white; text-align: center; padding: 20px;">
			<h1>Commute Planner GraphQL API</h1>
			<p>Send POST requests to this endpoint with GraphQL queries</p>
			<p>Example query:</p>
			<pre style="background: #1a1a1a; color: #f8f8f2; padding: 20px; border-radius: 5px; text-align: left; max-width: 500px; margin: 0 auto;">
{
  "query": "{ health }"
}
			</pre>
		</div>
	</div>
</body>
</html>`
			w.Write([]byte(playground))
			return
		}

		if r.Method != "POST" {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		var req GraphQLRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		var response GraphQLResponse

		// Handle basic queries and mutations
		switch {
		case req.Query == "{ health }" || req.Query == "query { health }":
			health, _ := resolver.Health(r.Context())
			response.Data = map[string]interface{}{"health": health}
		case req.Query == "{ users }" || req.Query == "{ users { id email name } }" || req.Query == "query { users { id email name } }":
			users, err := resolver.Users(r.Context())
			if err != nil {
				response.Errors = []string{err.Error()}
			} else {
				response.Data = map[string]interface{}{"users": users}
			}
		case strings.Contains(req.Query, "calendarEvents"):
			// Handle calendarEvents query
			if req.Variables != nil {
				if userID, ok := req.Variables["userId"].(string); ok {
					// Check for optional targetDate parameter
					var targetDate *string
					if td, ok := req.Variables["targetDate"].(string); ok {
						targetDate = &td
					}
					
					events, err := resolver.CalendarEvents(r.Context(), userID, targetDate)
					if err != nil {
						response.Errors = []string{err.Error()}
					} else {
						response.Data = map[string]interface{}{"calendarEvents": events}
					}
				} else {
					response.Errors = []string{"userId variable is required for calendarEvents query"}
				}
			} else {
				response.Errors = []string{"variables are required for calendarEvents query"}
			}
		default:
			// Handle job mutations
			if req.Variables != nil {
				if input, ok := req.Variables["input"].(map[string]interface{}); ok {
					if userID, exists := input["userId"]; exists {
						// This is likely a createJob mutation
						createInput := resolvers.CreateJobInput{
							UserID:     userID.(string),
							TargetDate: input["targetDate"].(string),
						}
						if inputData, hasInputData := input["inputData"]; hasInputData && inputData != nil {
							inputDataStr := inputData.(string)
							createInput.InputData = &inputDataStr
						}
						
						job, err := resolver.CreateJob(r.Context(), createInput)
						if err != nil {
							response.Errors = []string{err.Error()}
						} else {
							response.Data = map[string]interface{}{"createJob": job}
						}
						
						// Send job to Redis queue for processing
						if job != nil {
							jobData := map[string]interface{}{
								"job_id":      job.ID,
								"user_id":     job.UserID,
								"target_date": job.TargetDate,
								"input_data":  input["inputData"], // Pass original input_data
							}
							
							// Add job to Redis queue
							if err := resolver.QueueJob(r.Context(), jobData); err != nil {
								log.Printf("Failed to queue job %s: %v", job.ID, err)
							} else {
								log.Printf("Added job %s to Redis queue for processing", job.ID)
							}
						}
						
						// Return early to prevent "not supported" error
						json.NewEncoder(w).Encode(response)
						return
					}
				}
				
				// Handle updateJob mutation
				if id, ok := req.Variables["id"].(string); ok {
					if input, ok := req.Variables["input"].(map[string]interface{}); ok {
						updateInput := resolvers.UpdateJobInput{}
						
						if status, exists := input["status"]; exists && status != nil {
							statusStr := status.(string)
							updateInput.Status = &statusStr
						}
						if progress, exists := input["progress"]; exists && progress != nil {
							progressFloat := progress.(float64)
							updateInput.Progress = &progressFloat
						}
						if currentStep, exists := input["currentStep"]; exists && currentStep != nil {
							currentStepStr := currentStep.(string)
							updateInput.CurrentStep = &currentStepStr
						}
						if result, exists := input["result"]; exists && result != nil {
							resultStr := result.(string)
							updateInput.Result = &resultStr
						}
						if errorMessage, exists := input["errorMessage"]; exists && errorMessage != nil {
							errorMessageStr := errorMessage.(string)
							updateInput.ErrorMessage = &errorMessageStr
						}
						
						job, err := resolver.UpdateJob(r.Context(), id, updateInput)
						if err != nil {
							response.Errors = []string{err.Error()}
						} else {
							response.Data = map[string]interface{}{"updateJob": job}
						}
						
						// Return early to prevent "not supported" error
						json.NewEncoder(w).Encode(response)
						return
					}
				}
			}
			response.Errors = []string{"Query not supported in this basic implementation. Try: { health } or { users { id email name } } or createJob/updateJob mutations"}
		}

		json.NewEncoder(w).Encode(response)
	}).Methods("GET", "POST")

	c := cors.New(cors.Options{
		AllowedOrigins:   []string{"*"},
		AllowCredentials: true,
		AllowedHeaders:   []string{"*"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
	})

	handler := c.Handler(router)

	log.Printf("Connect to http://localhost:%s/ for GraphQL playground", cfg.Port)
	log.Printf("Health check available at http://localhost:%s/health", cfg.Port)
	log.Fatal(http.ListenAndServe(":"+cfg.Port, handler))
}