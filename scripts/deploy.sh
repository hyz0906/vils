#!/bin/bash

# VILS Deployment Script
# This script deploys the VILS application to Kubernetes

set -e  # Exit on any error

# Configuration
NAMESPACE="vils"
BACKEND_IMAGE="vils/backend:latest"
FRONTEND_IMAGE="vils/frontend:latest"
KUBECTL_CONTEXT=""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for deployment rollout
wait_for_rollout() {
    local deployment=$1
    print_status "Waiting for $deployment to be ready..."
    if kubectl -n $NAMESPACE rollout status deployment/$deployment --timeout=300s; then
        print_success "$deployment is ready"
    else
        print_error "$deployment failed to become ready"
        return 1
    fi
}

# Function to check pod status
check_pods() {
    print_status "Checking pod status..."
    kubectl -n $NAMESPACE get pods
    
    # Check if any pods are in error state
    if kubectl -n $NAMESPACE get pods | grep -E "(Error|CrashLoopBackOff|ImagePullBackOff)"; then
        print_warning "Some pods are in error state. Check logs with: kubectl -n $NAMESPACE logs <pod-name>"
    fi
}

# Function to run health checks
health_check() {
    print_status "Running health checks..."
    
    # Check if backend service is accessible
    if kubectl -n $NAMESPACE get svc vils-backend-service >/dev/null 2>&1; then
        print_success "Backend service is available"
        
        # Try to access health endpoint (if port-forward is available)
        if command_exists curl; then
            print_status "You can check the health endpoint with:"
            echo "  kubectl -n $NAMESPACE port-forward svc/vils-backend-service 8000:8000"
            echo "  curl http://localhost:8000/api/monitoring/health"
        fi
    else
        print_error "Backend service is not available"
    fi
    
    # Check if frontend service is accessible
    if kubectl -n $NAMESPACE get svc vils-frontend-service >/dev/null 2>&1; then
        print_success "Frontend service is available"
    else
        print_error "Frontend service is not available"
    fi
}

# Function to show access information
show_access_info() {
    print_success "Deployment completed successfully!"
    echo
    print_status "Access Information:"
    echo "  Frontend: https://vils.example.com"
    echo "  API: https://api.vils.example.com"
    echo "  Flower (Celery monitoring): https://flower.vils.example.com"
    echo
    print_status "Local access (using port-forward):"
    echo "  Frontend: kubectl -n $NAMESPACE port-forward svc/vils-frontend-service 3000:80"
    echo "  Backend: kubectl -n $NAMESPACE port-forward svc/vils-backend-service 8000:8000"
    echo "  Flower: kubectl -n $NAMESPACE port-forward svc/vils-celery-flower-service 5555:5555"
    echo
    print_status "Useful commands:"
    echo "  View pods: kubectl -n $NAMESPACE get pods"
    echo "  View services: kubectl -n $NAMESPACE get svc"
    echo "  View logs: kubectl -n $NAMESPACE logs -f deployment/<deployment-name>"
    echo "  Scale deployment: kubectl -n $NAMESPACE scale deployment/<deployment-name> --replicas=<number>"
}

# Main deployment function
deploy() {
    print_status "Starting VILS deployment to Kubernetes..."
    
    # Check prerequisites
    if ! command_exists kubectl; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    if ! command_exists docker; then
        print_warning "docker is not installed. You may need it to build images."
    fi
    
    # Set kubectl context if provided
    if [ ! -z "$KUBECTL_CONTEXT" ]; then
        print_status "Setting kubectl context to $KUBECTL_CONTEXT"
        kubectl config use-context $KUBECTL_CONTEXT
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info >/dev/null 2>&1; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    # Create namespace
    print_status "Creating namespace..."
    kubectl apply -f k8s/namespace.yaml
    
    # Apply configurations
    print_status "Applying configurations..."
    kubectl apply -f k8s/configmap.yaml
    
    # Deploy databases
    print_status "Deploying PostgreSQL..."
    kubectl apply -f k8s/postgres.yaml
    wait_for_rollout postgres
    
    print_status "Deploying Redis..."
    kubectl apply -f k8s/redis.yaml
    wait_for_rollout redis
    
    # Wait a bit for databases to be fully ready
    print_status "Waiting for databases to be ready..."
    sleep 30
    
    # Deploy backend services
    print_status "Deploying backend services..."
    kubectl apply -f k8s/backend.yaml
    
    # Wait for backend to be ready
    wait_for_rollout vils-backend
    wait_for_rollout vils-celery-worker
    wait_for_rollout vils-celery-beat
    wait_for_rollout vils-celery-flower
    
    # Deploy frontend
    print_status "Deploying frontend..."
    kubectl apply -f k8s/frontend.yaml
    wait_for_rollout vils-frontend
    
    # Apply ingress and networking
    print_status "Applying ingress configuration..."
    kubectl apply -f k8s/ingress.yaml
    
    # Apply autoscaling
    print_status "Applying autoscaling configuration..."
    kubectl apply -f k8s/hpa.yaml
    
    # Final status check
    sleep 10
    check_pods
    health_check
    show_access_info
}

# Function to build and push images
build_images() {
    print_status "Building Docker images..."
    
    # Build backend image
    print_status "Building backend image..."
    docker build -t $BACKEND_IMAGE -f backend/Dockerfile backend/
    
    # Build frontend image
    print_status "Building frontend image..."
    docker build -t $FRONTEND_IMAGE -f frontend/Dockerfile frontend/
    
    # Push images (if registry is configured)
    if [ "$PUSH_IMAGES" = "true" ]; then
        print_status "Pushing images to registry..."
        docker push $BACKEND_IMAGE
        docker push $FRONTEND_IMAGE
    fi
    
    print_success "Images built successfully"
}

# Function to clean up deployment
cleanup() {
    print_warning "Cleaning up VILS deployment..."
    
    # Delete in reverse order
    kubectl delete -f k8s/hpa.yaml --ignore-not-found=true
    kubectl delete -f k8s/ingress.yaml --ignore-not-found=true
    kubectl delete -f k8s/frontend.yaml --ignore-not-found=true
    kubectl delete -f k8s/backend.yaml --ignore-not-found=true
    kubectl delete -f k8s/redis.yaml --ignore-not-found=true
    kubectl delete -f k8s/postgres.yaml --ignore-not-found=true
    kubectl delete -f k8s/configmap.yaml --ignore-not-found=true
    
    # Delete namespace (this will delete everything in it)
    print_warning "Deleting namespace $NAMESPACE (this will delete all resources)..."
    kubectl delete namespace $NAMESPACE --ignore-not-found=true
    
    print_success "Cleanup completed"
}

# Function to show status
status() {
    print_status "VILS Deployment Status:"
    echo
    
    # Check namespace
    if kubectl get namespace $NAMESPACE >/dev/null 2>&1; then
        print_success "Namespace '$NAMESPACE' exists"
    else
        print_error "Namespace '$NAMESPACE' does not exist"
        return 1
    fi
    
    # Show deployments
    print_status "Deployments:"
    kubectl -n $NAMESPACE get deployments
    echo
    
    # Show pods
    print_status "Pods:"
    kubectl -n $NAMESPACE get pods
    echo
    
    # Show services
    print_status "Services:"
    kubectl -n $NAMESPACE get services
    echo
    
    # Show ingress
    print_status "Ingress:"
    kubectl -n $NAMESPACE get ingress
}

# Function to show logs
logs() {
    local service=${1:-backend}
    
    case $service in
        backend)
            kubectl -n $NAMESPACE logs -f deployment/vils-backend
            ;;
        frontend)
            kubectl -n $NAMESPACE logs -f deployment/vils-frontend
            ;;
        worker)
            kubectl -n $NAMESPACE logs -f deployment/vils-celery-worker
            ;;
        beat)
            kubectl -n $NAMESPACE logs -f deployment/vils-celery-beat
            ;;
        flower)
            kubectl -n $NAMESPACE logs -f deployment/vils-celery-flower
            ;;
        postgres)
            kubectl -n $NAMESPACE logs -f deployment/postgres
            ;;
        redis)
            kubectl -n $NAMESPACE logs -f deployment/redis
            ;;
        *)
            print_error "Unknown service: $service"
            print_status "Available services: backend, frontend, worker, beat, flower, postgres, redis"
            exit 1
            ;;
    esac
}

# Parse command line arguments
case "${1:-}" in
    deploy)
        deploy
        ;;
    build)
        build_images
        ;;
    cleanup)
        cleanup
        ;;
    status)
        status
        ;;
    logs)
        logs "${2:-backend}"
        ;;
    help|--help|-h)
        echo "VILS Deployment Script"
        echo
        echo "Usage: $0 [command] [options]"
        echo
        echo "Commands:"
        echo "  deploy     Deploy VILS to Kubernetes"
        echo "  build      Build Docker images"
        echo "  cleanup    Remove VILS deployment from Kubernetes"
        echo "  status     Show deployment status"
        echo "  logs       Show logs for a service (default: backend)"
        echo "  help       Show this help message"
        echo
        echo "Environment variables:"
        echo "  KUBECTL_CONTEXT  Set kubectl context"
        echo "  PUSH_IMAGES      Push images to registry (true/false)"
        echo
        echo "Examples:"
        echo "  $0 deploy                    # Deploy to current kubectl context"
        echo "  $0 build                     # Build images locally"
        echo "  PUSH_IMAGES=true $0 build    # Build and push images"
        echo "  $0 logs worker               # Show worker logs"
        echo "  $0 cleanup                   # Remove deployment"
        ;;
    *)
        print_error "Unknown command: ${1:-}"
        print_status "Run '$0 help' for usage information"
        exit 1
        ;;
esac