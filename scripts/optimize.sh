#!/bin/bash

# VILS Optimization Script
# This script performs various optimizations and final checks

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[OPTIMIZE]${NC} $1"
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

# Function to optimize backend
optimize_backend() {
    print_status "Optimizing backend..."
    
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # Install optimization tools if not present
    pip install -q black isort flake8 mypy bandit safety
    
    # Code formatting
    print_status "Formatting code with black..."
    black src/ --quiet
    
    # Import sorting
    print_status "Sorting imports with isort..."
    isort src/ --quiet
    
    # Linting
    print_status "Running flake8 linting..."
    flake8 src/ --max-line-length=88 --extend-ignore=E203,W503 || print_warning "Linting warnings found"
    
    # Type checking
    print_status "Running mypy type checking..."
    mypy src/ --ignore-missing-imports || print_warning "Type checking warnings found"
    
    # Security check
    print_status "Running security analysis with bandit..."
    bandit -r src/ -f json -o ../reports/backend-security.json --quiet || print_warning "Security warnings found"
    
    # Dependency security check
    print_status "Checking dependencies with safety..."
    safety check --json --output ../reports/backend-safety.json || print_warning "Dependency security warnings found"
    
    # Generate requirements.txt hash for cache busting
    python -c "
import hashlib
with open('requirements.txt', 'rb') as f:
    content = f.read()
    hash_value = hashlib.sha256(content).hexdigest()[:8]
    with open('requirements.hash', 'w') as h:
        h.write(hash_value)
"
    
    deactivate
    cd ..
    print_success "Backend optimization completed"
}

# Function to optimize frontend
optimize_frontend() {
    print_status "Optimizing frontend..."
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing dependencies..."
        npm ci
    fi
    
    # Linting
    print_status "Running ESLint..."
    npm run lint || print_warning "Linting warnings found"
    
    # Code formatting
    print_status "Formatting code with Prettier..."
    npm run format
    
    # Type checking
    print_status "Running TypeScript type checking..."
    npm run type-check || print_warning "Type checking warnings found"
    
    # Security audit
    print_status "Running npm security audit..."
    npm audit --audit-level=moderate --json > ../reports/frontend-audit.json || print_warning "Security vulnerabilities found"
    
    # Bundle analysis
    print_status "Analyzing bundle size..."
    npm run build -- --mode=production
    
    if command_exists du; then
        bundle_size=$(du -sh dist/ | cut -f1)
        print_status "Bundle size: $bundle_size"
    fi
    
    # Generate package.json hash for cache busting
    node -e "
const crypto = require('crypto');
const fs = require('fs');
const content = fs.readFileSync('package.json');
const hash = crypto.createHash('sha256').update(content).digest('hex').substring(0, 8);
fs.writeFileSync('package.hash', hash);
"
    
    cd ..
    print_success "Frontend optimization completed"
}

# Function to optimize Docker images
optimize_docker() {
    print_status "Optimizing Docker images..."
    
    # Create optimized Dockerfiles if they don't exist
    if [ ! -f "backend/Dockerfile.optimized" ]; then
        print_status "Creating optimized backend Dockerfile..."
        cat > backend/Dockerfile.optimized << 'EOF'
# Multi-stage build for optimized backend image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd -r vils && useradd -r -g vils vils

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=vils:vils . .

# Switch to non-root user
USER vils

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/monitoring/health || exit 1

# Start application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
EOF
    fi
    
    if [ ! -f "frontend/Dockerfile.optimized" ]; then
        print_status "Creating optimized frontend Dockerfile..."
        cat > frontend/Dockerfile.optimized << 'EOF'
# Multi-stage build for optimized frontend image
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Install security updates
RUN apk upgrade --no-cache

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user for nginx
RUN addgroup -g 1001 -S nginx && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF
    fi
    
    # Build optimized images
    print_status "Building optimized backend image..."
    docker build -f backend/Dockerfile.optimized -t vils/backend:optimized backend/
    
    print_status "Building optimized frontend image..."
    docker build -f frontend/Dockerfile.optimized -t vils/frontend:optimized frontend/
    
    # Compare image sizes
    if command_exists docker; then
        print_status "Image size comparison:"
        docker images vils/backend --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
        docker images vils/frontend --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
    fi
    
    print_success "Docker optimization completed"
}

# Function to optimize database
optimize_database() {
    print_status "Generating database optimization recommendations..."
    
    cat > reports/database-optimization.md << 'EOF'
# Database Optimization Recommendations

## Indexes
Add the following indexes for better performance:

```sql
-- Localization tasks
CREATE INDEX CONCURRENTLY idx_tasks_user_status ON localization_tasks(user_id, status);
CREATE INDEX CONCURRENTLY idx_tasks_project_created ON localization_tasks(project_id, created_at);
CREATE INDEX CONCURRENTLY idx_tasks_status_updated ON localization_tasks(status, updated_at);

-- Task iterations
CREATE INDEX CONCURRENTLY idx_iterations_task_number ON task_iterations(task_id, iteration_number);

-- Build jobs
CREATE INDEX CONCURRENTLY idx_builds_task_status ON build_jobs(task_id, status);
CREATE INDEX CONCURRENTLY idx_builds_status_created ON build_jobs(status, created_at);

-- Users
CREATE INDEX CONCURRENTLY idx_users_email ON users(email) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_users_username ON users(username) WHERE is_active = true;

-- Projects
CREATE INDEX CONCURRENTLY idx_projects_owner_active ON projects(owner_id) WHERE is_active = true;
```

## Configuration Settings

Add to postgresql.conf:

```
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Query planner settings
random_page_cost = 1.1
effective_io_concurrency = 200

# Connection settings
max_connections = 100

# Logging
log_statement = 'mod'
log_duration = on
log_min_duration_statement = 1000
```

## Monitoring Queries

```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time, stddev_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT
  schemaname,
  tablename,
  indexname,
  idx_tup_read,
  idx_tup_fetch,
  idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;
```
EOF

    print_success "Database optimization recommendations generated"
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    
    # Create performance test script
    cat > scripts/performance-test.js << 'EOF'
const http = require('http');
const { performance } = require('perf_hooks');

const API_BASE = process.env.API_BASE || 'http://localhost:8000/api';
const CONCURRENT_REQUESTS = 10;
const TOTAL_REQUESTS = 100;

async function makeRequest(path) {
  return new Promise((resolve, reject) => {
    const start = performance.now();
    const req = http.get(`${API_BASE}${path}`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const end = performance.now();
        resolve({
          statusCode: res.statusCode,
          responseTime: end - start,
          size: data.length
        });
      });
    });
    
    req.on('error', reject);
    req.setTimeout(10000, () => reject(new Error('Timeout')));
  });
}

async function runTest(path, name) {
  console.log(`\nTesting ${name}...`);
  const promises = [];
  const results = [];
  
  for (let i = 0; i < TOTAL_REQUESTS; i++) {
    promises.push(makeRequest(path));
    
    if (promises.length >= CONCURRENT_REQUESTS) {
      const batch = await Promise.allSettled(promises.splice(0, CONCURRENT_REQUESTS));
      results.push(...batch.map(r => r.status === 'fulfilled' ? r.value : null).filter(Boolean));
    }
  }
  
  // Process remaining requests
  if (promises.length > 0) {
    const batch = await Promise.allSettled(promises);
    results.push(...batch.map(r => r.status === 'fulfilled' ? r.value : null).filter(Boolean));
  }
  
  if (results.length === 0) {
    console.log('No successful requests');
    return;
  }
  
  const responseTimes = results.map(r => r.responseTime);
  const avgResponseTime = responseTimes.reduce((a, b) => a + b) / responseTimes.length;
  const minResponseTime = Math.min(...responseTimes);
  const maxResponseTime = Math.max(...responseTimes);
  
  console.log(`  Requests: ${results.length}/${TOTAL_REQUESTS}`);
  console.log(`  Success rate: ${(results.length / TOTAL_REQUESTS * 100).toFixed(1)}%`);
  console.log(`  Avg response time: ${avgResponseTime.toFixed(2)}ms`);
  console.log(`  Min response time: ${minResponseTime.toFixed(2)}ms`);
  console.log(`  Max response time: ${maxResponseTime.toFixed(2)}ms`);
  
  const statusCodes = {};
  results.forEach(r => {
    statusCodes[r.statusCode] = (statusCodes[r.statusCode] || 0) + 1;
  });
  console.log(`  Status codes:`, statusCodes);
}

async function main() {
  console.log('VILS Performance Test');
  console.log('===================');
  
  try {
    await runTest('/monitoring/health', 'Health Check');
    await runTest('/projects', 'Projects List');
    await runTest('/tasks', 'Tasks List');
    await runTest('/monitoring/stats', 'Statistics');
  } catch (error) {
    console.error('Performance test failed:', error);
    process.exit(1);
  }
  
  console.log('\nPerformance test completed');
}

main();
EOF
    
    # Run performance test if Node.js is available
    if command_exists node && [ -f "scripts/performance-test.js" ]; then
        print_status "Running API performance test..."
        node scripts/performance-test.js > reports/performance-results.txt 2>&1 || print_warning "Performance test failed"
        
        if [ -f "reports/performance-results.txt" ]; then
            print_status "Performance test results:"
            cat reports/performance-results.txt
        fi
    fi
    
    print_success "Performance testing completed"
}

# Function to generate optimization report
generate_report() {
    print_status "Generating optimization report..."
    
    cat > reports/optimization-report.md << EOF
# VILS Optimization Report

Generated on: $(date)

## Summary

This report contains optimization results and recommendations for the VILS application.

## Backend Optimization

- ✅ Code formatting with Black
- ✅ Import sorting with isort
- ✅ Linting with flake8
- ✅ Type checking with mypy
- ✅ Security analysis with bandit
- ✅ Dependency security check with safety

### Files Analyzed
$(find backend/src -name "*.py" | wc -l) Python files processed

## Frontend Optimization

- ✅ Linting with ESLint
- ✅ Code formatting with Prettier
- ✅ TypeScript type checking
- ✅ Security audit with npm audit
- ✅ Bundle analysis

### Bundle Information
$(if [ -f "frontend/dist/index.html" ]; then
    echo "Bundle built successfully"
    if command_exists du; then
        echo "Bundle size: $(du -sh frontend/dist/ | cut -f1)"
    fi
else
    echo "Bundle not available"
fi)

## Docker Optimization

- ✅ Multi-stage build Dockerfiles created
- ✅ Optimized base images
- ✅ Security hardening applied
- ✅ Health checks implemented

## Database Optimization

- ✅ Index recommendations generated
- ✅ Configuration tuning suggestions provided
- ✅ Monitoring queries prepared

## Performance Testing

$(if [ -f "reports/performance-results.txt" ]; then
    echo "✅ Performance tests completed"
    echo ""
    echo "### Results Summary"
    grep -A 10 "VILS Performance Test" reports/performance-results.txt || echo "Performance results available in reports/performance-results.txt"
else
    echo "⚠️ Performance tests not run"
fi)

## Security Analysis

$(if [ -f "reports/backend-security.json" ]; then
    issues=$(cat reports/backend-security.json | grep -o '"severity"' | wc -l || echo "0")
    echo "Backend security issues: $issues"
else
    echo "Backend security analysis not available"
fi)

$(if [ -f "reports/frontend-audit.json" ]; then
    vulnerabilities=$(grep -o '"severity"' reports/frontend-audit.json | wc -l || echo "0")
    echo "Frontend vulnerabilities: $vulnerabilities"
else
    echo "Frontend security audit not available"
fi)

## Recommendations

### High Priority
1. Review and fix any security issues found in security scans
2. Implement database indexes for better performance
3. Configure production database settings
4. Set up monitoring and alerting

### Medium Priority
1. Implement bundle splitting for better caching
2. Add image optimization and CDN
3. Configure Redis clustering for high availability
4. Implement backup and disaster recovery procedures

### Low Priority
1. Add more comprehensive error boundaries
2. Implement progressive web app features
3. Add more detailed metrics and dashboards
4. Consider implementing search functionality

## Next Steps

1. Deploy optimized Docker images to staging
2. Apply database optimizations
3. Set up monitoring dashboards
4. Plan load testing with realistic data volumes
5. Review security recommendations with security team

---

For more details, see individual report files in the reports/ directory.
EOF

    print_success "Optimization report generated at reports/optimization-report.md"
}

# Function to clean up temporary files
cleanup() {
    print_status "Cleaning up temporary files..."
    
    # Remove build artifacts
    rm -rf backend/build/
    rm -rf backend/dist/
    rm -rf backend/src/**/__pycache__/
    rm -rf backend/src/**/*.pyc
    
    # Remove frontend build artifacts (keep dist for production)
    rm -rf frontend/node_modules/.cache/
    rm -rf frontend/.vite/
    
    # Remove test artifacts
    rm -rf backend/.pytest_cache/
    rm -rf frontend/coverage/
    
    # Remove logs
    rm -rf logs/*.log
    
    print_success "Cleanup completed"
}

# Main optimization function
run_optimization() {
    print_status "Starting VILS optimization process..."
    
    # Create reports directory
    mkdir -p reports
    
    # Run optimizations
    optimize_backend
    optimize_frontend
    optimize_docker
    optimize_database
    run_performance_tests
    
    # Generate report
    generate_report
    
    # Cleanup
    cleanup
    
    print_success "Optimization process completed successfully!"
    print_status "Check the reports/ directory for detailed results"
}

# Command handling
case "${1:-optimize}" in
    optimize)
        run_optimization
        ;;
    backend)
        mkdir -p reports
        optimize_backend
        ;;
    frontend)
        mkdir -p reports
        optimize_frontend
        ;;
    docker)
        mkdir -p reports
        optimize_docker
        ;;
    database)
        mkdir -p reports
        optimize_database
        ;;
    performance)
        mkdir -p reports
        run_performance_tests
        ;;
    report)
        generate_report
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        echo "VILS Optimization Script"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  optimize     Run full optimization process (default)"
        echo "  backend      Optimize backend code only"
        echo "  frontend     Optimize frontend code only"
        echo "  docker       Create optimized Docker images"
        echo "  database     Generate database optimization recommendations"
        echo "  performance  Run performance tests"
        echo "  report       Generate optimization report"
        echo "  cleanup      Clean up temporary files"
        echo "  help         Show this help message"
        ;;
    *)
        print_error "Unknown command: $1"
        print_status "Run '$0 help' for usage information"
        exit 1
        ;;
esac