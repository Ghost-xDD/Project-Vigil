.PHONY: build run test clean docker-build docker-run

# Build the Go binary
build:
	@echo "Building vigil-intelligent-router..."
	@go build -o vigil-router .
	@echo "Build complete: ./vigil-router"

# Run the application
run:
	@echo "Starting vigil-intelligent-router..."
	@go run .

# Run tests
test:
	@echo "Running tests..."
	@go test ./... -v

# Clean build artifacts
clean:
	@echo "Cleaning..."
	@rm -f vigil-router
	@echo "Clean complete"

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	@docker build -t vigil-intelligent-router:latest .
	@echo "Docker image built successfully"

# Run in Docker
docker-run:
	@echo "Running in Docker..."
	@docker run -p 8080:8080 \
		-e ML_SERVICE_URL=http://host.docker.internal:8001 \
		-e DATA_COLLECTOR_URL=http://host.docker.internal:8000 \
		vigil-intelligent-router:latest

# Download dependencies
deps:
	@echo "Downloading dependencies..."
	@go mod download
	@echo "Dependencies downloaded"

# Tidy dependencies
tidy:
	@echo "Tidying dependencies..."
	@go mod tidy
	@echo "Dependencies tidied"

# Format code
fmt:
	@echo "Formatting code..."
	@go fmt ./...
	@echo "Code formatted"

# Run linter
lint:
	@echo "Running linter..."
	@golangci-lint run ./...

# Development mode with hot reload (requires air: go install github.com/cosmtrek/air@latest)
dev:
	@air

.DEFAULT_GOAL := build

