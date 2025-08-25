# Claude.md

A comprehensive guide for AI-assisted development with Claude on Python and TypeScript projects.

## Quick Start

This document serves as a reference for effectively collaborating with Claude AI on software development projects. Keep this file in your project root for optimal AI assistance.

## Project Context

**Project Type:** [Python/TypeScript/Go/Rust/Full-Stack]  
**Framework:** [Django/Flask/FastAPI/React/Next.js/Node.js/Gin/Echo/Actix/Axum/etc.]  
**Last Updated:** [Date]

## Development Guidelines

### Code Standards

**Python Projects:**
- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Implement proper error handling with try/except blocks
- Use virtual environments (venv/conda)
- Prefer f-strings for string formatting
- Use meaningful variable and function names

**TypeScript Projects:**
- Use strict TypeScript configuration
- Implement proper type definitions
- Follow ESLint and Prettier configurations
- Use async/await for asynchronous operations
- Implement proper error boundaries in React
- Use meaningful interface and type names

**Go Projects:**
- Follow Go conventions (gofmt, golint)
- Use meaningful package and function names
- Implement proper error handling with explicit error returns
- Follow Go module structure
- Use interfaces for abstraction
- Write clear and concise comments

**Rust Projects:**
- Use cargo fmt for consistent formatting
- Follow Rust naming conventions (snake_case, CamelCase)
- Use Result<T, E> for error handling
- Implement proper ownership and borrowing
- Use clippy for linting recommendations
- Write comprehensive documentation with ///

### File Structure Preferences

**Python/Django:**
```
project-root/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
├── .env.example   # Environment variables template
├── requirements.txt
├── README.md
└── claude.md      # This file
```

**TypeScript/Node.js:**
```
project-root/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
├── .env.example   # Environment variables template
├── package.json
├── README.md
└── claude.md      # This file
```

**Go:**
```
project-root/
├── cmd/           # Main applications
├── internal/      # Private application code
├── pkg/           # Public library code
├── api/           # API definitions
├── web/           # Web application assets
├── configs/       # Configuration files
├── test/          # Test files
├── docs/          # Documentation
├── go.mod
├── go.sum
├── README.md
└── claude.md      # This file
```

**Rust:**
```
project-root/
├── src/           # Source code
│   ├── main.rs    # Main binary
│   └── lib.rs     # Library root
├── tests/         # Integration tests
├── benches/       # Benchmarks
├── examples/      # Example code
├── docs/          # Documentation
├── Cargo.toml     # Package manifest
├── Cargo.lock     # Lock file
├── README.md
└── claude.md      # This file
```

### Git Workflow

**Commit Message Format:**
```
<type>(<scope>): <description>

<body>

<footer>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Example:**
```bash
git add .
git commit -m "feat(auth): implement JWT authentication middleware

- Add JWT token generation and validation
- Create auth middleware for protected routes  
- Update user model with token refresh logic

Closes #123"
git push origin main
```

### Language-Specific Commit Examples

**Python:**
```bash
git commit -m "feat(api): add user registration endpoint with email validation"
```

**TypeScript:**
```bash
git commit -m "feat(components): implement responsive navigation component"
```

**Go:**
```bash
git commit -m "feat(handler): add health check endpoint with database ping"
```

**Rust:**
```bash
git commit -m "feat(parser): implement JSON configuration parser with error handling"
```

## Claude Interaction Patterns

### Effective Prompting

**DO:**
- Provide specific context about the current task
- Include relevant code snippets
- Mention the framework/library versions
- Specify desired output format
- Ask for explanations of complex logic

**Example:**
```
I'm working on a FastAPI project with SQLAlchemy. I need to create a user registration endpoint that validates email format and checks for duplicate users. Please include proper error handling and type hints.
```

**Go Example:**
```
I'm building a REST API with Gin framework and GORM. I need to implement a middleware for JWT authentication that validates tokens and adds user context to requests. Please include proper error handling and struct definitions.
```

**Rust Example:**
```
I'm developing a web service using Axum and Tokio. I need to create an async function that processes file uploads, validates file types, and stores metadata in PostgreSQL. Please include proper error handling with custom error types.
```

**DON'T:**
- Ask vague questions like "fix my code"
- Omit important context about the project structure
- Request deprecated or insecure practices

### Code Review Requests

When asking Claude to review code:

1. **Provide context:** What does this code do?
2. **Specify concerns:** Performance, security, readability?
3. **Include dependencies:** What libraries are being used?
4. **Ask specific questions:** "Is this the most efficient approach?"

### Debugging Assistance

Structure debugging requests:

1. **Problem description:** What's not working?
2. **Expected behavior:** What should happen?
3. **Current behavior:** What actually happens?
4. **Error messages:** Full stack trace if available
5. **Environment:** Python/Node version, OS, dependencies

## Common Tasks

### Project Setup
- "Help me set up a new [Python/TypeScript] project with [framework]"
- "Create a proper project structure for [project type]"
- "Generate a comprehensive requirements.txt/package.json"

### Code Generation
- "Create a [component/function/class] that does [specific task]"
- "Write tests for this [function/component]"
- "Generate API endpoints for [resource] with CRUD operations"

### Code Optimization
- "Optimize this function for better performance"
- "Refactor this code to be more readable"
- "Make this code more maintainable"

### Documentation
- "Generate docstrings for these functions"
- "Create API documentation for these endpoints"
- "Write a README section for [feature]"

## Environment Setup

### Python
```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Dependencies
pip install -r requirements.txt
pip freeze > requirements.txt
```

### TypeScript/Node.js
```bash
# Initialize project
npm init -y
npm install typescript @types/node ts-node

# Development dependencies
npm install -D nodemon eslint prettier

# Run development server
npm run dev
```

### Go
```bash
# Initialize module
go mod init github.com/username/project-name

# Install dependencies
go get github.com/gin-gonic/gin
go get gorm.io/gorm

# Run application
go run main.go

# Build binary
go build -o app main.go

# Format code
go fmt ./...

# Run tests
go test ./...
```

### Rust
```bash
# Create new project
cargo new project-name
cd project-name

# Add dependencies to Cargo.toml
cargo add tokio --features full
cargo add serde --features derive

# Run application
cargo run

# Build release
cargo build --release

# Format code
cargo fmt

# Run tests
cargo test

# Run clippy (linter)
cargo clippy
```

## Testing Guidelines

### Python Testing
```python
# pytest example
import pytest
from src.main import calculate_total

def test_calculate_total():
    assert calculate_total([1, 2, 3]) == 6
    assert calculate_total([]) == 0
```

### TypeScript Testing
```typescript
// Jest example
import { calculateTotal } from '../src/utils';

describe('calculateTotal', () => {
  test('should sum array of numbers', () => {
    expect(calculateTotal([1, 2, 3])).toBe(6);
    expect(calculateTotal([])).toBe(0);
  });
});
```

### Go Testing
```go
// main_test.go
package main

import (
    "testing"
)

func TestCalculateTotal(t *testing.T) {
    tests := []struct {
        name     string
        numbers  []int
        expected int
    }{
        {"sum positive numbers", []int{1, 2, 3}, 6},
        {"empty slice", []int{}, 0},
        {"single number", []int{5}, 5},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := CalculateTotal(tt.numbers)
            if result != tt.expected {
                t.Errorf("CalculateTotal() = %v, want %v", result, tt.expected)
            }
        })
    }
}
```

### Rust Testing
```rust
// src/lib.rs
pub fn calculate_total(numbers: &[i32]) -> i32 {
    numbers.iter().sum()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calculate_total() {
        assert_eq!(calculate_total(&[1, 2, 3]), 6);
        assert_eq!(calculate_total(&[]), 0);
        assert_eq!(calculate_total(&[5]), 5);
    }

    #[test]
    fn test_calculate_total_negative() {
        assert_eq!(calculate_total(&[-1, -2, -3]), -6);
    }
}
```

## Security Considerations

### Python
- Use environment variables for sensitive data
- Validate all user inputs
- Use parameterized queries for database operations
- Implement proper authentication and authorization
- Keep dependencies updated

### TypeScript
- Sanitize user inputs
- Use HTTPS for all API calls
- Implement proper CORS policies
- Validate data on both client and server side
- Use secure headers

### Go
- Use context for request timeouts and cancellation
- Validate and sanitize all inputs
- Use prepared statements for database queries
- Implement proper middleware for authentication
- Handle errors explicitly and securely

### Rust
- Leverage Rust's memory safety by default
- Use strong typing for input validation
- Implement proper error handling with Result types
- Use secure random number generation
- Validate all external inputs and data

## Performance Best Practices

### Python
- Use list comprehensions for simple iterations
- Implement proper database indexing
- Use async/await for I/O operations
- Profile code with cProfile when needed
- Cache expensive computations

### TypeScript
- Use React.memo() for component optimization
- Implement proper state management
- Lazy load components when appropriate
- Optimize bundle size with tree shaking
- Use proper TypeScript compiler options

### Go
- Use goroutines for concurrent operations
- Implement connection pooling for databases
- Use sync.Pool for object reuse
- Profile with pprof when needed
- Minimize memory allocations in hot paths

### Rust
- Use zero-cost abstractions where possible
- Leverage ownership system to avoid unnecessary allocations
- Use async/await for I/O-bound operations
- Profile with cargo flamegraph
- Use Vec with pre-allocated capacity when size is known

## Deployment Checklist

- [ ] Environment variables configured
- [ ] Dependencies updated and locked
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Security checks completed
- [ ] Performance benchmarks met
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Backup strategies in place
- [ ] Monitoring set up

## Useful Commands

### Git Commands
```bash
# Quick commit and push
git add -A && git commit -m "feat: description" && git push

# Create and switch to new branch
git checkout -b feature/new-feature

# Merge branch and cleanup
git checkout main && git merge feature/new-feature && git branch -d feature/new-feature
```

### Python Commands
```bash
# Format code
black src/
isort src/

# Type checking
mypy src/

# Run tests
pytest tests/ -v
```

### TypeScript Commands
```bash
# Format code
npx prettier --write src/
npx eslint src/ --fix

# Type checking
npx tsc --noEmit

# Run tests
npm test
```

### Go Commands
```bash
# Format code
go fmt ./...
goimports -w .

# Vet code
go vet ./...

# Run tests with coverage
go test -cover ./...

# Build for different platforms
GOOS=linux GOARCH=amd64 go build -o app-linux main.go
```

### Rust Commands
```bash
# Format code
cargo fmt

# Lint code
cargo clippy -- -D warnings

# Run tests with output
cargo test -- --nocapture

# Build with optimizations
cargo build --release

# Generate documentation
cargo doc --open
```

## Notes for Claude

- Always consider the specific project type and framework when providing suggestions
- Include error handling in all code examples
- Provide clear explanations for complex concepts
- Suggest improvements for code quality and maintainability
- Consider performance implications of suggested solutions
- Include relevant testing approaches when appropriate

## Project-Specific Notes

[Add project-specific information here such as:]
- Custom coding conventions
- Specific libraries or frameworks in use
- Database schema considerations  
- API design patterns
- Deployment requirements
- Team preferences

---

