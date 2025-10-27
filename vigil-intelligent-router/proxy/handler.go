package proxy

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"net/http"
	"time"

	"github.com/project-vigil/vigil-intelligent-router/config"
	"github.com/project-vigil/vigil-intelligent-router/ml"
	"go.uber.org/zap"
)

// Handler handles the intelligent routing of RPC requests
type Handler struct {
	mlClient   *ml.Client
	httpClient *http.Client
	config     *config.Config
	logger     *zap.Logger
}

// NewHandler creates a new proxy handler
func NewHandler(mlClient *ml.Client, cfg *config.Config, logger *zap.Logger) *Handler {
	return &Handler{
		mlClient: mlClient,
		httpClient: &http.Client{
			Timeout: cfg.RequestTimeout,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 20,
				IdleConnTimeout:     90 * time.Second,
			},
		},
		config: cfg,
		logger: logger,
	}
}

// ServeHTTP implements http.Handler for intelligent RPC routing
func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	startTime := time.Now()
	
	// Enable CORS for browser-based clients
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
	
	// Handle preflight OPTIONS request
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}
	
	// Only accept POST requests
	if r.Method != http.MethodPost {
		h.logger.Warn("Invalid request method",
			zap.String("method", r.Method),
			zap.String("path", r.URL.Path))
		http.Error(w, "Method not allowed. Use POST for RPC requests.", http.StatusMethodNotAllowed)
		return
	}

	// Read the original request body
	bodyBytes, err := io.ReadAll(r.Body)
	if err != nil {
		h.logger.Error("Failed to read request body", zap.Error(err))
		http.Error(w, "Failed to read request body", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// Validate JSON-RPC format
	if !json.Valid(bodyBytes) {
		h.logger.Warn("Invalid JSON in request body")
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	h.logger.Info("Received RPC request",
		zap.Int("body_size", len(bodyBytes)),
		zap.String("remote_addr", r.RemoteAddr))

	// Query ML service for best node recommendation
	ctx, cancel := context.WithTimeout(context.Background(), h.config.MLQueryTimeout)
	defer cancel()

	prediction, err := h.mlClient.GetRecommendation(ctx)
	if err != nil {
		h.logger.Error("ML service query failed", zap.Error(err))
		
		// Use fallback if enabled
		if h.config.FallbackEnabled {
			h.logger.Info("Using fallback RPC",
				zap.String("url", h.config.FallbackRPCURL))
			h.forwardRequest(w, r, h.config.FallbackRPCURL, bodyBytes, startTime)
			return
		}
		
		http.Error(w, "ML service unavailable and no fallback configured", http.StatusServiceUnavailable)
		return
	}

	// Get the target RPC URL from the recommended node
	targetURL, err := h.mlClient.GetRecommendedNodeURL(prediction.RecommendedNode)
	if err != nil {
		h.logger.Error("Failed to resolve node URL",
			zap.String("node_id", prediction.RecommendedNode),
			zap.Error(err))
		
		// Use fallback
		if h.config.FallbackEnabled {
			targetURL = h.config.FallbackRPCURL
			h.logger.Info("Using fallback due to URL resolution failure",
				zap.String("url", targetURL))
		} else {
			http.Error(w, "Failed to resolve target node", http.StatusInternalServerError)
			return
		}
	}

	h.logger.Info("Routing to recommended node",
		zap.String("node", prediction.RecommendedNode),
		zap.String("url", targetURL),
		zap.Float64("failure_prob", prediction.RecommendationDetails.FailureProb),
		zap.Float64("predicted_latency", prediction.RecommendationDetails.PredictedLatencyMS),
		zap.Float64("cost_score", prediction.RecommendationDetails.CostScore))

	// Forward the request
	h.forwardRequest(w, r, targetURL, bodyBytes, startTime)
}

// forwardRequest forwards the RPC request to the target node and streams the response
func (h *Handler) forwardRequest(w http.ResponseWriter, originalReq *http.Request, targetURL string, bodyBytes []byte, startTime time.Time) {
	// Create new request to target RPC
	req, err := http.NewRequest(http.MethodPost, targetURL, bytes.NewReader(bodyBytes))
	if err != nil {
		h.logger.Error("Failed to create forwarding request", zap.Error(err))
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	// Copy essential headers
	req.Header.Set("Content-Type", "application/json")
	if userAgent := originalReq.Header.Get("User-Agent"); userAgent != "" {
		req.Header.Set("User-Agent", userAgent)
	}

	// Execute the request
	resp, err := h.httpClient.Do(req)
	if err != nil {
		h.logger.Error("Request to target RPC failed",
			zap.String("target", targetURL),
			zap.Error(err))
		http.Error(w, "Failed to reach RPC node", http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	// Copy response headers
	for key, values := range resp.Header {
		for _, value := range values {
			w.Header().Add(key, value)
		}
	}

	// Set status code
	w.WriteHeader(resp.StatusCode)

	// Stream response body back to client
	written, err := io.Copy(w, resp.Body)
	if err != nil {
		h.logger.Error("Failed to stream response",
			zap.Error(err),
			zap.Int64("bytes_written", written))
		return
	}

	duration := time.Since(startTime)
	h.logger.Info("Request completed",
		zap.String("target", targetURL),
		zap.Int("status", resp.StatusCode),
		zap.Int64("response_size", written),
		zap.Duration("total_duration", duration))
}

// HealthCheckHandler returns a simple health check handler
func HealthCheckHandler(logger *zap.Logger) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Enable CORS for health checks too
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}
		
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		
		response := map[string]interface{}{
			"status":  "healthy",
			"service": "vigil-intelligent-router",
			"time":    time.Now().UTC().Format(time.RFC3339),
		}
		
		json.NewEncoder(w).Encode(response)
		
		logger.Debug("Health check requested",
			zap.String("remote_addr", r.RemoteAddr))
	}
}

