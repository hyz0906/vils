# Contributing to VILS

Thank you for your interest in contributing to VILS (Version Issue Locator System)! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submission Guidelines](#submission-guidelines)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

### Prerequisites

- **Git** for version control
- **Docker** and **Docker Compose** for local development
- **Node.js** 18+ and **npm** for frontend development
- **Python** 3.11+ and **pip** for backend development

### Setting Up Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/vils.git
   cd vils
   ```

3. **Set up the development environment**:
   ```bash
   ./scripts/local-dev.sh setup
   ```

4. **Start the development servers**:
   ```bash
   ./scripts/local-dev.sh start
   ```

5. **Run database migrations**:
   ```bash
   ./scripts/local-dev.sh migrate
   ```

6. **Verify the setup** by accessing:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Backend Health: http://localhost:8000/api/monitoring/health

## Development Process

### Workflow

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards
3. **Write or update tests** for your changes
4. **Run the test suite** to ensure nothing breaks:
   ```bash
   ./scripts/local-dev.sh test
   ```

5. **Run code quality checks**:
   ```bash
   ./scripts/optimize.sh backend
   ./scripts/optimize.sh frontend
   ```

6. **Commit your changes** with a descriptive message:
   ```bash
   git commit -m "feat: add support for GitLab CI integration"
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request** on GitHub

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(api): add support for GitLab CI webhooks
fix(ui): resolve binary search visualization alignment issue
docs(readme): update deployment instructions
test(backend): add tests for localization task creation
```

### Branch Naming

Use descriptive branch names with prefixes:
- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation
- `refactor/` for refactoring
- `test/` for test-related changes

Examples:
- `feature/gitlab-integration`
- `fix/websocket-connection-issue`
- `docs/api-documentation-update`

## Coding Standards

### Backend (Python)

#### Code Style
- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://isort.readthedocs.io/) for import sorting
- Maximum line length: 88 characters

#### Type Hints
- Use type hints for all function parameters and return values
- Use `typing` module for complex types
- Example:
  ```python
  from typing import List, Optional, Dict, Any

  def create_task(
      project_id: str,
      description: str,
      good_commit: str,
      bad_commit: str
  ) -> Dict[str, Any]:
      # Implementation here
      pass
  ```

#### Documentation
- Use docstrings for all modules, classes, and functions
- Follow [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) docstrings
- Example:
  ```python
  def generate_candidates(commits: List[str], iteration: int) -> List[str]:
      """Generate candidate commits for binary search iteration.
      
      Args:
          commits: List of commit hashes to search through
          iteration: Current iteration number
      
      Returns:
          List of exactly 10 candidate commit hashes
          
      Raises:
          ValueError: If commits list is empty or invalid
      """
      # Implementation here
      pass
  ```

#### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Log errors appropriately
- Example:
  ```python
  from src.core.logging import get_logger

  logger = get_logger(__name__)

  try:
      result = perform_operation()
  except SpecificError as e:
      logger.error("Operation failed", error=str(e), context={"param": value})
      raise HTTPException(status_code=400, detail="Operation failed")
  ```

### Frontend (TypeScript/Vue.js)

#### Code Style
- Follow [Vue.js Style Guide](https://vuejs.org/style-guide/)
- Use [ESLint](https://eslint.org/) for linting
- Use [Prettier](https://prettier.io/) for code formatting
- Use TypeScript strict mode

#### Component Structure
- Use Composition API with `<script setup>`
- Define prop types explicitly
- Use meaningful component and prop names
- Example:
  ```vue
  <script setup lang="ts">
  interface Props {
    task: LocalizationTask
    isLoading?: boolean
  }

  interface Emits {
    (e: 'select-candidate', candidate: string): void
    (e: 'submit-result', result: TestResult): void
  }

  const props = withDefaults(defineProps<Props>(), {
    isLoading: false
  })

  const emit = defineEmits<Emits>()
  </script>
  ```

#### State Management
- Use Pinia for state management
- Keep stores focused and single-responsibility
- Use TypeScript for store definitions
- Example:
  ```typescript
  export const useTaskStore = defineStore('tasks', () => {
    const tasks = ref<LocalizationTask[]>([])
    const isLoading = ref(false)
    const error = ref<string | null>(null)

    const fetchTasks = async (): Promise<void> => {
      // Implementation here
    }

    return {
      tasks: readonly(tasks),
      isLoading: readonly(isLoading),
      error: readonly(error),
      fetchTasks
    }
  })
  ```

#### Documentation
- Use JSDoc comments for functions and interfaces
- Document complex logic and business rules
- Example:
  ```typescript
  /**
   * Calculates the next set of candidates for binary search
   * @param commits - Array of all commits in the range
   * @param goodCommit - Known good commit hash
   * @param badCommit - Known bad commit hash
   * @returns Array of exactly 10 candidate commits
   */
  function calculateCandidates(
    commits: string[],
    goodCommit: string,
    badCommit: string
  ): string[] {
    // Implementation here
  }
  ```

### Database

#### Migrations
- Always create migrations for schema changes
- Use descriptive migration names
- Include both upgrade and downgrade operations
- Test migrations on sample data

#### Naming Conventions
- Tables: snake_case, plural (e.g., `localization_tasks`)
- Columns: snake_case (e.g., `created_at`, `user_id`)
- Indexes: `idx_tablename_columns` (e.g., `idx_tasks_user_status`)
- Foreign keys: `fk_tablename_referenced` (e.g., `fk_tasks_user`)

## Testing Guidelines

### Backend Testing

#### Test Structure
```
backend/tests/
├── unit/           # Unit tests for individual functions/classes
├── integration/    # API endpoint tests
├── e2e/           # End-to-end workflow tests
└── fixtures/      # Test data and mocks
```

#### Writing Tests
- Use pytest for testing framework
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies
- Example:
  ```python
  def test_generate_candidates_returns_ten_commits():
      # Arrange
      commits = [f"commit{i}" for i in range(100)]
      
      # Act
      candidates = generate_candidates(commits, iteration=1)
      
      # Assert
      assert len(candidates) == 10
      assert all(commit in commits for commit in candidates)
  ```

#### Test Coverage
- Aim for >90% test coverage for new code
- Test both happy path and edge cases
- Include tests for error conditions

### Frontend Testing

#### Test Structure
```
frontend/src/
├── components/
│   └── __tests__/     # Component tests
├── stores/
│   └── __tests__/     # Store tests
└── test/
    ├── __tests__/
    │   └── integration/  # Integration tests
    └── utils.ts          # Test utilities
```

#### Writing Tests
- Use Vitest for unit testing
- Use Vue Test Utils for component testing
- Test user interactions and state changes
- Example:
  ```typescript
  describe('BinarySearchVisualization', () => {
    it('should highlight middle candidate by default', () => {
      const wrapper = mountComponent(BinarySearchVisualization, {
        props: { task: mockTask }
      })

      const candidates = wrapper.findAll('[data-testid="candidate-item"]')
      const middleCandidate = candidates[Math.floor(candidates.length / 2)]
      
      expect(middleCandidate.classes()).toContain('highlighted')
    })
  })
  ```

### Integration Testing
- Test complete user workflows
- Test API integrations
- Test WebSocket communications
- Use realistic test data

## Submission Guidelines

### Pull Request Requirements

#### Before Submitting
- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests cover the changes
- [ ] Documentation is updated
- [ ] Commit messages follow conventional format
- [ ] No merge conflicts with main branch

#### Pull Request Description
Use this template:

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran and their results.

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective
- [ ] New and existing unit tests pass locally
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: Maintainers review the code
3. **Testing**: Changes are tested in staging environment
4. **Approval**: At least one maintainer approval required
5. **Merge**: Changes are merged into main branch

### Review Criteria

Reviewers will check:
- Code quality and style
- Test coverage and quality
- Documentation completeness
- Performance implications
- Security considerations
- Backward compatibility

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General discussions and questions
- **Pull Requests**: Code reviews and discussions

### Getting Help

- Check existing [issues](https://github.com/yourusername/vils/issues)
- Search [discussions](https://github.com/yourusername/vils/discussions)
- Read the [documentation](docs/)
- Ask questions in discussions

### Reporting Bugs

When reporting bugs, include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, browser, versions)
- Screenshots or logs if applicable

Use the bug report template provided.

### Feature Requests

When requesting features:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if any)
- Acceptance criteria

Use the feature request template provided.

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Documentation acknowledgments

## Questions?

If you have questions about contributing, feel free to:
- Open a discussion on GitHub
- Ask in a pull request
- Contact the maintainers

Thank you for contributing to VILS! 🎯