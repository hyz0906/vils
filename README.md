# VILS - Version Issue Locator System

[![Build Status](https://github.com/yourusername/vils/workflows/CI/badge.svg)](https://github.com/yourusername/vils/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue.svg)](https://kubernetes.io)

VILS is a production-ready application that helps developers identify problematic commits in their codebase using an intelligent binary search algorithm. It automates the process of finding the exact commit that introduced a bug or regression by systematically testing commits between known good and bad states.

## 🌟 Key Features

### Core Functionality
- **🔍 Intelligent Binary Search**: Automatically generates 10 evenly distributed candidate commits per iteration
- **🏗️ Multi-Platform Build Support**: Integrates with Jenkins, GitHub Actions, and GitLab CI
- **📊 Real-time Progress Tracking**: WebSocket-powered live updates and interactive visualization
- **👥 Multi-User Support**: User authentication, project ownership, and task management
- **🎯 Interactive Testing**: Manual test result submission with visual commit selection

### Technical Excellence
- **🚀 Production-Ready**: Comprehensive monitoring, logging, and error handling
- **📈 Scalable Architecture**: Kubernetes deployment with horizontal pod autoscaling
- **🔐 Enterprise Security**: JWT authentication, encrypted secrets, and secure API endpoints
- **⚡ High Performance**: Redis caching, async operations, and optimized database queries
- **🧪 Thoroughly Tested**: Unit tests, integration tests, and end-to-end testing

### Developer Experience
- **🎨 Modern UI**: Responsive Vue.js 3 interface with Tailwind CSS
- **📱 Mobile-Friendly**: Fully responsive design for all devices
- **🛠️ Development Tools**: Hot reloading, automated scripts, and comprehensive tooling
- **📚 Complete Documentation**: API docs, deployment guides, and examples

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Background    │
│   Vue.js 3      │◄──►│   FastAPI       │◄──►│   Workers       │
│   TypeScript    │    │   Python 3.11   │    │   Celery        │
│   Tailwind CSS │    │   SQLAlchemy    │    │   Redis         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐             │
         └──────────────►│   PostgreSQL    │◄────────────┘
                        │   Database      │
                        └─────────────────┘
```

### Technology Stack

#### Backend
- **FastAPI**: Modern, fast web framework for APIs
- **PostgreSQL**: Robust relational database with JSONB support
- **Redis**: In-memory data store for caching and message brokering
- **Celery**: Distributed task queue for background processing
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool
- **Prometheus**: Metrics collection and monitoring

#### Frontend
- **Vue.js 3**: Progressive JavaScript framework with Composition API
- **TypeScript**: Type-safe JavaScript development
- **Pinia**: State management for Vue applications
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Fast build tool and development server
- **Vitest**: Unit testing framework

#### DevOps & Infrastructure
- **Docker**: Containerization platform
- **Kubernetes**: Container orchestration
- **Nginx**: Reverse proxy and load balancer
- **Let's Encrypt**: SSL certificate management

## 🚀 Quick Start

### Prerequisites
- **Docker** and **Docker Compose**
- **Node.js** 18+ and **npm**
- **Python** 3.11+ and **pip**
- **Git** for version control

### Option 1: Docker Compose (Recommended for local development)

```bash
# Clone the repository
git clone https://github.com/yourusername/vils.git
cd vils

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access the application
open http://localhost:3000
```

### Option 2: Local Development Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/vils.git
cd vils

# Setup development environment
./scripts/local-dev.sh setup

# Start services
./scripts/local-dev.sh start

# Run migrations
./scripts/local-dev.sh migrate
```

### Option 3: Standalone Frontend Demo

```bash
cd frontend

# Install dependencies
npm install

# Run in demo mode with mock data
npm run demo

# Access demo at http://localhost:5173
```

## 📖 Usage Guide

### Creating a Localization Task

1. **Login** to the VILS application
2. **Navigate** to the Projects section and create or select a project
3. **Click** "New Localization Task"
4. **Fill in** the task details:
   - **Description**: Brief description of the issue
   - **Good Commit**: Known working commit hash
   - **Bad Commit**: Known broken commit hash
   - **Build Command**: Command to build the project
   - **Test Command**: Command to test for the issue

5. **Submit** the task and watch the binary search progress

### Binary Search Process

The system automatically:
1. **Analyzes** the commit range between good and bad commits
2. **Generates** 10 evenly distributed candidate commits
3. **Highlights** the middle candidate for testing
4. **Waits** for your test result (Pass/Fail)
5. **Narrows** the search range based on your input
6. **Repeats** until the problematic commit is identified

### Testing Candidates

1. **Review** the highlighted commit in the visualization
2. **Run** your tests against that specific commit
3. **Click** "Pass" if tests succeed, "Fail" if they don't
4. **Continue** until the search completes

## 🔧 Configuration

### Environment Variables

#### Backend Configuration
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/vils_db

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_MASTER_KEY=your-encryption-key-here

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# External Services
JENKINS_URL=https://jenkins.example.com
JENKINS_TOKEN=your-jenkins-token
GITHUB_TOKEN=your-github-token
```

#### Frontend Configuration
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
VITE_USE_MOCK_API=false
```

### Build Service Integration

#### Jenkins
```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'make build'
            }
        }
        stage('Test') {
            steps {
                sh 'make test'
            }
        }
    }
}
```

#### GitHub Actions
```yaml
name: VILS Integration
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build
      run: make build
    - name: Test
      run: make test
```

## 🏭 Production Deployment

### Kubernetes Deployment

```bash
# Build and push images
./scripts/ci-cd.sh build
PUSH_IMAGES=true ./scripts/ci-cd.sh push

# Deploy to Kubernetes
./scripts/deploy.sh deploy

# Check deployment status
./scripts/deploy.sh status
```

### Docker Swarm Deployment

```bash
# Initialize swarm (if not already done)
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml vils

# Check services
docker service ls
```

### Manual Deployment

See [docs/deployment.md](docs/deployment.md) for detailed manual deployment instructions.

## 🧪 Testing

### Running Tests Locally

```bash
# Run all tests
./scripts/local-dev.sh test

# Run backend tests only
./scripts/local-dev.sh test backend

# Run frontend tests only
./scripts/local-dev.sh test frontend

# Run tests with coverage
cd backend && pytest --cov=src --cov-report=html
cd frontend && npm run test:coverage
```

### Test Structure

```
tests/
├── backend/
│   ├── unit/          # Unit tests for individual functions
│   ├── integration/   # API endpoint tests
│   └── e2e/          # End-to-end workflow tests
├── frontend/
│   ├── unit/          # Component and store unit tests
│   ├── integration/   # User workflow tests
│   └── e2e/          # Playwright browser tests
└── fixtures/         # Test data and mocks
```

## 📊 Monitoring & Observability

### Health Checks
- **Backend**: `GET /api/monitoring/health`
- **Frontend**: Available via load balancer health checks
- **Database**: Connection pool monitoring
- **Redis**: Memory usage and connection tracking

### Metrics
- **Prometheus**: Available at `/api/monitoring/metrics`
- **Grafana**: Dashboard templates in `monitoring/grafana/`
- **Custom Metrics**: Task completion rates, search efficiency, user activity

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Log Aggregation**: ELK stack or similar centralized logging
- **Error Tracking**: Sentry integration for error monitoring

## 🔧 Development

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/vils.git
cd vils

# Setup development environment
./scripts/local-dev.sh setup

# Start development servers
./scripts/local-dev.sh start

# View logs
./scripts/local-dev.sh logs backend
```

### Code Quality

```bash
# Backend
cd backend
black src/                    # Code formatting
isort src/                    # Import sorting
flake8 src/                   # Linting
mypy src/                     # Type checking

# Frontend
cd frontend
npm run lint                  # ESLint
npm run format                # Prettier
npm run type-check            # TypeScript checking
```

### Database Migrations

```bash
# Create new migration
./scripts/local-dev.sh migration "Add new table"

# Run migrations
./scripts/local-dev.sh migrate

# Rollback migration
cd backend && alembic downgrade -1
```

## 📚 API Documentation

### Interactive API Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

### Key Endpoints

#### Authentication
```http
POST /api/auth/login
POST /api/auth/register
POST /api/auth/refresh
DELETE /api/auth/logout
```

#### Projects
```http
GET    /api/projects          # List projects
POST   /api/projects          # Create project
GET    /api/projects/{id}     # Get project
PUT    /api/projects/{id}     # Update project
DELETE /api/projects/{id}     # Delete project
```

#### Localization Tasks
```http
GET    /api/tasks             # List tasks
POST   /api/tasks             # Create task
GET    /api/tasks/{id}        # Get task details
POST   /api/tasks/{id}/result # Submit test result
DELETE /api/tasks/{id}        # Cancel/delete task
```

### WebSocket Events
```json
{
  "type": "task_update",
  "data": {
    "task_id": "uuid",
    "status": "running",
    "current_iteration": 3,
    "current_candidates": ["commit1", "commit2", "commit3"]
  }
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `./scripts/local-dev.sh test`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Standards
- **Backend**: Follow PEP 8, use type hints, write docstrings
- **Frontend**: Follow Vue.js style guide, use TypeScript, write JSDoc comments
- **Testing**: Maintain >90% test coverage for new code
- **Documentation**: Update docs for any API or feature changes

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Error
```bash
# Check database status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Reset database
./scripts/local-dev.sh reset-db
```

#### Frontend Build Issues
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check for version conflicts
npm ls
```

#### WebSocket Connection Issues
```bash
# Check backend logs
./scripts/local-dev.sh logs backend

# Test WebSocket endpoint
wscat -c ws://localhost:8000/ws
```

### Performance Optimization

#### Database Optimization
- **Indexing**: Ensure proper indexes on frequently queried columns
- **Connection Pooling**: Tune pool size based on load
- **Query Optimization**: Use EXPLAIN ANALYZE for slow queries

#### Frontend Optimization
- **Bundle Analysis**: `npm run build:analyze`
- **Lazy Loading**: Implement route-based code splitting
- **Caching**: Configure proper browser caching headers

#### Redis Optimization
- **Memory Usage**: Monitor with `redis-cli info memory`
- **Key Expiration**: Set appropriate TTL values
- **Persistence**: Configure based on durability requirements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Binary Search Algorithm**: Inspired by Git's bisect functionality
- **UI Design**: Built with modern design principles and accessibility in mind
- **Architecture**: Follows microservices and clean architecture patterns
- **Testing**: Comprehensive test coverage following testing best practices

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/vils/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/vils/discussions)
- **Email**: support@vils.example.com

---

**VILS** - Making commit localization intelligent and efficient. 🎯
