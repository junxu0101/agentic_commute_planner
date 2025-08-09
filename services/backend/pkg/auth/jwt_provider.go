






















package auth

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/lib/pq"
	"golang.org/x/crypto/bcrypt"

	"github.com/commute-planner/backend/pkg/database"
	"github.com/commute-planner/backend/pkg/models"
	"github.com/google/uuid"
)

// JWTProvider implements AuthProvider using JWT tokens
// This provides local authentication while being OAuth-ready
type JWTProvider struct {
	db        *database.DB
	jwtSecret []byte
	tokenTTL  time.Duration
}

// NewJWTProvider creates a new JWT auth provider
func NewJWTProvider(db *database.DB, jwtSecret string) *JWTProvider {
	return &JWTProvider{
		db:        db,
		jwtSecret: []byte(jwtSecret),
		tokenTTL:  24 * time.Hour, // 24 hours
	}
}

// Signup creates a new local user account
func (p *JWTProvider) Signup(ctx context.Context, email, password, name string) (*AuthResult, error) {
	// Check if user exists
	existingUser, _ := p.GetUserByEmail(ctx, email)
	if existingUser != nil {
		return nil, fmt.Errorf("user already exists")
	}

	// Hash password
	passwordHash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}

	// Create user
	userID := uuid.New().String()
	now := time.Now()
	
	query := `INSERT INTO users (id, email, name, password_hash, auth_provider, is_email_verified, created_at, updated_at) 
	          VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
	          RETURNING id, email, name, auth_provider, is_email_verified, created_at, updated_at`

	user := &models.User{}
	err = p.db.QueryRow(query, userID, email, name, string(passwordHash), "local", false, now, now).Scan(
		&user.ID,
		&user.Email,
		&user.Name,
		&user.AuthProvider,
		&user.IsEmailVerified,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	
	if err != nil {
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	// Generate JWT token
	token, err := p.generateJWT(user)
	if err != nil {
		return nil, fmt.Errorf("failed to generate token: %w", err)
	}

	return &AuthResult{
		User:        user,
		AccessToken: token,
		TokenType:   "Bearer",
		ExpiresIn:   int64(p.tokenTTL.Seconds()),
		Scopes:      []string{"read", "write"},
	}, nil
}

// Login authenticates a user with email/password
func (p *JWTProvider) Login(ctx context.Context, email, password string) (*AuthResult, error) {
	// Get user
	query := `SELECT id, email, name, password_hash, auth_provider, is_email_verified, created_at, updated_at 
	          FROM users WHERE email = $1 AND auth_provider = 'local'`
	
	user := &models.User{}
	var passwordHash string
	
	err := p.db.QueryRow(query, email).Scan(
		&user.ID,
		&user.Email,
		&user.Name,
		&passwordHash,
		&user.AuthProvider,
		&user.IsEmailVerified,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	
	if err != nil {
		return nil, fmt.Errorf("invalid credentials")
	}

	// Verify password
	err = bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(password))
	if err != nil {
		return nil, fmt.Errorf("invalid credentials")
	}

	// Update last login
	_, err = p.db.Exec("UPDATE users SET last_login = NOW() WHERE id = $1", user.ID)
	if err != nil {
		// Log but don't fail the login
		fmt.Printf("Failed to update last login: %v\n", err)
	}

	// Generate JWT token
	token, err := p.generateJWT(user)
	if err != nil {
		return nil, fmt.Errorf("failed to generate token: %w", err)
	}

	return &AuthResult{
		User:        user,
		AccessToken: token,
		TokenType:   "Bearer",
		ExpiresIn:   int64(p.tokenTTL.Seconds()),
		Scopes:      []string{"read", "write"},
	}, nil
}

// ValidateToken validates and parses a JWT token
func (p *JWTProvider) ValidateToken(ctx context.Context, tokenString string) (*models.User, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return p.jwtSecret, nil
	})

	if err != nil || !token.Valid {
		return nil, fmt.Errorf("invalid token")
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return nil, fmt.Errorf("invalid token claims")
	}

	userID, ok := claims["sub"].(string)
	if !ok {
		return nil, fmt.Errorf("invalid user ID in token")
	}

	// Get fresh user data from database
	return p.GetUserByID(ctx, userID)
}

// GetUserByID retrieves a user by ID
func (p *JWTProvider) GetUserByID(ctx context.Context, userID string) (*models.User, error) {
	query := `SELECT id, email, name, auth_provider, is_email_verified, COALESCE(oauth_scopes, '{}'::text[]), last_login, created_at, updated_at 
	          FROM users WHERE id = $1`
	
	user := &models.User{}
	var scopes pq.StringArray
	err := p.db.QueryRow(query, userID).Scan(
		&user.ID,
		&user.Email,
		&user.Name,
		&user.AuthProvider,
		&user.IsEmailVerified,
		&scopes,
		&user.LastLogin,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	
	if err == nil {
		user.OAuthScopes = []string(scopes)
	}
	
	if err != nil {
		return nil, fmt.Errorf("user not found: %w", err)
	}
	
	return user, nil
}

// GetUserByEmail retrieves a user by email
func (p *JWTProvider) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	query := `SELECT id, email, name, auth_provider, is_email_verified, COALESCE(oauth_scopes, '{}'::text[]), last_login, created_at, updated_at 
	          FROM users WHERE email = $1`
	
	user := &models.User{}
	var scopes pq.StringArray
	err := p.db.QueryRow(query, email).Scan(
		&user.ID,
		&user.Email,
		&user.Name,
		&user.AuthProvider,
		&user.IsEmailVerified,
		&scopes,
		&user.LastLogin,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	
	if err == nil {
		user.OAuthScopes = []string(scopes)
	}
	
	if err != nil {
		return nil, fmt.Errorf("user not found")
	}
	
	return user, nil
}

// generateJWT creates a JWT token for a user
func (p *JWTProvider) generateJWT(user *models.User) (string, error) {
	now := time.Now()
	
	claims := jwt.MapClaims{
		"sub":           user.ID,
		"email":         user.Email,
		"name":          user.Name,
		"auth_provider": user.AuthProvider,
		"scopes":        []string{"read", "write"},
		"iat":           now.Unix(),
		"exp":           now.Add(p.tokenTTL).Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(p.jwtSecret)
}

// OAuth methods - stubbed for future implementation
func (p *JWTProvider) HandleOAuth(ctx context.Context, provider string, code string) (*AuthResult, error) {
	return nil, fmt.Errorf("OAuth not implemented yet - coming soon for Google Calendar!")
}

func (p *JWTProvider) RefreshToken(ctx context.Context, refreshToken string) (*AuthResult, error) {
	return nil, fmt.Errorf("refresh token not implemented yet")
}

// generateSecureToken generates a secure random token
func generateSecureToken() string {
	bytes := make([]byte, 32)
	rand.Read(bytes)
	return base64.URLEncoding.EncodeToString(bytes)
}