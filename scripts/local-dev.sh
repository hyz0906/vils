#!/bin/bash

# VILS Local Development Script
# This script helps manage local development environment

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command_exists node; then
        missing_deps+=("node")
    fi
    
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Please install the missing dependencies and try again."
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Function to setup backend
setup_backend() {
    print_status "Setting up backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    print_status "Installing Python dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating backend .env file..."
        cat > .env << EOF
# Database
DATABASE_URL=postgresql://vils_user:vils_password@localhost:5432/vils_db

# Security
SECRET_KEY=dev-secret-key-change-in-production
ENCRYPTION_MASTER_KEY=dev-encryption-key-change-in-production

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
    fi
    
    cd ..
    print_success "Backend setup completed"
}

# Function to setup frontend
setup_frontend() {
    print_status "Setting up frontend..."
    
    cd frontend
    
    # Install node dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_status "Creating frontend .env file..."
        cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
VITE_USE_MOCK_API=false
EOF
    fi
    
    cd ..
    print_success "Frontend setup completed"
}

# Function to start services with Docker Compose
start_services() {
    print_status "Starting services with Docker Compose..."
    
    # Start databases and Redis
    docker-compose up -d postgres redis
    
    # Wait for databases to be ready
    print_status "Waiting for databases to be ready..."
    sleep 10
    
    # Start other services
    docker-compose up -d
    
    print_success "All services started"
    print_status "Services are accessible at:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  Backend Docs: http://localhost:8000/docs"
    echo "  Flower (Celery monitoring): http://localhost:5555"
    echo "  PostgreSQL: localhost:5432"
    echo "  Redis: localhost:6379"
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Services stopped"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    cd backend
    source venv/bin/activate
    
    # Run Alembic migrations
    alembic upgrade head
    
    cd ..
    print_success "Database migrations completed"
}

# Function to create a new migration
create_migration() {
    local message="${1:-Auto migration}"
    
    print_status "Creating new migration: $message"
    
    cd backend
    source venv/bin/activate
    
    # Create new migration
    alembic revision --autogenerate -m "$message"
    
    cd ..
    print_success "Migration created"
}

# Function to reset database
reset_database() {
    print_warning "This will delete all data in the database. Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Resetting database..."
        
        # Stop services
        docker-compose down
        
        # Remove database volume
        docker volume rm vils_postgres_data 2>/dev/null || true
        
        # Start services
        docker-compose up -d postgres redis
        sleep 10
        
        # Run migrations
        run_migrations
        
        # Restart all services
        docker-compose up -d
        
        print_success "Database reset completed"
    else
        print_status "Database reset cancelled"
    fi
}

# Function to run tests
run_tests() {
    local service="${1:-all}"
    
    case $service in
        backend)
            print_status "Running backend tests..."
            cd backend
            source venv/bin/activate
            pytest
            cd ..
            ;;
        frontend)
            print_status "Running frontend tests..."
            cd frontend
            npm run test
            cd ..
            ;;
        all)
            run_tests backend
            run_tests frontend
            ;;
        *)
            print_error "Unknown test target: $service"
            print_status "Available targets: backend, frontend, all"
            exit 1
            ;;
    esac
}

# Function to show logs
show_logs() {
    local service="${1:-}"
    
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# Function to show status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    
    print_status "Docker containers:"
    docker ps --filter "name=vils"
    
    print_status "Useful URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
    echo "  Flower (Celery): http://localhost:5555"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up development environment..."
    
    # Stop and remove containers
    docker-compose down --volumes --remove-orphans
    
    # Remove images (optional)
    print_warning "Remove Docker images? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        docker-compose down --rmi all
    fi
    
    print_success "Cleanup completed"
}

# Function to open shell in container
shell() {
    local service="${1:-backend}"
    
    case $service in
        backend|frontend|worker|postgres|redis)
            print_status "Opening shell in $service container..."
            docker-compose exec "$service" /bin/sh
            ;;
        *)
            print_error "Unknown service: $service"
            print_status "Available services: backend, frontend, worker, postgres, redis"
            exit 1
            ;;
    esac
}

# Main command handling
case "${1:-}" in
    setup)
        check_prerequisites
        setup_backend
        setup_frontend
        print_success "Development environment setup completed!"
        print_status "Next steps:"
        echo "  1. $0 start    # Start all services"
        echo "  2. $0 migrate  # Run database migrations"
        echo "  3. Open http://localhost:3000 in your browser"
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        start_services
        ;;
    migrate)
        run_migrations
        ;;
    migration)
        create_migration "${2:-Auto migration}"
        ;;
    reset-db)
        reset_database
        ;;
    test)
        run_tests "${2:-all}"
        ;;
    logs)
        show_logs "${2:-}"
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup
        ;;
    shell)
        shell "${2:-backend}"
        ;;
    help|--help|-h)
        echo "VILS Local Development Script"
        echo
        echo "Usage: $0 [command] [options]"
        echo
        echo "Commands:"
        echo "  setup              Set up development environment"
        echo "  start              Start all services"
        echo "  stop               Stop all services"
        echo "  restart            Restart all services"
        echo "  migrate            Run database migrations"
        echo "  migration [msg]    Create new migration"
        echo "  reset-db           Reset database (WARNING: deletes all data)"
        echo "  test [target]      Run tests (backend/frontend/all)"
        echo "  logs [service]     Show logs"
        echo "  status             Show service status"
        echo "  cleanup            Clean up development environment"
        echo "  shell [service]    Open shell in container"
        echo "  help               Show this help message"
        echo
        echo "Examples:"
        echo "  $0 setup                    # Initial setup"
        echo "  $0 start                    # Start development servers"
        echo "  $0 logs backend             # Show backend logs"
        echo "  $0 shell postgres           # Open PostgreSQL shell"
        echo "  $0 test frontend            # Run frontend tests"
        ;;
    *)
        print_error "Unknown command: ${1:-}"
        print_status "Run '$0 help' for usage information"
        exit 1
        ;;
esac