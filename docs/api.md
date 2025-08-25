# VILS API Documentation

This document provides comprehensive documentation for the VILS API endpoints.

## Base URL

```
http://localhost:8000/api  # Development
https://api.vils.example.com  # Production
```

## Authentication

VILS uses JWT (JSON Web Tokens) for authentication. Include the access token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

### Authentication Endpoints

#### POST /auth/login

Authenticate a user and return access and refresh tokens.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "created_at": "2023-01-01T00:00:00Z",
    "is_active": true
  }
}
```

#### POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "created_at": "2023-01-01T00:00:00Z",
    "is_active": true
  }
}
```

#### POST /auth/refresh

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "expires_in": 1800
}
```

#### POST /auth/logout

Logout and invalidate tokens.

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

## Projects

### GET /projects

List all projects accessible to the authenticated user.

**Query Parameters:**
- `limit`: Maximum number of results (default: 50)
- `offset`: Number of results to skip (default: 0)
- `search`: Filter by project name or description
- `is_active`: Filter by active status (true/false)

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "repository_url": "string",
      "build_command": "string",
      "test_command": "string",
      "is_active": true,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z",
      "owner": {
        "id": "uuid",
        "username": "string"
      },
      "tags": ["tag1", "tag2"]
    }
  ],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

### POST /projects

Create a new project.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "repository_url": "string",
  "build_command": "string",
  "test_command": "string",
  "tags": ["tag1", "tag2"]
}
```

### GET /projects/{project_id}

Get detailed information about a specific project.

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "repository_url": "string",
  "build_command": "string",
  "test_command": "string",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z",
  "owner": {
    "id": "uuid",
    "username": "string"
  },
  "tags": ["tag1", "tag2"],
  "statistics": {
    "total_tasks": 10,
    "completed_tasks": 8,
    "failed_tasks": 1,
    "active_tasks": 1
  }
}
```

### PUT /projects/{project_id}

Update an existing project.

**Request Body:** Same as POST /projects

### DELETE /projects/{project_id}

Delete a project and all associated tasks.

**Response:**
```json
{
  "message": "Project deleted successfully"
}
```

## Localization Tasks

### GET /tasks

List localization tasks.

**Query Parameters:**
- `limit`: Maximum number of results (default: 50)
- `offset`: Number of results to skip (default: 0)
- `project_id`: Filter by project ID
- `status`: Filter by status (active, completed, failed, cancelled)
- `user_id`: Filter by user ID (admin only)

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "project": {
        "id": "uuid",
        "name": "string"
      },
      "user": {
        "id": "uuid",
        "username": "string"
      },
      "description": "string",
      "status": "active",
      "good_commit": "string",
      "bad_commit": "string",
      "current_iteration": 3,
      "current_candidates": ["commit1", "commit2", "commit3"],
      "total_iterations": null,
      "problematic_commit": null,
      "error_message": null,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 5,
  "limit": 50,
  "offset": 0
}
```

### POST /tasks

Create a new localization task.

**Request Body:**
```json
{
  "project_id": "uuid",
  "description": "string",
  "good_commit": "string",
  "bad_commit": "string"
}
```

**Response:**
```json
{
  "id": "uuid",
  "project": {
    "id": "uuid",
    "name": "string"
  },
  "user": {
    "id": "uuid",
    "username": "string"
  },
  "description": "string",
  "status": "active",
  "good_commit": "string",
  "bad_commit": "string",
  "current_iteration": 1,
  "current_candidates": ["commit1", "commit2", "commit3", "commit4", "commit5"],
  "total_iterations": null,
  "problematic_commit": null,
  "error_message": null,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### GET /tasks/{task_id}

Get detailed information about a specific task, including iteration history.

**Response:**
```json
{
  "id": "uuid",
  "project": {
    "id": "uuid",
    "name": "string",
    "repository_url": "string",
    "build_command": "string",
    "test_command": "string"
  },
  "user": {
    "id": "uuid",
    "username": "string"
  },
  "description": "string",
  "status": "active",
  "good_commit": "string",
  "bad_commit": "string",
  "current_iteration": 3,
  "current_candidates": ["commit1", "commit2", "commit3"],
  "total_iterations": null,
  "problematic_commit": null,
  "error_message": null,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z",
  "iterations": [
    {
      "id": "uuid",
      "iteration_number": 1,
      "candidates": ["commit1", "commit2", "commit3", "commit4", "commit5"],
      "selected_candidate": "commit3",
      "test_result": "pass",
      "created_at": "2023-01-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "iteration_number": 2,
      "candidates": ["commit6", "commit7", "commit8"],
      "selected_candidate": "commit7",
      "test_result": "fail",
      "created_at": "2023-01-01T01:00:00Z"
    }
  ]
}
```

### POST /tasks/{task_id}/result

Submit test result for the current iteration.

**Request Body:**
```json
{
  "selected_candidate": "commit_hash",
  "test_result": "pass|fail"
}
```

**Response:**
```json
{
  "message": "Test result submitted successfully",
  "status": "active|completed",
  "next_candidates": ["commit1", "commit2", "commit3"],
  "problematic_commit": null
}
```

### DELETE /tasks/{task_id}

Cancel or delete a localization task.

**Response:**
```json
{
  "message": "Task cancelled successfully"
}
```

## Build Jobs

### GET /build-jobs

List build jobs.

**Query Parameters:**
- `task_id`: Filter by task ID
- `status`: Filter by status (pending, running, success, failed)
- `limit`: Maximum number of results (default: 50)
- `offset`: Number of results to skip (default: 0)

### POST /build-jobs

Trigger a new build job.

**Request Body:**
```json
{
  "task_id": "uuid",
  "commit_hash": "string",
  "build_config": {
    "build_command": "string",
    "test_command": "string",
    "timeout": 1800
  }
}
```

### GET /build-jobs/{job_id}

Get build job details and output.

**Response:**
```json
{
  "id": "uuid",
  "task_id": "uuid",
  "commit_hash": "string",
  "status": "success",
  "started_at": "2023-01-01T00:00:00Z",
  "completed_at": "2023-01-01T00:05:00Z",
  "build_output": {
    "stdout": "Build output...",
    "stderr": "Warning messages...",
    "returncode": 0
  },
  "test_output": {
    "stdout": "Test output...",
    "stderr": "",
    "returncode": 0
  }
}
```

## Tags

### GET /tags

List all available tags.

**Response:**
```json
[
  {
    "name": "frontend",
    "count": 5,
    "color": "#3B82F6"
  },
  {
    "name": "backend",
    "count": 3,
    "color": "#10B981"
  }
]
```

### POST /tags

Create a new tag.

**Request Body:**
```json
{
  "name": "string",
  "color": "#3B82F6"
}
```

## Monitoring

### GET /monitoring/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### GET /monitoring/metrics

Prometheus metrics endpoint (returns plain text format).

### GET /monitoring/stats

Application statistics.

**Response:**
```json
{
  "users": {
    "total": 100,
    "active_today": 15,
    "new_today": 2
  },
  "tasks": {
    "total": 500,
    "active": 10,
    "completed_today": 25,
    "failed_today": 2
  },
  "builds": {
    "total": 1500,
    "successful_today": 45,
    "failed_today": 3
  }
}
```

## WebSocket API

### Connection

Connect to WebSocket at `/ws` with authentication:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws', [], {
  headers: {
    'Authorization': 'Bearer ' + accessToken
  }
});
```

### Message Format

All WebSocket messages follow this format:

```json
{
  "type": "message_type",
  "data": {
    // Message-specific data
  }
}
```

### Message Types

#### task_update

Sent when a task status changes.

```json
{
  "type": "task_update",
  "data": {
    "task_id": "uuid",
    "status": "running",
    "current_iteration": 3,
    "current_candidates": ["commit1", "commit2", "commit3"],
    "problematic_commit": null
  }
}
```

#### build_status

Sent when a build job status changes.

```json
{
  "type": "build_status",
  "data": {
    "build_id": "uuid",
    "task_id": "uuid",
    "commit": "commit_hash",
    "status": "success",
    "output": {
      "stdout": "Build successful",
      "stderr": "",
      "returncode": 0
    }
  }
}
```

#### notification

Sent for user notifications.

```json
{
  "type": "notification",
  "data": {
    "title": "Task Completed",
    "message": "Your localization task has been completed successfully.",
    "type": "success",
    "task_id": "uuid"
  }
}
```

## Error Handling

### Error Response Format

All API errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      // Additional error details
    }
  }
}
```

### Common Error Codes

- `AUTHENTICATION_REQUIRED`: Missing or invalid authentication
- `PERMISSION_DENIED`: Insufficient permissions
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `VALIDATION_ERROR`: Invalid request data
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_SERVER_ERROR`: Server error

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `204 No Content`: Successful request with no response body
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Authentication endpoints**: 10 requests per minute per IP
- **General API endpoints**: 100 requests per minute per user
- **WebSocket connections**: 5 connections per user

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```