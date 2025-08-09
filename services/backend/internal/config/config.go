package config

import (
	"os"
)

type Config struct {
	DatabaseURL string
	Port        string
}

func Load() *Config {
	return &Config{
		DatabaseURL: getEnv("DATABASE_URL", "postgres://commute_planner:dev_password@localhost:5432/commute_planner?sslmode=disable"),
		Port:        getEnv("PORT", "8080"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}