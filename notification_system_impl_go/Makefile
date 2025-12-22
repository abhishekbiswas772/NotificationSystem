.PHONY: build run worker clean migrate
build:
	@echo "Building API server..."
	@go build -o bin/server .

run: build
	@echo "Starting API server on :8080..."
	@./bin/server

worker:
	@echo "Building and starting worker..."
	@go build -o bin/worker ./cmd/worker
	@./bin/worker

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf bin/

migrate:
	@echo "Running migrations..."
	@go run main.go migrate

test:
	@echo "Running tests..."
	@go test ./... -v

deps:
	@echo "Installing dependencies..."
	@go mod download
	@go mod tidy

all:
	@echo "Run 'make run' in one terminal and 'make worker' in another"
