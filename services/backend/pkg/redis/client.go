package redis

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"
	
	"github.com/go-redis/redis/v8"
)

type Client struct {
	client *redis.Client
}


// NewClient creates a new Redis client
func NewClient(addr string) *Client {
	rdb := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: "", // no password
		DB:       0,  // default DB
	})

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	_, err := rdb.Ping(ctx).Result()
	if err != nil {
		log.Printf("Warning: Could not connect to Redis at %s: %v", addr, err)
		log.Printf("Jobs will be created in database but may not be processed by AI service")
	} else {
		log.Printf("Connected to Redis at %s", addr)
	}

	return &Client{client: rdb}
}

// JobMessage represents the job data structure expected by AI service
type JobMessage struct {
	JobID      string  `json:"job_id"`
	UserID     string  `json:"user_id"`
	TargetDate string  `json:"target_date"`
	InputData  *string `json:"input_data,omitempty"`
}

// AddJobToQueue adds a job to the commute_jobs queue
func (c *Client) AddJobToQueue(ctx context.Context, jobID, userID, targetDate string, inputData *string) error {
	if c.client == nil {
		return fmt.Errorf("redis client not initialized")
	}

	// Create job message as JSON object (as expected by AI service)
	jobMessage := JobMessage{
		JobID:      jobID,
		UserID:     userID,
		TargetDate: targetDate,
		InputData:  inputData,
	}

	// Marshal to JSON
	messageJSON, err := json.Marshal(jobMessage)
	if err != nil {
		return fmt.Errorf("failed to marshal job message: %w", err)
	}

	// Add job JSON to the commute_jobs queue
	err = c.client.LPush(ctx, "commute_jobs", string(messageJSON)).Err()
	if err != nil {
		return fmt.Errorf("failed to add job to queue: %w", err)
	}

	log.Printf("Added job %s to Redis queue for processing", jobID)
	return nil
}

// Close closes the Redis connection
func (c *Client) Close() error {
	if c.client != nil {
		return c.client.Close()
	}
	return nil
}