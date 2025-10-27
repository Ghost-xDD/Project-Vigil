package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/project-vigil/vigil-intelligent-router/config"
	"github.com/project-vigil/vigil-intelligent-router/ml"
	"github.com/project-vigil/vigil-intelligent-router/proxy"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to load configuration: %v\n", err)
		os.Exit(1)
	}

	// Initialize logger
	logger, err := initLogger(cfg.LogLevel, cfg.LogFormat)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to initialize logger: %v\n", err)
		os.Exit(1)
	}
	defer logger.Sync()

	logger.Info("Starting Vigil Intelligent Router",
		zap.String("version", "1.0.0"),
		zap.String("listen_addr", cfg.GetListenAddr()),
		zap.String("ml_service", cfg.MLServiceURL),
		zap.String("data_collector", cfg.DataCollectorURL),
		zap.String("fallback_rpc", cfg.FallbackRPCURL),
		zap.Bool("fallback_enabled", cfg.FallbackEnabled))

	// Initialize ML client
	mlClient := ml.NewClient(
		cfg.GetMLPredictURL(),
		cfg.GetMetricsURL(),
		cfg.MLQueryTimeout,
		cfg.NodeURLMap,
		logger,
	)
	
	logger.Info("Node URL mappings configured",
		zap.Int("node_count", len(cfg.NodeURLMap)))

	// Create proxy handler
	proxyHandler := proxy.NewHandler(mlClient, cfg, logger)

	// Set up HTTP router
	mux := http.NewServeMux()
	
	// Main RPC endpoint
	mux.Handle("/rpc", proxyHandler)
	
	// Health check endpoint
	if cfg.HealthCheckEnabled {
		mux.HandleFunc("/health", proxy.HealthCheckHandler(logger))
	}
	
	// Root endpoint - handle both RPC requests and info
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		
		// If it's a POST request or OPTIONS (CORS preflight), treat it as RPC
		// The proxy handler will set CORS headers
		if r.Method == http.MethodPost || r.Method == http.MethodOptions {
			proxyHandler.ServeHTTP(w, r)
			return
		}
		
		// For GET requests, set CORS and show service info
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		w.Header().Set("Content-Type", "application/json")
		
		fmt.Fprintf(w, `{
  "service": "Vigil Intelligent Router",
  "version": "1.0.0",
  "endpoints": {
    "rpc": "/rpc",
    "root": "/",
    "health": "/health"
  },
  "description": "ML-powered intelligent routing for Solana RPC requests",
  "note": "POST JSON-RPC requests to / or /rpc"
}`)
	})

	// Create HTTP server
	server := &http.Server{
		Addr:         cfg.GetListenAddr(),
		Handler:      mux,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: cfg.RequestTimeout + (5 * time.Second), // Buffer for processing
		IdleTimeout:  60 * time.Second,
	}

	// Channel to listen for errors from the server
	serverErrors := make(chan error, 1)

	// Start HTTP server in a goroutine
	go func() {
		logger.Info("HTTP server listening", zap.String("addr", server.Addr))
		serverErrors <- server.ListenAndServe()
	}()

	// Channel to listen for interrupt signals
	shutdown := make(chan os.Signal, 1)
	signal.Notify(shutdown, os.Interrupt, syscall.SIGTERM)

	// Block until we receive a signal or an error
	select {
	case err := <-serverErrors:
		logger.Fatal("Server error", zap.Error(err))

	case sig := <-shutdown:
		logger.Info("Shutdown signal received",
			zap.String("signal", sig.String()))

		// Give outstanding requests some time to complete
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cancel()

		if err := server.Shutdown(ctx); err != nil {
			logger.Error("Graceful shutdown failed", zap.Error(err))
			if err := server.Close(); err != nil {
				logger.Fatal("Failed to close server", zap.Error(err))
			}
		}

		logger.Info("Server stopped gracefully")
	}
}

// initLogger initializes the zap logger based on configuration
func initLogger(level, format string) (*zap.Logger, error) {
	var zapLevel zapcore.Level
	if err := zapLevel.UnmarshalText([]byte(level)); err != nil {
		return nil, fmt.Errorf("invalid log level %q: %w", level, err)
	}

	var config zap.Config
	if format == "json" {
		config = zap.NewProductionConfig()
	} else {
		config = zap.NewDevelopmentConfig()
		config.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	}

	config.Level = zap.NewAtomicLevelAt(zapLevel)

	return config.Build()
}

