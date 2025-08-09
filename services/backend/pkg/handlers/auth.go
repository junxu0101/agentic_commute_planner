package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"

	"github.com/commute-planner/backend/pkg/auth"
	"github.com/commute-planner/backend/pkg/models"
)

// AuthHandler handles authentication endpoints
type AuthHandler struct {
	authProvider auth.AuthProvider
}

// NewAuthHandler creates a new auth handler
func NewAuthHandler(authProvider auth.AuthProvider) *AuthHandler {
	return &AuthHandler{
		authProvider: authProvider,
	}
}

// SignupRequest represents the signup request payload
type SignupRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
	Name     string `json:"name"`
}

// LoginRequest represents the login request payload
type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

// AuthResponse represents the auth response
type AuthResponse struct {
	Success bool               `json:"success"`
	Data    *auth.AuthResult   `json:"data,omitempty"`
	Error   string             `json:"error,omitempty"`
}

// Signup handles user registration
func (h *AuthHandler) Signup(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req SignupRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		json.NewEncoder(w).Encode(AuthResponse{
			Success: false,
			Error:   "Invalid request payload",
		})
		return
	}

	// Basic validation
	if req.Email == "" || req.Password == "" || req.Name == "" {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(AuthResponse{
			Success: false,
			Error:   "Email, password, and name are required",
		})
		return
	}

	result, err := h.authProvider.Signup(r.Context(), req.Email, req.Password, req.Name)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(AuthResponse{
			Success: false,
			Error:   err.Error(),
		})
		return
	}

	json.NewEncoder(w).Encode(AuthResponse{
		Success: true,
		Data:    result,
	})
}

// Login handles user authentication
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		json.NewEncoder(w).Encode(AuthResponse{
			Success: false,
			Error:   "Invalid request payload",
		})
		return
	}

	// Basic validation
	if req.Email == "" || req.Password == "" {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(AuthResponse{
			Success: false,
			Error:   "Email and password are required",
		})
		return
	}

	result, err := h.authProvider.Login(r.Context(), req.Email, req.Password)
	if err != nil {
		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(AuthResponse{
			Success: false,
			Error:   err.Error(),
		})
		return
	}

	json.NewEncoder(w).Encode(AuthResponse{
		Success: true,
		Data:    result,
	})
}

// Me returns current user info from JWT token
func (h *AuthHandler) Me(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	if r.Method != "GET" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	user := GetUserFromContext(r.Context())
	if user == nil {
		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(AuthResponse{
			Success: false,
			Error:   "Unauthorized",
		})
		return
	}

	json.NewEncoder(w).Encode(AuthResponse{
		Success: true,
		Data: &auth.AuthResult{
			User: user,
		},
	})
}

// AuthMiddleware validates JWT tokens and adds user to context
func (h *AuthHandler) AuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			next.ServeHTTP(w, r)
			return
		}

		// Extract token from "Bearer <token>"
		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			next.ServeHTTP(w, r)
			return
		}

		token := parts[1]
		user, err := h.authProvider.ValidateToken(r.Context(), token)
		if err != nil {
			next.ServeHTTP(w, r)
			return
		}

		// Add user to context
		ctx := context.WithValue(r.Context(), "user", user)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// RequireAuth middleware that requires authentication
func RequireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		user := GetUserFromContext(r.Context())
		if user == nil {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			json.NewEncoder(w).Encode(AuthResponse{
				Success: false,
				Error:   "Authentication required",
			})
			return
		}
		next.ServeHTTP(w, r)
	})
}

// GetUserFromContext extracts user from request context
func GetUserFromContext(ctx context.Context) *models.User {
	user, ok := ctx.Value("user").(*models.User)
	if !ok {
		return nil
	}
	return user
}