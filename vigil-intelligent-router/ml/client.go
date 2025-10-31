package ml

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"

	"go.uber.org/zap"
)

// CalibrationRecord tracks a single prediction vs actual measurement
type CalibrationRecord struct {
	NodeID           string
	PredictedLatency float64
	ActualLatency    float64
	Timestamp        time.Time
}

// Client handles communication with the ML prediction service
type Client struct {
	httpClient       *http.Client
	predictURL       string
	metricsURL       string
	nodeURLMap       map[string]string
	logger           *zap.Logger
	
	// Auto-calibration
	calibrationMutex sync.RWMutex
	calibrationData  []CalibrationRecord
	calibrationLimit int
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
		predictURL:       predictURL,
		metricsURL:       metricsURL,
		nodeURLMap:       nodeURLMap,
		logger:           logger,
		calibrationData:  make([]CalibrationRecord, 0, 100),
		calibrationLimit: 100,
	}
}

// MetricData represents a single metric data point
type MetricData struct {
	Timestamp       string   `json:"timestamp"`
	NodeID          string   `json:"node_id,omitempty"`     // Optional - if missing, use NodeName
	NodeName        string   `json:"node_name,omitempty"`   // From Data Collector
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

// GetRecommendation fetches metrics and gets a routing recommendation with hybrid scoring
func (c *Client) GetRecommendation(ctx context.Context) (*PredictionResponse, error) {
	// Step 1: Fetch metrics from Data Collector
	metrics, err := c.fetchMetrics(ctx)
	if err != nil {
		c.logger.Warn("Failed to fetch metrics, will try ML service anyway", zap.Error(err))
		
	}

	
	recentAvgs := calculateRecentAverages(metrics)
	
	c.logger.Debug("Calculated recent averages",
		zap.Int("node_count", len(recentAvgs)),
		zap.Any("sample_avgs", recentAvgs))

	// Step 2: Try to get ML prediction
	prediction, err := c.getPrediction(ctx, metrics)
	if err != nil {
		c.logger.Warn("ML prediction failed, falling back to metrics-only routing", zap.Error(err))
		// Fallback: Use recent metrics to pick best node
		return c.fallbackToMetricsOnly(metrics, recentAvgs)
	}

	// Step 3: Apply hybrid scoring (combine ML prediction with recent actual latency)
	prediction = c.applyHybridScoring(prediction, recentAvgs)

	// Step 4: Apply auto-calibration to correct for environment-specific offsets
	prediction = c.applyCalibration(prediction)

	c.logger.Info("Hybrid recommendation selected",
		zap.String("recommended_node", prediction.RecommendedNode),
		zap.Float64("hybrid_score", prediction.RecommendationDetails.CostScore))

	return prediction, nil
}

// calculateRecentAverages computes average latency per node from recent metrics
func calculateRecentAverages(metrics []MetricData) map[string]float64 {
	nodeLatencies := make(map[string][]float64)
	
	
	for _, m := range metrics {
		nodeID := m.NodeName
		if nodeID == "" {
			nodeID = m.NodeID
		}
		if nodeID == "" || m.LatencyMS == nil {
			continue
		}
		nodeLatencies[nodeID] = append(nodeLatencies[nodeID], *m.LatencyMS)
	}
	
	
	averages := make(map[string]float64)
	for nodeID, latencies := range nodeLatencies {
		if len(latencies) == 0 {
			continue
		}
		sum := 0.0
		for _, lat := range latencies {
			sum += lat
		}
		averages[nodeID] = sum / float64(len(latencies))
	}
	
	return averages
}

// applyHybridScoring combines ML prediction with recent actual latency
func (c *Client) applyHybridScoring(prediction *PredictionResponse, recentAvgs map[string]float64) *PredictionResponse {
	const (
		predictionWeight = 0.7  // Weight for ML prediction
		recentWeight     = 0.3  // Weight for recent actual latency
	)
	
	bestNode := ""
	bestScore := float64(999999) 
	
	// Recalculate scores for all nodes using hybrid approach
	for i := range prediction.AllPredictions {
		node := &prediction.AllPredictions[i]
		nodeID := node.NodeID
		
		predictedLatency := node.PredictedLatencyMS
		recentAvg, hasRecent := recentAvgs[nodeID]
		
		var hybridScore float64
		if hasRecent {
			
			hybridScore = (predictionWeight * predictedLatency) + (recentWeight * recentAvg)
		} else {
			
			hybridScore = predictedLatency
		}
		
		
		failurePenalty := node.FailureProb * 1000 // High penalty for risky nodes
		hybridScore += failurePenalty
		
		
		if node.AnomalyDetected {
			hybridScore *= 1.2 
		}
		
		
		node.CostScore = hybridScore
		
		
		if bestNode == "" || hybridScore < bestScore {
			bestNode = nodeID
			bestScore = hybridScore
		}
		
		c.logger.Debug("Node hybrid score",
			zap.String("node", nodeID),
			zap.Float64("predicted", predictedLatency),
			zap.Float64("recent_avg", recentAvg),
			zap.Float64("hybrid_score", hybridScore),
			zap.Bool("has_recent", hasRecent))
	}
	
	
	if bestNode != "" {
		prediction.RecommendedNode = bestNode
		for _, node := range prediction.AllPredictions {
			if node.NodeID == bestNode {
				prediction.RecommendationDetails = node
				break
			}
		}
	}
	
	return prediction
}

// applyCalibration adjusts predictions based on learned offset between predictions and actuals
func (c *Client) applyCalibration(prediction *PredictionResponse) *PredictionResponse {
	c.calibrationMutex.RLock()
	defer c.calibrationMutex.RUnlock()
	
	if len(c.calibrationData) < 5 {
		// Not enough data for calibration yet
		c.logger.Debug("Insufficient calibration data",
			zap.Int("records", len(c.calibrationData)))
		return prediction
	}
	
	// Calculate per-node offsets (predicted - actual)
	nodeOffsets := make(map[string][]float64)
	for _, record := range c.calibrationData {
		offset := record.PredictedLatency - record.ActualLatency
		nodeOffsets[record.NodeID] = append(nodeOffsets[record.NodeID], offset)
	}
	
	// Calculate average offset per node
	nodeAvgOffsets := make(map[string]float64)
	for nodeID, offsets := range nodeOffsets {
		if len(offsets) == 0 {
			continue
		}
		sum := 0.0
		for _, offset := range offsets {
			sum += offset
		}
		nodeAvgOffsets[nodeID] = sum / float64(len(offsets))
	}
	
	// Calculate global offset as fallback
	globalOffset := 0.0
	totalRecords := 0
	for _, offsets := range nodeOffsets {
		for _, offset := range offsets {
			globalOffset += offset
			totalRecords++
		}
	}
	if totalRecords > 0 {
		globalOffset /= float64(totalRecords)
	}
	
	c.logger.Info("Calibration offsets calculated",
		zap.Float64("global_offset", globalOffset),
		zap.Int("total_records", len(c.calibrationData)))
	
	// Apply calibration to all predictions
	for i := range prediction.AllPredictions {
		node := &prediction.AllPredictions[i]
		
		// Use node-specific offset if available, otherwise global offset
		offset, hasNodeOffset := nodeAvgOffsets[node.NodeID]
		if !hasNodeOffset {
			offset = globalOffset
		}
		
		// Apply calibration
		originalLatency := node.PredictedLatencyMS
		node.PredictedLatencyMS = originalLatency - offset
		
		// Ensure non-negative
		if node.PredictedLatencyMS < 0 {
			node.PredictedLatencyMS = 0
		}
		
		c.logger.Debug("Applied calibration",
			zap.String("node", node.NodeID),
			zap.Float64("original", originalLatency),
			zap.Float64("offset", offset),
			zap.Float64("calibrated", node.PredictedLatencyMS))
	}
	
	// Update recommendation details
	for _, node := range prediction.AllPredictions {
		if node.NodeID == prediction.RecommendedNode {
			prediction.RecommendationDetails = node
			break
		}
	}
	
	return prediction
}

// RecordActual records actual latency for calibration learning
func (c *Client) RecordActual(nodeID string, predictedLatency, actualLatency float64) {
	c.calibrationMutex.Lock()
	defer c.calibrationMutex.Unlock()
	
	record := CalibrationRecord{
		NodeID:           nodeID,
		PredictedLatency: predictedLatency,
		ActualLatency:    actualLatency,
		Timestamp:        time.Now(),
	}
	
	c.calibrationData = append(c.calibrationData, record)
	
	// Keep only recent records
	if len(c.calibrationData) > c.calibrationLimit {
		c.calibrationData = c.calibrationData[len(c.calibrationData)-c.calibrationLimit:]
	}
	
	c.logger.Debug("Recorded calibration data",
		zap.String("node", nodeID),
		zap.Float64("predicted", predictedLatency),
		zap.Float64("actual", actualLatency),
		zap.Float64("offset", predictedLatency-actualLatency),
		zap.Int("total_records", len(c.calibrationData)))
}

// GetCalibrationStats returns current calibration statistics
func (c *Client) GetCalibrationStats() map[string]interface{} {
	c.calibrationMutex.RLock()
	defer c.calibrationMutex.RUnlock()
	
	if len(c.calibrationData) == 0 {
		return map[string]interface{}{
			"records": 0,
			"status":  "no_data",
		}
	}
	
	// Calculate per-node offsets
	nodeOffsets := make(map[string][]float64)
	for _, record := range c.calibrationData {
		offset := record.PredictedLatency - record.ActualLatency
		nodeOffsets[record.NodeID] = append(nodeOffsets[record.NodeID], offset)
	}
	
	// Calculate average offset per node
	nodeAvgOffsets := make(map[string]float64)
	for nodeID, offsets := range nodeOffsets {
		if len(offsets) == 0 {
			continue
		}
		sum := 0.0
		for _, offset := range offsets {
			sum += offset
		}
		nodeAvgOffsets[nodeID] = sum / float64(len(offsets))
	}
	
	// Global offset
	globalOffset := 0.0
	for _, record := range c.calibrationData {
		globalOffset += record.PredictedLatency - record.ActualLatency
	}
	globalOffset /= float64(len(c.calibrationData))
	
	return map[string]interface{}{
		"records":       len(c.calibrationData),
		"global_offset": globalOffset,
		"node_offsets":  nodeAvgOffsets,
		"status":        "active",
	}
}

func (c *Client) fallbackToMetricsOnly(metrics []MetricData, recentAvgs map[string]float64) (*PredictionResponse, error) {
	if len(recentAvgs) == 0 {
		return nil, fmt.Errorf("no metrics available for fallback routing")
	}
	
	
	bestNode := ""
	bestLatency := float64(999999)
	
	for nodeID, avgLatency := range recentAvgs {
		
		isHealthy := false
		for i := len(metrics) - 1; i >= 0; i-- {
			if metrics[i].NodeName == nodeID || metrics[i].NodeID == nodeID {
				isHealthy = metrics[i].IsHealthy == 1
				break
			}
		}
		
		if !isHealthy {
			c.logger.Debug("Skipping unhealthy node in fallback",
				zap.String("node", nodeID))
			continue
		}
		
		if avgLatency < bestLatency {
			bestNode = nodeID
			bestLatency = avgLatency
		}
	}
	
	if bestNode == "" {
		
		for nodeID, avgLatency := range recentAvgs {
			if bestNode == "" || avgLatency < bestLatency {
				bestNode = nodeID
				bestLatency = avgLatency
			}
		}
	}
	
	if bestNode == "" {
		return nil, fmt.Errorf("no viable nodes found")
	}
	
	c.logger.Info("Fallback routing selected",
		zap.String("node", bestNode),
		zap.Float64("avg_latency", bestLatency))
	
	
	return &PredictionResponse{
		RecommendedNode: bestNode,
		Explanation:     fmt.Sprintf("Fallback routing: selected %s based on recent metrics (avg: %.1fms)", bestNode, bestLatency),
		Timestamp:       time.Now().Format(time.RFC3339),
		AllPredictions: []NodePrediction{
			{
				NodeID:             bestNode,
				PredictedLatencyMS: bestLatency,
				FailureProb:        0.0,
				AnomalyDetected:    false,
				CostScore:          bestLatency,
			},
		},
		RecommendationDetails: NodePrediction{
			NodeID:             bestNode,
			PredictedLatencyMS: bestLatency,
			FailureProb:        0.0,
			AnomalyDetected:    false,
			CostScore:          bestLatency,
		},
	}, nil
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

	c.logger.Debug("Fetched metrics from collector",
		zap.Int("count", len(metrics)),
		zap.Strings("sample_node_names", func() []string {
			names := []string{}
			for i := 0; i < 3 && i < len(metrics); i++ {
				names = append(names, metrics[i].NodeName)
			}
			return names
		}()))

	return metrics, nil
}

// getPrediction sends metrics to ML service and gets a prediction
func (c *Client) getPrediction(ctx context.Context, metrics []MetricData) (*PredictionResponse, error) {
	// Ensure each metric has NodeID populated from NodeName if needed
	for i := range metrics {
		if metrics[i].NodeID == "" && metrics[i].NodeName != "" {
			metrics[i].NodeID = metrics[i].NodeName
			c.logger.Debug("Copied NodeName to NodeID",
				zap.String("node", metrics[i].NodeID))
		}
	}
	
	reqBody := PredictionRequest{Metrics: metrics}
	
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}
	
	c.logger.Debug("Sending to ML service",
		zap.Int("metric_count", len(metrics)),
		zap.String("first_100_chars", string(jsonData[:min(100, len(jsonData))])))


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

// Helper function
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// GetRecommendedNodeURL extracts the RPC URL from node_id using the configured mapping
func (c *Client) GetRecommendedNodeURL(nodeID string) (string, error) {
	if url, exists := c.nodeURLMap[nodeID]; exists {
		return url, nil
	}

	return "", fmt.Errorf("unknown node ID: %s (not found in configuration)", nodeID)
}

