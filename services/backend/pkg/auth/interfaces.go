package auth

import (
	"context"
	"time"

	"github.com/commute-planner/backend/pkg/models"
)

// AuthProvider defines the interface for different auth providers
// This makes it easy to switch between JWT, OAuth, Auth0, etc.
type AuthProvider interface {
	// Local auth methods (JWT)
	Signup(ctx context.Context, email, password, name string) (*AuthResult, error)
	Login(ctx context.Context, email, password string) (*AuthResult, error)
	
	// OAuth methods (for future Google Calendar integration)
	HandleOAuth(ctx context.Context, provider string, code string) (*AuthResult, error)
	RefreshToken(ctx context.Context, refreshToken string) (*AuthResult, error)
	
	// Token validation (works for both JWT and OAuth)
	ValidateToken(ctx context.Context, token string) (*models.User, error)
	
	// User management
	GetUserByID(ctx context.Context, userID string) (*models.User, error)
	GetUserByEmail(ctx context.Context, email string) (*models.User, error)
}

// AuthResult represents the result of authentication
type AuthResult struct {
	User         *models.User `json:"user"`
	AccessToken  string       `json:"accessToken"`
	RefreshToken string       `json:"refreshToken,omitempty"`
	TokenType    string       `json:"tokenType"` // "Bearer"
	ExpiresIn    int64        `json:"expiresIn"` // seconds
	Scopes       []string     `json:"scopes,omitempty"`
}

// TokenClaims represents JWT token claims (OAuth-compatible)
type TokenClaims struct {
	UserID       string    `json:"sub"`
	Email        string    `json:"email"`
	Name         string    `json:"name"`
	AuthProvider string    `json:"auth_provider"`
	Scopes       []string  `json:"scopes,omitempty"`
	IssuedAt     time.Time `json:"iat"`
	ExpiresAt    time.Time `json:"exp"`
}

// OAuthConfig holds OAuth provider configuration
// This will be used when we migrate to Google OAuth
type OAuthConfig struct {
	ClientID     string
	ClientSecret string
	RedirectURL  string
	Scopes       []string
	AuthURL      string
	TokenURL     string
}