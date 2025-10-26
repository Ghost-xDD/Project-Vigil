package config

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/joho/godotenv"
)

// Config holds all configuration for the intelligent router
type Config struct {
	// Server settings
	RouterPort string
	RouterHost string

	// ML Service settings
	MLServiceURL       string
	MLPredictEndpoint  string
	MLQueryTimeout     time.Duration

	// Data Collector settings
	DataCollectorURL string
	MetricsEndpoint  string

	// Fallback settings
	FallbackRPCURL string
	FallbackEnabled bool

	// Request settings
	RequestTimeout time.Duration

	// Logging
	LogLevel  string
	LogFormat string

	// Health check
	HealthCheckEnabled bool

	// Node URL mappings
	NodeURLMap map[string]string
}

// Load loads configuration from environment variables
func Load() (*Config, error) {
	// Try to load .env file (ignore error if it doesn't exist)
	_ = godotenv.Load()

	config := &Config{
		RouterPort:         getEnv("ROUTER_PORT", "8080"),
		RouterHost:         getEnv("ROUTER_HOST", "0.0.0.0"),
		MLServiceURL:       getEnv("ML_SERVICE_URL", "http://localhost:8001"),
		MLPredictEndpoint:  getEnv("ML_PREDICT_ENDPOINT", "/predict"),
		DataCollectorURL:   getEnv("DATA_COLLECTOR_URL", "http://localhost:8000"),
		MetricsEndpoint:    getEnv("METRICS_ENDPOINT", "/api/v1/metrics/latest-metrics"),
		FallbackRPCURL:     getEnv("FALLBACK_RPC_URL", "https://api.devnet.solana.com"),
		FallbackEnabled:    getEnvBool("FALLBACK_ENABLED", true),
		RequestTimeout:     getEnvDuration("REQUEST_TIMEOUT_SECONDS", 30),
		MLQueryTimeout:     getEnvDuration("ML_QUERY_TIMEOUT_SECONDS", 5),
		LogLevel:           getEnv("LOG_LEVEL", "info"),
		LogFormat:          getEnv("LOG_FORMAT", "json"),
		HealthCheckEnabled: getEnvBool("HEALTH_CHECK_ENABLED", true),
		NodeURLMap:         loadNodeURLMap(),
	}

	if err := config.Validate(); err != nil {
		return nil, fmt.Errorf("invalid configuration: %w", err)
	}

	return config, nil
}

// loadNodeURLMap loads node ID to RPC URL mappings from environment
func loadNodeURLMap() map[string]string {
	nodeMap := make(map[string]string)
	
	// Load from environment variables
	// Format: NODE_URL_<NODE_ID>=<URL>
	if url := os.Getenv("NODE_URL_ANKR_DEVNET"); url != "" {
		nodeMap["ankr_devnet"] = url
	} else {
		nodeMap["ankr_devnet"] = getEnv("ANKR_DEVNET_RPC_URL", "https://rpc.ankr.com/solana_devnet")
	}
	
	if url := os.Getenv("NODE_URL_HELIUS_DEVNET"); url != "" {
		nodeMap["helius_devnet"] = url
	} else {
		nodeMap["helius_devnet"] = getEnv("HELIUS_DEVNET_RPC_URL", "https://devnet.helius-rpc.com")
	}
	
	if url := os.Getenv("NODE_URL_ALCHEMY_DEVNET"); url != "" {
		nodeMap["alchemy_devnet"] = url
	} else {
		nodeMap["alchemy_devnet"] = getEnv("ALCHEMY_DEVNET_RPC_URL", "https://solana-devnet.g.alchemy.com/v2")
	}
	
	if url := os.Getenv("NODE_URL_SOLANA_PUBLIC_DEVNET"); url != "" {
		nodeMap["solana_public_devnet"] = url
	} else {
		nodeMap["solana_public_devnet"] = getEnv("SOLANA_PUBLIC_DEVNET_RPC_URL", "https://api.devnet.solana.com")
	}
	
	if url := os.Getenv("NODE_URL_AGAVE_SELF_HOSTED"); url != "" {
		nodeMap["agave_self_hosted"] = url
	} else {
		// For simulated node, default to public endpoint
		nodeMap["agave_self_hosted"] = getEnv("AGAVE_SELF_HOSTED_RPC_URL", "https://api.devnet.solana.com")
	}
	
	return nodeMap
}

// Validate checks if the configuration is valid
func (c *Config) Validate() error {
	if c.MLServiceURL == "" {
		return fmt.Errorf("ML_SERVICE_URL is required")
	}
	if c.DataCollectorURL == "" {
		return fmt.Errorf("DATA_COLLECTOR_URL is required")
	}
	if c.FallbackEnabled && c.FallbackRPCURL == "" {
		return fmt.Errorf("FALLBACK_RPC_URL is required when fallback is enabled")
	}
	return nil
}

// GetMLPredictURL returns the full URL for ML predictions
func (c *Config) GetMLPredictURL() string {
	return c.MLServiceURL + c.MLPredictEndpoint
}

// GetMetricsURL returns the full URL for fetching metrics
func (c *Config) GetMetricsURL() string {
	return c.DataCollectorURL + c.MetricsEndpoint
}

// GetListenAddr returns the address to listen on
func (c *Config) GetListenAddr() string {
	return c.RouterHost + ":" + c.RouterPort
}

// Helper functions

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		boolVal, err := strconv.ParseBool(value)
		if err == nil {
			return boolVal
		}
	}
	return defaultValue
}

func getEnvDuration(key string, defaultSeconds int) time.Duration {
	if value := os.Getenv(key); value != "" {
		seconds, err := strconv.Atoi(value)
		if err == nil {
			return time.Duration(seconds) * time.Second
		}
	}
	return time.Duration(defaultSeconds) * time.Second
}

