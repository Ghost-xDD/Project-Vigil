package ml

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"go.uber.org/zap"
)

// Client handles communication with the ML prediction service
type Client struct {
	httpClient       *http.Client
	predictURL       string
	metricsURL       string
	nodeURLMap       map[string]string
	logger           *zap.Logger
}

// NewClient creates a new ML client
func NewClient(predictURL, metricsURL string, timeout time.Duration, nodeURLMap map[string]string, logger *zap.Logger) *Client {
	return &Client{
		httpClient: &http.Client{
			Timeout: timeout,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     90 * time.Second,
			},
		},
		predictURL: predictURL,
		metricsURL: metricsURL,
		nodeURLMap: nodeURLMap,
		logger:     logger,
	}
}

// MetricData represents a single metric data point
type MetricData struct {
	Timestamp       string   `json:"timestamp"`
	NodeID          string   `json:"node_id"`
	CPUUsage        *float64 `json:"cpu_usage,omitempty"`
	MemoryUsage     *float64 `json:"memory_usage,omitempty"`
	DiskIO          *float64 `json:"disk_io,omitempty"`
	LatencyMS       *float64 `json:"latency_ms,omitempty"`
	BlockHeightGap  *int     `json:"block_height_gap,omitempty"`
	IsHealthy       int      `json:"is_healthy"`
}

// PredictionRequest represents the request to the ML service
type PredictionRequest struct {
	Metrics []MetricData `json:"metrics"`
}

// NodePrediction represents a prediction for a single node
type NodePrediction struct {
	NodeID             string  `json:"node_id"`
	FailureProb        float64 `json:"failure_prob"`
	PredictedLatencyMS float64 `json:"predicted_latency_ms"`
	AnomalyDetected    bool    `json:"anomaly_detected"`
	CostScore          float64 `json:"cost_score"`
}

// PredictionResponse represents the response from the ML service
type PredictionResponse struct {
	RecommendedNode        string           `json:"recommended_node"`
	Explanation            string           `json:"explanation"`
	Timestamp              string           `json:"timestamp"`
	AllPredictions         []NodePrediction `json:"all_predictions"`
	RecommendationDetails  NodePrediction   `json:"recommendation_details"`
}

// GetRecommendation fetches metrics and gets a routing recommendation
func (c *Client) GetRecommendation(ctx context.Context) (*PredictionResponse, error) {
	// Step 1: Fetch metrics from Data Collector
	metrics, err := c.fetchMetrics(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch metrics: %w", err)
	}

	if len(metrics) == 0 {
		return nil, fmt.Errorf("no metrics available")
	}

	c.logger.Debug("Fetched metrics from collector",
		zap.Int("metric_count", len(metrics)))

	// Step 2: Send metrics to ML service for prediction
	prediction, err := c.getPrediction(ctx, metrics)
	if err != nil {
		return nil, fmt.Errorf("failed to get prediction: %w", err)
	}

	c.logger.Info("Received ML recommendation",
		zap.String("recommended_node", prediction.RecommendedNode),
		zap.Float64("cost_score", prediction.RecommendationDetails.CostScore))

	return prediction, nil
}

// fetchMetrics retrieves current metrics from the Data Collector
func (c *Client) fetchMetrics(ctx context.Context) ([]MetricData, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.metricsURL, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(body))
	}

	var metrics []MetricData
	if err := json.NewDecoder(resp.Body).Decode(&metrics); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return metrics, nil
}

// getPrediction sends metrics to ML service and gets a prediction
func (c *Client) getPrediction(ctx context.Context, metrics []MetricData) (*PredictionResponse, error) {
	reqBody := PredictionRequest{Metrics: metrics}
	
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.predictURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(body))
	}

	var prediction PredictionResponse
	if err := json.NewDecoder(resp.Body).Decode(&prediction); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &prediction, nil
}

// GetRecommendedNodeURL extracts the RPC URL from node_id using the configured mapping
func (c *Client) GetRecommendedNodeURL(nodeID string) (string, error) {
	if url, exists := c.nodeURLMap[nodeID]; exists {
		return url, nil
	}

	return "", fmt.Errorf("unknown node ID: %s (not found in configuration)", nodeID)
}

