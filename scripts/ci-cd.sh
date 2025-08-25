#!/bin/bash

# VILS CI/CD Pipeline Script
# This script is designed to be used in CI/CD environments like GitHub Actions, GitLab CI, etc.

set -e

# Environment variables with defaults
ENVIRONMENT="${ENVIRONMENT:-development}"
BUILD_NUMBER="${BUILD_NUMBER:-$(date +%Y%m%d-%H%M%S)}"
REGISTRY_URL="${REGISTRY_URL:-docker.io}"
REGISTRY_USERNAME="${REGISTRY_USERNAME:-}"
REGISTRY_PASSWORD="${REGISTRY_PASSWORD:-}"
BACKEND_IMAGE="${BACKEND_IMAGE:-vils/backend}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-vils/frontend}"
IMAGE_TAG="${IMAGE_TAG:-$BUILD_NUMBER}"
PUSH_IMAGES="${PUSH_IMAGES:-true}"
RUN_TESTS="${RUN_TESTS:-true}"
DEPLOY_TO_K8S="${DEPLOY_TO_K8S:-false}"
K8S_NAMESPACE="${K8S_NAMESPACE:-vils}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[CI/CD]${NC} $1"
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

# Function to setup build environment
setup_build_env() {
    print_status "Setting up build environment..."
    
    # Install dependencies if needed
    if ! command_exists docker; then
        print_error "Docker is required but not installed"
        exit 1
    fi
    
    # Login to registry if credentials provided
    if [ -n "$REGISTRY_USERNAME" ] && [ -n "$REGISTRY_PASSWORD" ]; then
        print_status "Logging into registry..."
        echo "$REGISTRY_PASSWORD" | docker login "$REGISTRY_URL" -u "$REGISTRY_USERNAME" --password-stdin
        print_success "Registry login successful"
    fi
    
    # Create build directory
    mkdir -p build-artifacts
    
    print_success "Build environment setup completed"
}

# Function to run backend tests
test_backend() {
    print_status "Running backend tests..."
    
    cd backend
    
    # Create test environment
    python3 -m venv test-venv
    source test-venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Set test environment variables
    export DATABASE_URL="sqlite:///./test.db"
    export SECRET_KEY="test-secret-key"
    export ENCRYPTION_MASTER_KEY="test-encryption-key"
    export ENVIRONMENT="testing"
    
    # Run tests with coverage
    pytest --cov=src --cov-report=xml --cov-report=html --junitxml=../build-artifacts/backend-test-results.xml
    
    # Copy coverage reports
    cp coverage.xml ../build-artifacts/backend-coverage.xml
    cp -r htmlcov ../build-artifacts/backend-coverage-html
    
    # Cleanup
    deactivate
    rm -rf test-venv test.db
    
    cd ..
    print_success "Backend tests completed"
}

# Function to run frontend tests
test_frontend() {
    print_status "Running frontend tests..."
    
    cd frontend
    
    # Install dependencies
    npm ci
    
    # Run linting
    npm run lint
    
    # Run type checking
    npm run type-check
    
    # Run unit tests
    npm run test -- --run --coverage --reporter=junit --outputFile=../build-artifacts/frontend-test-results.xml
    
    # Copy coverage reports
    if [ -d "coverage" ]; then
        cp -r coverage ../build-artifacts/frontend-coverage
    fi
    
    cd ..
    print_success "Frontend tests completed"
}

# Function to run security scanning
security_scan() {
    print_status "Running security scans..."
    
    # Backend security scan
    if command_exists bandit; then
        print_status "Running backend security scan with bandit..."
        bandit -r backend/src -f json -o build-artifacts/backend-security-scan.json || true
    fi
    
    # Frontend security scan
    cd frontend
    if npm list --depth=0 > /dev/null 2>&1; then
        print_status "Running frontend security audit..."
        npm audit --audit-level=moderate --json > ../build-artifacts/frontend-security-scan.json || true
    fi
    cd ..
    
    print_success "Security scans completed"
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build backend image
    print_status "Building backend image: $BACKEND_IMAGE:$IMAGE_TAG"
    docker build \
        -t "$BACKEND_IMAGE:$IMAGE_TAG" \
        -t "$BACKEND_IMAGE:latest" \
        --build-arg BUILD_NUMBER="$BUILD_NUMBER" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        backend/
    
    # Build frontend image
    print_status "Building frontend image: $FRONTEND_IMAGE:$IMAGE_TAG"
    docker build \
        -t "$FRONTEND_IMAGE:$IMAGE_TAG" \
        -t "$FRONTEND_IMAGE:latest" \
        --build-arg BUILD_NUMBER="$BUILD_NUMBER" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        frontend/
    
    print_success "Docker images built successfully"
    
    # Save image information
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}" | grep -E "(vils|REPOSITORY)" > build-artifacts/docker-images.txt
}

# Function to scan Docker images for vulnerabilities
scan_images() {
    print_status "Scanning Docker images for vulnerabilities..."
    
    # You can integrate with tools like Trivy, Clair, or Snyk here
    # Example with Trivy (if available):
    if command_exists trivy; then
        print_status "Scanning backend image with Trivy..."
        trivy image --format json --output build-artifacts/backend-image-scan.json "$BACKEND_IMAGE:$IMAGE_TAG" || true
        
        print_status "Scanning frontend image with Trivy..."
        trivy image --format json --output build-artifacts/frontend-image-scan.json "$FRONTEND_IMAGE:$IMAGE_TAG" || true
    else
        print_warning "Trivy not found, skipping image vulnerability scanning"
    fi
    
    print_success "Image scanning completed"
}

# Function to push Docker images
push_images() {
    if [ "$PUSH_IMAGES" != "true" ]; then
        print_warning "Image pushing is disabled (PUSH_IMAGES=$PUSH_IMAGES)"
        return 0
    fi
    
    print_status "Pushing Docker images to registry..."
    
    # Push backend image
    print_status "Pushing $BACKEND_IMAGE:$IMAGE_TAG"
    docker push "$BACKEND_IMAGE:$IMAGE_TAG"
    docker push "$BACKEND_IMAGE:latest"
    
    # Push frontend image
    print_status "Pushing $FRONTEND_IMAGE:$IMAGE_TAG"
    docker push "$FRONTEND_IMAGE:$IMAGE_TAG"
    docker push "$FRONTEND_IMAGE:latest"
    
    print_success "Docker images pushed successfully"
    
    # Create image manifest
    cat > build-artifacts/image-manifest.json << EOF
{
  "build_number": "$BUILD_NUMBER",
  "build_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "git_commit": "$(git rev-parse HEAD)",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD)",
  "images": {
    "backend": {
      "repository": "$BACKEND_IMAGE",
      "tag": "$IMAGE_TAG",
      "full_name": "$BACKEND_IMAGE:$IMAGE_TAG"
    },
    "frontend": {
      "repository": "$FRONTEND_IMAGE",
      "tag": "$IMAGE_TAG",
      "full_name": "$FRONTEND_IMAGE:$IMAGE_TAG"
    }
  }
}
EOF
}

# Function to deploy to Kubernetes
deploy_to_kubernetes() {
    if [ "$DEPLOY_TO_K8S" != "true" ]; then
        print_warning "Kubernetes deployment is disabled (DEPLOY_TO_K8S=$DEPLOY_TO_K8S)"
        return 0
    fi
    
    print_status "Deploying to Kubernetes..."
    
    # Check if kubectl is available
    if ! command_exists kubectl; then
        print_error "kubectl is required for deployment but not found"
        exit 1
    fi
    
    # Update image tags in Kubernetes manifests
    print_status "Updating Kubernetes manifests with new image tags..."
    
    # Create temporary manifests with updated image tags
    mkdir -p build-artifacts/k8s-manifests
    cp -r k8s/* build-artifacts/k8s-manifests/
    
    # Update image tags in backend deployment
    sed -i "s|image: vils/backend:latest|image: $BACKEND_IMAGE:$IMAGE_TAG|g" build-artifacts/k8s-manifests/backend.yaml
    sed -i "s|image: vils/frontend:latest|image: $FRONTEND_IMAGE:$IMAGE_TAG|g" build-artifacts/k8s-manifests/frontend.yaml
    
    # Apply manifests
    kubectl apply -f build-artifacts/k8s-manifests/namespace.yaml
    kubectl apply -f build-artifacts/k8s-manifests/configmap.yaml
    kubectl apply -f build-artifacts/k8s-manifests/postgres.yaml
    kubectl apply -f build-artifacts/k8s-manifests/redis.yaml
    kubectl apply -f build-artifacts/k8s-manifests/backend.yaml
    kubectl apply -f build-artifacts/k8s-manifests/frontend.yaml
    kubectl apply -f build-artifacts/k8s-manifests/ingress.yaml
    kubectl apply -f build-artifacts/k8s-manifests/hpa.yaml
    
    # Wait for rollout
    print_status "Waiting for deployment rollout..."
    kubectl -n "$K8S_NAMESPACE" rollout status deployment/vils-backend --timeout=600s
    kubectl -n "$K8S_NAMESPACE" rollout status deployment/vils-frontend --timeout=300s
    
    print_success "Kubernetes deployment completed"
    
    # Get deployment status
    kubectl -n "$K8S_NAMESPACE" get pods > build-artifacts/k8s-pod-status.txt
    kubectl -n "$K8S_NAMESPACE" get services > build-artifacts/k8s-service-status.txt
}

# Function to run health checks after deployment
health_check() {
    print_status "Running post-deployment health checks..."
    
    if [ "$DEPLOY_TO_K8S" = "true" ]; then
        # Kubernetes health check
        print_status "Checking Kubernetes deployment health..."
        
        # Port forward to test endpoints
        kubectl -n "$K8S_NAMESPACE" port-forward svc/vils-backend-service 8000:8000 &
        PF_PID=$!
        
        sleep 10
        
        # Test health endpoint
        if curl -f http://localhost:8000/api/monitoring/health > build-artifacts/health-check.json; then
            print_success "Health check passed"
        else
            print_error "Health check failed"
            # Don't fail the build for health check failure
        fi
        
        # Kill port-forward
        kill $PF_PID || true
    fi
}

# Function to generate build report
generate_report() {
    print_status "Generating build report..."
    
    cat > build-artifacts/build-report.md << EOF
# Build Report

## Build Information
- **Build Number**: $BUILD_NUMBER
- **Build Date**: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- **Environment**: $ENVIRONMENT
- **Git Commit**: $(git rev-parse HEAD)
- **Git Branch**: $(git rev-parse --abbrev-ref HEAD)

## Images Built
- **Backend**: $BACKEND_IMAGE:$IMAGE_TAG
- **Frontend**: $FRONTEND_IMAGE:$IMAGE_TAG

## Test Results
- Backend tests: $([ -f build-artifacts/backend-test-results.xml ] && echo "✅ Passed" || echo "❌ Failed")
- Frontend tests: $([ -f build-artifacts/frontend-test-results.xml ] && echo "✅ Passed" || echo "❌ Failed")

## Security Scans
- Backend security: $([ -f build-artifacts/backend-security-scan.json ] && echo "✅ Completed" || echo "⏭️ Skipped")
- Frontend security: $([ -f build-artifacts/frontend-security-scan.json ] && echo "✅ Completed" || echo "⏭️ Skipped")
- Image vulnerability scan: $([ -f build-artifacts/backend-image-scan.json ] && echo "✅ Completed" || echo "⏭️ Skipped")

## Deployment
- Images pushed: $([ "$PUSH_IMAGES" = "true" ] && echo "✅ Yes" || echo "⏭️ No")
- Kubernetes deployment: $([ "$DEPLOY_TO_K8S" = "true" ] && echo "✅ Yes" || echo "⏭️ No")

## Artifacts
- Build artifacts are available in the \`build-artifacts\` directory
- Test reports, coverage reports, and security scan results are included
EOF

    print_success "Build report generated"
}

# Function to cleanup build environment
cleanup_build() {
    print_status "Cleaning up build environment..."
    
    # Remove temporary files
    rm -f backend/test.db
    rm -rf backend/test-venv
    
    # Logout from registry
    if [ -n "$REGISTRY_USERNAME" ]; then
        docker logout "$REGISTRY_URL" || true
    fi
    
    print_success "Cleanup completed"
}

# Main CI/CD pipeline
run_pipeline() {
    print_status "Starting VILS CI/CD pipeline..."
    print_status "Environment: $ENVIRONMENT"
    print_status "Build Number: $BUILD_NUMBER"
    print_status "Image Tag: $IMAGE_TAG"
    
    # Setup
    setup_build_env
    
    # Run tests if enabled
    if [ "$RUN_TESTS" = "true" ]; then
        test_backend
        test_frontend
        security_scan
    else
        print_warning "Tests are disabled (RUN_TESTS=$RUN_TESTS)"
    fi
    
    # Build images
    build_images
    scan_images
    
    # Push images
    push_images
    
    # Deploy to Kubernetes
    deploy_to_kubernetes
    
    # Health check
    health_check
    
    # Generate report
    generate_report
    
    # Cleanup
    cleanup_build
    
    print_success "CI/CD pipeline completed successfully!"
}

# Command handling
case "${1:-pipeline}" in
    pipeline)
        run_pipeline
        ;;
    test)
        setup_build_env
        test_backend
        test_frontend
        security_scan
        ;;
    build)
        setup_build_env
        build_images
        scan_images
        ;;
    push)
        setup_build_env
        push_images
        ;;
    deploy)
        deploy_to_kubernetes
        ;;
    health-check)
        health_check
        ;;
    report)
        generate_report
        ;;
    help|--help|-h)
        echo "VILS CI/CD Pipeline Script"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  pipeline       Run full CI/CD pipeline (default)"
        echo "  test           Run tests only"
        echo "  build          Build Docker images only"
        echo "  push           Push Docker images only"
        echo "  deploy         Deploy to Kubernetes only"
        echo "  health-check   Run health checks only"
        echo "  report         Generate build report only"
        echo "  help           Show this help message"
        echo
        echo "Environment Variables:"
        echo "  ENVIRONMENT          Build environment (default: development)"
        echo "  BUILD_NUMBER         Build number (default: timestamp)"
        echo "  REGISTRY_URL         Docker registry URL (default: docker.io)"
        echo "  REGISTRY_USERNAME    Docker registry username"
        echo "  REGISTRY_PASSWORD    Docker registry password"
        echo "  BACKEND_IMAGE        Backend image name (default: vils/backend)"
        echo "  FRONTEND_IMAGE       Frontend image name (default: vils/frontend)"
        echo "  IMAGE_TAG            Image tag (default: BUILD_NUMBER)"
        echo "  PUSH_IMAGES          Push images to registry (default: true)"
        echo "  RUN_TESTS            Run tests (default: true)"
        echo "  DEPLOY_TO_K8S        Deploy to Kubernetes (default: false)"
        echo "  K8S_NAMESPACE        Kubernetes namespace (default: vils)"
        ;;
    *)
        print_error "Unknown command: $1"
        print_status "Run '$0 help' for usage information"
        exit 1
        ;;
esac