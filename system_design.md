# Version Issue Locator System - Technical Design Document

## 1. Executive Summary

The Version Issue Locator System (VILS) is an enterprise-grade application designed to help development teams identify problematic code versions using an optimized binary search methodology. The system integrates with third-party build and testing services to systematically narrow down the exact commit or tag where issues were introduced, significantly reducing debugging time and improving code quality management.

## 2. System Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Vue.js 3 + TypeScript Frontend Application              │   │
│  │  - Dashboard & Task Management                           │   │
│  │  - Binary Search Visualization                           │   │
│  │  - Build Monitoring Interface                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Application Server                              │   │
│  │  - RESTful API Endpoints                                 │   │
│  │  - WebSocket for Real-time Updates                       │   │
│  │  - JWT Authentication                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Business Logic │  │   Integration   │  │  Background     │
│     Layer       │  │     Layer       │  │  Processing     │
│                 │  │                 │  │                 │
│ - Binary Search │  │ - Git APIs      │  │ - Celery Tasks  │
│ - Task Manager  │  │ - Build Service │  │ - Build Queue   │
│ - Session Mgmt  │  │ - Test Platform │  │ - Notifications │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │      Redis      │  │  Object Storage │
│    Database     │  │      Cache      │  │   (S3/MinIO)    │
│                 │  │                 │  │                 │
│ - Task History  │  │ - Session State │  │ - Build Logs    │
│ - User Data     │  │ - Build Status  │  │ - Test Results  │
│ - Tag Metadata  │  │ - Rate Limiting │  │ - Artifacts     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2.2 Component Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant TaskManager
    participant GitService
    participant BuildService
    participant Database

    User->>Frontend: Create Issue Locator Task
    Frontend->>API: POST /api/tasks/create
    API->>TaskManager: Initialize Task
    TaskManager->>GitService: Fetch Tag Range
    GitService-->>TaskManager: Return Tags
    TaskManager->>Database: Save Task & Tags
    TaskManager-->>API: Task Created
    API-->>Frontend: Task ID & Initial Tags
    
    loop Binary Search Iterations
        Frontend->>API: GET /api/tasks/{id}/candidates
        API->>TaskManager: Calculate 10 Candidates
        TaskManager-->>API: Candidate Tags
        API-->>Frontend: Display Candidates
        User->>Frontend: Select 3-5 Tags
        Frontend->>API: POST /api/builds/trigger
        API->>BuildService: Trigger Builds
        BuildService-->>API: Build IDs & Links
        API-->>Frontend: Build Status & Links
        User->>Frontend: Mark Build Results
        Frontend->>API: POST /api/tasks/{id}/feedback
        API->>TaskManager: Update Search Range
        TaskManager->>Database: Save Iteration
    end
    
    TaskManager-->>Frontend: Final Problematic Tag
```

## 3. Database Schema Design

### 3.1 Core Tables

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    repository_url TEXT NOT NULL,
    repository_type VARCHAR(50) NOT NULL, -- 'gerrit', 'repo', 'codehub'
    default_branch VARCHAR(100) DEFAULT 'main',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_url, name)
);

-- Branches table
CREATE TABLE branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    last_commit_hash VARCHAR(64),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, name)
);

-- Tags table
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    commit_hash VARCHAR(64) NOT NULL,
    tag_date TIMESTAMP WITH TIME ZONE,
    author_email VARCHAR(255),
    message TEXT,
    sequence_number INTEGER, -- For ordering tags
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, name),
    INDEX idx_tags_sequence (project_id, branch_id, sequence_number)
);

-- Issue localization tasks table
CREATE TABLE localization_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    branch_id UUID REFERENCES branches(id),
    task_name VARCHAR(255) NOT NULL,
    description TEXT,
    good_tag_id UUID REFERENCES tags(id),
    bad_tag_id UUID REFERENCES tags(id),
    status VARCHAR(50) NOT NULL, -- 'active', 'paused', 'completed', 'failed'
    total_tags_in_range INTEGER,
    current_iteration INTEGER DEFAULT 0,
    final_problematic_tag_id UUID REFERENCES tags(id),
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_tasks_user_status (user_id, status),
    INDEX idx_tasks_created (created_at DESC)
);

-- Task iterations table (tracks binary search progress)
CREATE TABLE task_iterations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES localization_tasks(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL,
    search_range_start INTEGER NOT NULL,
    search_range_end INTEGER NOT NULL,
    candidates_generated JSONB NOT NULL, -- Array of tag IDs
    selected_candidates JSONB, -- Array of selected tag IDs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(task_id, iteration_number),
    INDEX idx_iterations_task (task_id, iteration_number)
);

-- Build jobs table
CREATE TABLE build_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES localization_tasks(id) ON DELETE CASCADE,
    iteration_id UUID REFERENCES task_iterations(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id),
    external_build_id VARCHAR(255),
    build_service VARCHAR(100), -- 'jenkins', 'github_actions', 'gitlab_ci'
    build_url TEXT,
    status VARCHAR(50), -- 'pending', 'running', 'success', 'failed', 'cancelled'
    logs_url TEXT,
    artifacts_url TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_builds_task_iteration (task_id, iteration_id),
    INDEX idx_builds_status (status, created_at)
);

-- User feedback records table
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES localization_tasks(id) ON DELETE CASCADE,
    iteration_id UUID REFERENCES task_iterations(id) ON DELETE CASCADE,
    build_job_id UUID REFERENCES build_jobs(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id),
    feedback_type VARCHAR(50) NOT NULL, -- 'working', 'broken', 'inconclusive'
    notes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_feedback_task_iteration (task_id, iteration_id)
);

-- Task session state table (for resumption)
CREATE TABLE task_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES localization_tasks(id) ON DELETE CASCADE,
    session_data JSONB NOT NULL, -- Stores current search state
    current_range_start INTEGER,
    current_range_end INTEGER,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (task_id),
    INDEX idx_sessions_expires (expires_at)
);

-- External service configurations
CREATE TABLE service_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_type VARCHAR(100) NOT NULL, -- 'build_service', 'test_service'
    service_name VARCHAR(100) NOT NULL,
    base_url TEXT NOT NULL,
    api_key_encrypted TEXT,
    config_data JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(service_type, service_name)
);
```

### 3.2 Database Indexes and Constraints

```sql
-- Performance indexes
CREATE INDEX idx_tags_project_sequence ON tags(project_id, sequence_number);
CREATE INDEX idx_tasks_user_active ON localization_tasks(user_id, status) WHERE status = 'active';
CREATE INDEX idx_builds_pending ON build_jobs(status, created_at) WHERE status = 'pending';
CREATE INDEX idx_feedback_recent ON user_feedback(created_at DESC);

-- Full-text search indexes
CREATE INDEX idx_tasks_search ON localization_tasks USING gin(to_tsvector('english', task_name || ' ' || COALESCE(description, '')));
CREATE INDEX idx_tags_search ON tags USING gin(to_tsvector('english', name || ' ' || COALESCE(message, '')));

-- Constraints
ALTER TABLE task_iterations ADD CONSTRAINT check_range_valid 
    CHECK (search_range_end > search_range_start);
ALTER TABLE localization_tasks ADD CONSTRAINT check_tag_order 
    CHECK (bad_tag_id != good_tag_id);
```

## 4. API Specification

### 4.1 Authentication Endpoints

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
import uuid

app = FastAPI(title="Version Issue Locator API", version="1.0.0")

# Authentication Models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    created_at: datetime

# Authentication Endpoints
@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    """Register a new user account"""
    pass

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token"""
    pass

@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh expired access token"""
    pass

@app.post("/api/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Invalidate user session"""
    pass
```

### 4.2 Project and Branch Management

```python
# Project Models
class ProjectCreate(BaseModel):
    name: str
    repository_url: str
    repository_type: str  # 'gerrit', 'repo', 'codehub'
    default_branch: str = "main"

class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    repository_url: str
    repository_type: str
    default_branch: str
    created_by: uuid.UUID
    created_at: datetime
    branches_count: int

class BranchResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    last_commit_hash: Optional[str]
    last_sync_at: Optional[datetime]
    tags_count: int

# Project Endpoints
@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new project configuration"""
    pass

@app.get("/api/projects", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """List all projects accessible to user"""
    pass

@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Get project details"""
    pass

@app.get("/api/projects/{project_id}/branches", response_model=List[BranchResponse])
async def list_branches(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """List all branches for a project"""
    pass

@app.post("/api/projects/{project_id}/sync")
async def sync_project_data(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Synchronize project data from repository"""
    pass
```

### 4.3 Task Management Endpoints

```python
# Task Models
class TaskCreate(BaseModel):
    project_id: uuid.UUID
    branch_id: uuid.UUID
    task_name: str
    description: Optional[str]
    good_tag_name: str
    bad_tag_name: str

class TaskResponse(BaseModel):
    id: uuid.UUID
    task_name: str
    description: Optional[str]
    project_name: str
    branch_name: str
    good_tag: Dict[str, Any]
    bad_tag: Dict[str, Any]
    status: str
    total_tags_in_range: int
    current_iteration: int
    final_problematic_tag: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

class TaskIterationResponse(BaseModel):
    id: uuid.UUID
    iteration_number: int
    search_range_start: int
    search_range_end: int
    candidates_generated: List[Dict[str, Any]]
    selected_candidates: Optional[List[Dict[str, Any]]]
    created_at: datetime
    completed_at: Optional[datetime]

class BinarySearchCandidates(BaseModel):
    iteration_number: int
    current_range: Dict[str, int]
    candidates: List[Dict[str, Any]]  # Exactly 10 candidates
    
# Task Management Endpoints
@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new issue localization task"""
    pass

@app.get("/api/tasks", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = None,
    project_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """List user's tasks with optional filtering"""
    pass

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Get detailed task information"""
    pass

@app.get("/api/tasks/{task_id}/candidates", response_model=BinarySearchCandidates)
async def get_binary_search_candidates(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Generate exactly 10 candidate tags using binary search algorithm.
    Returns evenly distributed tags across the current search range.
    """
    pass

@app.post("/api/tasks/{task_id}/select-candidates")
async def select_candidates_for_testing(
    task_id: uuid.UUID,
    candidate_indices: List[int],  # 3-5 indices from the 10 candidates
    current_user: User = Depends(get_current_user)
):
    """Select 3-5 candidates from the 10 generated for testing"""
    pass

@app.get("/api/tasks/{task_id}/iterations", response_model=List[TaskIterationResponse])
async def get_task_iterations(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Get all iterations for a task"""
    pass

@app.put("/api/tasks/{task_id}/pause")
async def pause_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Pause an active task"""
    pass

@app.put("/api/tasks/{task_id}/resume")
async def resume_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Resume a paused task"""
    pass

@app.delete("/api/tasks/{task_id}")
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Delete a task and all associated data"""
    pass
```

### 4.4 Build Service Integration

```python
# Build Models
class BuildTriggerRequest(BaseModel):
    task_id: uuid.UUID
    iteration_id: uuid.UUID
    tag_ids: List[uuid.UUID]
    build_service: str  # 'jenkins', 'github_actions', 'gitlab_ci'
    build_parameters: Optional[Dict[str, Any]]

class BuildJobResponse(BaseModel):
    id: uuid.UUID
    external_build_id: str
    build_service: str
    build_url: str
    status: str
    tag_name: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class BuildFeedback(BaseModel):
    build_job_id: uuid.UUID
    feedback_type: str  # 'working', 'broken', 'inconclusive'
    notes: Optional[str]

# Build Service Endpoints
@app.post("/api/builds/trigger", response_model=List[BuildJobResponse])
async def trigger_builds(
    request: BuildTriggerRequest,
    current_user: User = Depends(get_current_user)
):
    """Trigger builds for selected tags via external service"""
    pass

@app.get("/api/builds/{build_id}", response_model=BuildJobResponse)
async def get_build_status(
    build_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Get current build status from external service"""
    pass

@app.post("/api/builds/{build_id}/feedback")
async def submit_build_feedback(
    build_id: uuid.UUID,
    feedback: BuildFeedback,
    current_user: User = Depends(get_current_user)
):
    """Submit user feedback for a build"""
    pass

@app.get("/api/builds/{build_id}/logs")
async def get_build_logs(
    build_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Retrieve build logs from external service"""
    pass

@app.get("/api/builds/{build_id}/artifacts")
async def get_build_artifacts(
    build_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Get links to build artifacts"""
    pass
```

### 4.5 WebSocket for Real-time Updates

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

    async def broadcast_task_update(self, task_id: str, update: dict, user_id: str):
        message = json.dumps({
            "type": "task_update",
            "task_id": task_id,
            "data": update
        })
        await self.send_personal_message(message, user_id)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
```

## 5. Frontend Architecture

### 5.1 Component Hierarchy

```typescript
// src/types/index.ts
export interface User {
  id: string;
  email: string;
  username: string;
  isActive: boolean;
}

export interface Project {
  id: string;
  name: string;
  repositoryUrl: string;
  repositoryType: 'gerrit' | 'repo' | 'codehub';
  defaultBranch: string;
  branchesCount: number;
}

export interface Task {
  id: string;
  taskName: string;
  description?: string;
  projectName: string;
  branchName: string;
  goodTag: Tag;
  badTag: Tag;
  status: 'active' | 'paused' | 'completed' | 'failed';
  totalTagsInRange: number;
  currentIteration: number;
  finalProblematicTag?: Tag;
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
}

export interface Tag {
  id: string;
  name: string;
  commitHash: string;
  tagDate: Date;
  message?: string;
}

export interface BinarySearchCandidate {
  tag: Tag;
  position: number;
  selected: boolean;
}
```

### 5.2 Vue.js Component Structure

```vue
<!-- src/App.vue -->
<template>
  <div id="app">
    <NavBar />
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <NotificationToast />
  </div>
</template>

<script setup lang="ts">
import NavBar from '@/components/layout/NavBar.vue'
import NotificationToast from '@/components/common/NotificationToast.vue'
</script>
```

```vue
<!-- src/views/Dashboard.vue -->
<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>Issue Locator Dashboard</h1>
      <button @click="createNewTask" class="btn-primary">
        <PlusIcon /> New Task
      </button>
    </div>
    
    <div class="dashboard-stats">
      <StatCard title="Active Tasks" :value="activeTasks" color="blue" />
      <StatCard title="Completed Today" :value="completedToday" color="green" />
      <StatCard title="Total Tasks" :value="totalTasks" color="gray" />
      <StatCard title="Success Rate" :value="successRate" suffix="%" color="purple" />
    </div>
    
    <div class="dashboard-content">
      <section class="active-tasks">
        <h2>Active Tasks</h2>
        <TaskList :tasks="activeTasksList" @task-click="navigateToTask" />
      </section>
      
      <section class="recent-activity">
        <h2>Recent Activity</h2>
        <ActivityFeed :activities="recentActivities" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '@/stores/task'
import StatCard from '@/components/dashboard/StatCard.vue'
import TaskList from '@/components/tasks/TaskList.vue'
import ActivityFeed from '@/components/dashboard/ActivityFeed.vue'
import { PlusIcon } from 'lucide-vue-next'

const router = useRouter()
const taskStore = useTaskStore()

const activeTasks = computed(() => taskStore.activeTasks.length)
const completedToday = computed(() => taskStore.getCompletedToday().length)
const totalTasks = computed(() => taskStore.allTasks.length)
const successRate = computed(() => taskStore.calculateSuccessRate())

const activeTasksList = computed(() => taskStore.activeTasks)
const recentActivities = computed(() => taskStore.recentActivities)

const createNewTask = () => {
  router.push('/tasks/new')
}

const navigateToTask = (taskId: string) => {
  router.push(`/tasks/${taskId}`)
}

onMounted(async () => {
  await taskStore.fetchDashboardData()
})
</script>
```

### 5.3 Pinia Store Implementation

```typescript
// src/stores/task.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Task, BinarySearchCandidate } from '@/types'
import { taskApi } from '@/api/tasks'

export const useTaskStore = defineStore('task', () => {
  // State
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const binaryCandidates = ref<BinarySearchCandidate[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // Getters
  const activeTasks = computed(() => 
    tasks.value.filter(t => t.status === 'active')
  )
  
  const completedTasks = computed(() => 
    tasks.value.filter(t => t.status === 'completed')
  )
  
  // Actions
  async function fetchTasks() {
    loading.value = true
    error.value = null
    try {
      const response = await taskApi.getTasks()
      tasks.value = response.data
    } catch (err) {
      error.value = 'Failed to fetch tasks'
      console.error(err)
    } finally {
      loading.value = false
    }
  }
  
  async function createTask(taskData: Partial<Task>) {
    loading.value = true
    error.value = null
    try {
      const response = await taskApi.createTask(taskData)
      tasks.value.push(response.data)
      currentTask.value = response.data
      return response.data
    } catch (err) {
      error.value = 'Failed to create task'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  async function fetchBinaryCandidates(taskId: string) {
    loading.value = true
    try {
      const response = await taskApi.getBinaryCandidates(taskId)
      binaryCandidates.value = response.data.candidates
      return response.data
    } catch (err) {
      error.value = 'Failed to fetch candidates'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  async function selectCandidates(taskId: string, indices: number[]) {
    if (indices.length < 3 || indices.length > 5) {
      throw new Error('Must select between 3 and 5 candidates')
    }
    
    loading.value = true
    try {
      const response = await taskApi.selectCandidates(taskId, indices)
      return response.data
    } catch (err) {
      error.value = 'Failed to select candidates'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  async function submitFeedback(buildId: string, feedback: string, notes?: string) {
    try {
      await taskApi.submitBuildFeedback(buildId, { 
        feedbackType: feedback, 
        notes 
      })
    } catch (err) {
      error.value = 'Failed to submit feedback'
      throw err
    }
  }
  
  return {
    // State
    tasks,
    currentTask,
    binaryCandidates,
    loading,
    error,
    // Getters
    activeTasks,
    completedTasks,
    // Actions
    fetchTasks,
    createTask,
    fetchBinaryCandidates,
    selectCandidates,
    submitFeedback
  }
})
```

### 5.4 Binary Search Visualization Component

```vue
<!-- src/components/BinarySearchVisualizer.vue -->
<template>
  <div class="binary-search-visualizer">
    <div class="search-header">
      <h3>Binary Search Progress</h3>
      <div class="iteration-info">
        <span>Iteration: {{ currentIteration }}</span>
        <span>Range: {{ rangeStart }} - {{ rangeEnd }}</span>
        <span>Remaining Tags: {{ rangeEnd - rangeStart + 1 }}</span>
      </div>
    </div>
    
    <div class="search-timeline">
      <div class="timeline-bar">
        <div 
          class="good-section" 
          :style="{ width: goodSectionWidth + '%' }"
        >
          <span class="label">Good</span>
        </div>
        <div 
          class="unknown-section" 
          :style="{ width: unknownSectionWidth + '%' }"
        >
          <span class="label">Unknown ({{ unknownCount }} tags)</span>
        </div>
        <div 
          class="bad-section" 
          :style="{ width: badSectionWidth + '%' }"
        >
          <span class="label">Bad</span>
        </div>
      </div>
      
      <div class="candidate-markers">
        <div 
          v-for="(candidate, index) in candidates" 
          :key="candidate.tag.id"
          class="candidate-marker"
          :class="{ 
            'selected': candidate.selected,
            'tested-good': candidate.result === 'working',
            'tested-bad': candidate.result === 'broken'
          }"
          :style="{ left: getMarkerPosition(candidate) + '%' }"
          @click="toggleCandidateSelection(index)"
        >
          <div class="marker-dot"></div>
          <div class="marker-label">{{ index + 1 }}</div>
          <div class="marker-tooltip">
            <strong>{{ candidate.tag.name }}</strong>
            <span>Position: {{ candidate.position }}</span>
            <span>{{ candidate.tag.commitHash.substring(0, 8) }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="candidates-grid">
      <h4>Select 3-5 Candidates for Testing</h4>
      <div class="candidates-list">
        <div 
          v-for="(candidate, index) in candidates" 
          :key="candidate.tag.id"
          class="candidate-card"
          :class="{ 'selected': candidate.selected }"
          @click="toggleCandidateSelection(index)"
        >
          <div class="candidate-number">{{ index + 1 }}</div>
          <div class="candidate-info">
            <strong>{{ candidate.tag.name }}</strong>
            <span class="commit-hash">{{ candidate.tag.commitHash.substring(0, 12) }}</span>
            <span class="position">Position: {{ candidate.position }}/{{ totalTags }}</span>
          </div>
          <div class="candidate-checkbox">
            <input 
              type="checkbox" 
              :checked="candidate.selected"
              @click.stop
              @change="toggleCandidateSelection(index)"
            />
          </div>
        </div>
      </div>
    </div>
    
    <div class="action-buttons">
      <button 
        class="btn-secondary" 
        @click="resetSelection"
      >
        Reset Selection
      </button>
      <button 
        class="btn-primary" 
        :disabled="!canProceed"
        @click="proceedWithTesting"
      >
        <PlayIcon /> Start Testing ({{ selectedCount }} selected)
      </button>
    </div>
    
    <div class="iteration-history" v-if="history.length > 0">
      <h4>Previous Iterations</h4>
      <div class="history-list">
        <div 
          v-for="iteration in history" 
          :key="iteration.id"
          class="history-item"
        >
          <span class="iteration-number">Iteration {{ iteration.number }}</span>
          <span class="iteration-range">Range: {{ iteration.rangeStart }} - {{ iteration.rangeEnd }}</span>
          <span class="iteration-result">
            Found {{ iteration.brokenCount }} broken, {{ iteration.workingCount }} working
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { PlayIcon } from 'lucide-vue-next'
import type { BinarySearchCandidate, IterationHistory } from '@/types'

const props = defineProps<{
  candidates: BinarySearchCandidate[]
  currentIteration: number
  rangeStart: number
  rangeEnd: number
  totalTags: number
  history: IterationHistory[]
}>()

const emit = defineEmits<{
  proceed: [indices: number[]]
}>()

const selectedIndices = ref<Set<number>>(new Set())

const selectedCount = computed(() => selectedIndices.value.size)
const canProceed = computed(() => selectedCount.value >= 3 && selectedCount.value <= 5)

const goodSectionWidth = computed(() => {
  return (props.rangeStart / props.totalTags) * 100
})

const unknownSectionWidth = computed(() => {
  return ((props.rangeEnd - props.rangeStart + 1) / props.totalTags) * 100
})

const badSectionWidth = computed(() => {
  return ((props.totalTags - props.rangeEnd) / props.totalTags) * 100
})

const unknownCount = computed(() => props.rangeEnd - props.rangeStart + 1)

function getMarkerPosition(candidate: BinarySearchCandidate): number {
  return (candidate.position / props.totalTags) * 100
}

function toggleCandidateSelection(index: number) {
  if (selectedIndices.value.has(index)) {
    selectedIndices.value.delete(index)
  } else if (selectedIndices.value.size < 5) {
    selectedIndices.value.add(index)
  }
}

function resetSelection() {
  selectedIndices.value.clear()
}

function proceedWithTesting() {
  emit('proceed', Array.from(selectedIndices.value))
}
</script>
```

## 6. Binary Search Algorithm Implementation

```python
# src/services/binary_search.py
from typing import List, Tuple, Optional
from dataclasses import dataclass
import math

@dataclass
class Tag:
    id: str
    name: str
    sequence_number: int
    commit_hash: str

@dataclass
class BinarySearchState:
    good_index: int
    bad_index: int
    current_iteration: int
    tested_tags: dict  # tag_id -> 'working' | 'broken'

class BinarySearchEngine:
    """
    Implements the binary search algorithm for issue localization.
    Generates exactly 10 evenly distributed candidates per iteration.
    """
    
    def __init__(self, tags: List[Tag]):
        self.tags = sorted(tags, key=lambda x: x.sequence_number)
        self.tag_map = {tag.id: tag for tag in self.tags}
        
    def generate_candidates(
        self, 
        good_index: int, 
        bad_index: int
    ) -> List[Tuple[int, Tag]]:
        """
        Generate exactly 10 candidate tags using binary division.
        Returns list of (index, tag) tuples.
        
        Example: With range [0, 1023], generates candidates at positions:
        64, 128, 192, 256, 320, 384, 512, 640, 768, 896
        """
        if bad_index <= good_index:
            raise ValueError("Bad index must be greater than good index")
            
        range_size = bad_index - good_index
        
        # If range is too small, return all available tags
        if range_size <= 10:
            candidates = []
            for i in range(good_index + 1, bad_index):
                candidates.append((i, self.tags[i]))
            return candidates
        
        # Calculate interval size for 10 evenly distributed points
        # Divide the range into 11 sections, pick the boundaries
        interval = range_size / 11.0
        
        candidates = []
        for i in range(1, 11):  # Generate exactly 10 points
            position = good_index + int(interval * i)
            # Ensure we don't exceed bounds
            if position < bad_index:
                candidates.append((position, self.tags[position]))
        
        return candidates
    
    def update_range(
        self,
        state: BinarySearchState,
        feedback: dict  # tag_id -> 'working' | 'broken'
    ) -> Tuple[int, int]:
        """
        Update search range based on user feedback.
        Returns new (good_index, bad_index) tuple.
        """
        state.tested_tags.update(feedback)
        
        # Find the rightmost working tag
        new_good = state.good_index
        for tag_id, result in feedback.items():
            if result == 'working':
                tag = self.tag_map[tag_id]
                tag_index = self.tags.index(tag)
                new_good = max(new_good, tag_index)
        
        # Find the leftmost broken tag
        new_bad = state.bad_index
        for tag_id, result in feedback.items():
            if result == 'broken':
                tag = self.tag_map[tag_id]
                tag_index = self.tags.index(tag)
                new_bad = min(new_bad, tag_index)
        
        return new_good, new_bad
    
    def is_complete(self, good_index: int, bad_index: int) -> bool:
        """Check if search is complete (adjacent tags)."""
        return bad_index - good_index == 1
    
    def get_problematic_tag(self, good_index: int, bad_index: int) -> Optional[Tag]:
        """Get the identified problematic tag."""
        if self.is_complete(good_index, bad_index):
            return self.tags[bad_index]
        return None

# Example usage in FastAPI endpoint
from fastapi import BackgroundTasks

@app.get("/api/tasks/{task_id}/candidates")
async def get_binary_search_candidates(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get tags in range
    tags = db.query(Tag).filter(
        Tag.project_id == task.project_id,
        Tag.sequence_number >= task.good_tag.sequence_number,
        Tag.sequence_number <= task.bad_tag.sequence_number
    ).order_by(Tag.sequence_number).all()
    
    engine = BinarySearchEngine(tags)
    
    # Get current search state
    session = db.query(TaskSession).filter(
        TaskSession.task_id == task_id
    ).first()
    
    if not session:
        # Initialize session
        session = TaskSession(
            task_id=task_id,
            current_range_start=0,
            current_range_end=len(tags) - 1,
            session_data={}
        )
        db.add(session)
        db.commit()
    
    # Generate candidates
    candidates = engine.generate_candidates(
        session.current_range_start,
        session.current_range_end
    )
    
    # Format response
    return {
        "iteration_number": task.current_iteration + 1,
        "current_range": {
            "start": session.current_range_start,
            "end": session.current_range_end
        },
        "candidates": [
            {
                "position": idx,
                "tag": {
                    "id": tag.id,
                    "name": tag.name,
                    "commit_hash": tag.commit_hash,
                    "sequence_number": tag.sequence_number
                }
            }
            for idx, tag in candidates
        ]
    }
```

## 7. Third-Party Integration Services

```python
# src/integrations/build_services.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import aiohttp
import json
from enum import Enum

class BuildStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BuildServiceInterface(ABC):
    """Abstract base class for build service integrations."""
    
    @abstractmethod
    async def trigger_build(
        self, 
        project: str, 
        branch: str, 
        tag: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger a build for a specific tag."""
        pass
    
    @abstractmethod
    async def get_build_status(self, build_id: str) -> BuildStatus:
        """Get the current status of a build."""
        pass
    
    @abstractmethod
    async def get_build_logs(self, build_id: str) -> str:
        """Retrieve build logs."""
        pass
    
    @abstractmethod
    async def cancel_build(self, build_id: str) -> bool:
        """Cancel a running build."""
        pass

class JenkinsIntegration(BuildServiceInterface):
    """Jenkins CI/CD integration."""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session:
            auth = aiohttp.BasicAuth('api', self.api_token)
            self.session = aiohttp.ClientSession(auth=auth)
        return self.session
    
    async def trigger_build(
        self, 
        project: str, 
        branch: str, 
        tag: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        session = await self._get_session()
        
        params = {
            'token': self.api_token,
            'BRANCH': branch,
            'TAG': tag,
            **parameters
        }
        
        url = f"{self.base_url}/job/{project}/buildWithParameters"
        
        async with session.post(url, params=params) as response:
            if response.status == 201:
                # Extract build queue URL from Location header
                location = response.headers.get('Location')
                queue_id = location.split('/')[-2] if location else None
                
                return {
                    'build_id': queue_id,
                    'status': 'pending',
                    'url': f"{self.base_url}/job/{project}/{queue_id}",
                    'service': 'jenkins'
                }
            else:
                raise Exception(f"Failed to trigger build: {response.status}")
    
    async def get_build_status(self, build_id: str) -> BuildStatus:
        session = await self._get_session()
        url = f"{self.base_url}/queue/item/{build_id}/api/json"
        
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                if data.get('cancelled'):
                    return BuildStatus.CANCELLED
                elif data.get('executable'):
                    # Build has started
                    build_url = data['executable']['url'] + 'api/json'
                    async with session.get(build_url) as build_response:
                        build_data = await build_response.json()
                        
                        if build_data['building']:
                            return BuildStatus.RUNNING
                        elif build_data['result'] == 'SUCCESS':
                            return BuildStatus.SUCCESS
                        elif build_data['result'] == 'FAILURE':
                            return BuildStatus.FAILED
                        elif build_data['result'] == 'ABORTED':
                            return BuildStatus.CANCELLED
                else:
                    return BuildStatus.PENDING
            else:
                raise Exception(f"Failed to get build status: {response.status}")
    
    async def get_build_logs(self, build_id: str) -> str:
        session = await self._get_session()
        url = f"{self.base_url}/job/{build_id}/lastBuild/consoleText"
        
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                return "Logs not available"
    
    async def cancel_build(self, build_id: str) -> bool:
        session = await self._get_session()
        url = f"{self.base_url}/queue/cancelItem"
        
        async with session.post(url, params={'id': build_id}) as response:
            return response.status == 200

class GitHubActionsIntegration(BuildServiceInterface):
    """GitHub Actions integration."""
    
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        
    async def trigger_build(
        self, 
        project: str, 
        branch: str, 
        tag: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Trigger workflow dispatch
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/workflows/{project}/dispatches"
        
        payload = {
            'ref': tag,
            'inputs': parameters
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 204:
                    # Get the run ID from recent runs
                    runs_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/runs"
                    
                    async with session.get(runs_url, headers=headers) as runs_response:
                        runs_data = await runs_response.json()
                        
                        if runs_data['workflow_runs']:
                            run = runs_data['workflow_runs'][0]
                            return {
                                'build_id': str(run['id']),
                                'status': 'pending',
                                'url': run['html_url'],
                                'service': 'github_actions'
                            }
                else:
                    raise Exception(f"Failed to trigger workflow: {response.status}")
    
    async def get_build_status(self, build_id: str) -> BuildStatus:
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/runs/{build_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    status_map = {
                        'queued': BuildStatus.PENDING,
                        'in_progress': BuildStatus.RUNNING,
                        'completed': BuildStatus.SUCCESS if data['conclusion'] == 'success' else BuildStatus.FAILED,
                        'cancelled': BuildStatus.CANCELLED
                    }
                    
                    return status_map.get(data['status'], BuildStatus.PENDING)
                else:
                    raise Exception(f"Failed to get run status: {response.status}")
    
    async def get_build_logs(self, build_id: str) -> str:
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/runs/{build_id}/logs"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return "Logs not available"
    
    async def cancel_build(self, build_id: str) -> bool:
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/runs/{build_id}/cancel"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                return response.status == 202

# Factory for creating build service instances
class BuildServiceFactory:
    @staticmethod
    def create_service(
        service_type: str, 
        config: Dict[str, Any]
    ) -> BuildServiceInterface:
        if service_type == 'jenkins':
            return JenkinsIntegration(
                base_url=config['base_url'],
                api_token=config['api_token']
            )
        elif service_type == 'github_actions':
            return GitHubActionsIntegration(
                token=config['token'],
                owner=config['owner'],
                repo=config['repo']
            )
        else:
            raise ValueError(f"Unsupported build service: {service_type}")
```

## 8. Deployment Architecture

### 8.1 Docker Configuration

```dockerfile
# backend.Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic.ini .
COPY .env.example .env

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"]

# frontend.Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build application
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 8.2 Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: vils_db
      POSTGRES_USER: vils_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U vils_user"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: backend.Dockerfile
    environment:
      DATABASE_URL: postgresql://vils_user:${DB_PASSWORD}@postgres:5432/vils_db
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
      CELERY_BROKER_URL: redis://redis:6379/0
    volumes:
      - ./backend/src:/app/src
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery:
    build:
      context: ./backend
      dockerfile: backend.Dockerfile
    command: celery -A src.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://vils_user:${DB_PASSWORD}@postgres:5432/vils_db
      REDIS_URL: redis://redis:6379
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: frontend.Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      VITE_API_URL: http://backend:8000

volumes:
  postgres_data:
  redis_data:
```

### 8.3 Kubernetes Deployment

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vils

---
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: vils
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: vils_db
        - name: POSTGRES_USER
          value: vils_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi

---
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: vils
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: vils/backend:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: backend-secret
              key: database-url
        - name: REDIS_URL
          value: redis://redis:6379
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: backend-secret
              key: jwt-secret
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: vils
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vils-ingress
  namespace: vils
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - vils.example.com
    secretName: vils-tls
  rules:
  - host: vils.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

## 9. Security Implementation

### 9.1 Authentication & Authorization

```python
# src/auth/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import secrets

# Configuration
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Rate-limited login endpoint"""
    pass
```

### 9.2 Data Encryption

```python
# src/auth/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

class EncryptionService:
    """Service for encrypting sensitive data like API keys"""
    
    def __init__(self, master_key: str = None):
        if master_key is None:
            master_key = os.environ.get('ENCRYPTION_MASTER_KEY')
        
        if not master_key:
            raise ValueError("Encryption master key not provided")
        
        # Derive encryption key from master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable_salt',  # In production, use random salt per item
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string value"""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a string value"""
        return self.cipher.decrypt(ciphertext.encode()).decode()

# API key validation
import hashlib
import hmac

def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash"""
    api_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key, api_key_hash

def validate_api_key(provided_key: str, stored_hash: str) -> bool:
    """Validate an API key against stored hash"""
    provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    return hmac.compare_digest(provided_hash, stored_hash)
```

## 10. Testing Strategy

### 10.1 Unit Tests

```python
# tests/test_binary_search.py
import pytest
from src.services.binary_search import BinarySearchEngine, Tag

class TestBinarySearchEngine:
    
    @pytest.fixture
    def sample_tags(self):
        """Create sample tags for testing"""
        return [
            Tag(id=f"tag_{i}", name=f"v{i}", sequence_number=i, commit_hash=f"hash_{i}")
            for i in range(1024)
        ]
    
    def test_generate_candidates_normal_range(self, sample_tags):
        """Test candidate generation with normal range"""
        engine = BinarySearchEngine(sample_tags)
        candidates = engine.generate_candidates(0, 1023)
        
        assert len(candidates) == 10
        
        # Check even distribution
        positions = [c[0] for c in candidates]
        expected_positions = [93, 186, 279, 372, 465, 558, 651, 744, 837, 930]
        
        for pos, expected in zip(positions, expected_positions):
            assert abs(pos - expected) <= 1  # Allow for rounding differences
    
    def test_generate_candidates_small_range(self, sample_tags):
        """Test candidate generation with small range"""
        engine = BinarySearchEngine(sample_tags[:10])
        candidates = engine.generate_candidates(0, 9)
        
        assert len(candidates) == 8  # All tags between good and bad
    
    def test_update_range(self, sample_tags):
        """Test range update based on feedback"""
        engine = BinarySearchEngine(sample_tags)
        
        state = BinarySearchState(
            good_index=0,
            bad_index=1023,
            current_iteration=1,
            tested_tags={}
        )
        
        feedback = {
            "tag_100": "working",
            "tag_500": "broken",
            "tag_300": "working"
        }
        
        new_good, new_bad = engine.update_range(state, feedback)
        
        assert new_good == 300  # Rightmost working tag
        assert new_bad == 500   # Leftmost broken tag
    
    def test_is_complete(self, sample_tags):
        """Test completion detection"""
        engine = BinarySearchEngine(sample_tags)
        
        assert engine.is_complete(5, 6) == True
        assert engine.is_complete(5, 7) == False
        assert engine.is_complete(5, 10) == False

# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import get_db

client = TestClient(app)

class TestTaskAPI:
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers for testing"""
        response = client.post("/api/auth/login", data={
            "username": "testuser",
            "password": "testpass"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_task(self, auth_headers, db_session):
        """Test task creation endpoint"""
        task_data = {
            "project_id": "test-project-id",
            "branch_id": "test-branch-id",
            "task_name": "Test Issue Locator",
            "description": "Finding test issue",
            "good_tag_name": "v1.0",
            "bad_tag_name": "v2.0"
        }
        
        response = client.post(
            "/api/tasks",
            json=task_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_name"] == task_data["task_name"]
        assert data["status"] == "active"
    
    def test_get_binary_candidates(self, auth_headers, existing_task):
        """Test binary candidate generation"""
        response = client.get(
            f"/api/tasks/{existing_task.id}/candidates",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["candidates"]) == 10
        assert "current_range" in data
        assert data["iteration_number"] == existing_task.current_iteration + 1
    
    def test_submit_feedback(self, auth_headers, existing_build):
        """Test feedback submission"""
        feedback_data = {
            "build_job_id": existing_build.id,
            "feedback_type": "working",
            "notes": "Build passed all tests"
        }
        
        response = client.post(
            f"/api/builds/{existing_build.id}/feedback",
            json=feedback_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
```

### 10.2 Integration Tests

```python
# tests/test_integration.py
import pytest
import asyncio
from src.integrations.build_services import JenkinsIntegration, BuildStatus

class TestJenkinsIntegration:
    
    @pytest.fixture
    async def jenkins_client(self):
        """Create Jenkins client for testing"""
        return JenkinsIntegration(
            base_url="http://jenkins.test",
            api_token="test-token"
        )
    
    @pytest.mark.asyncio
    async def test_trigger_build(self, jenkins_client, mock_jenkins_server):
        """Test triggering a Jenkins build"""
        result = await jenkins_client.trigger_build(
            project="test-project",
            branch="main",
            tag="v1.0",
            parameters={"ENV": "test"}
        )
        
        assert result["build_id"] is not None
        assert result["status"] == "pending"
        assert "jenkins" in result["service"]
    
    @pytest.mark.asyncio
    async def test_get_build_status(self, jenkins_client, mock_jenkins_server):
        """Test getting build status from Jenkins"""
        # Setup mock build
        build_id = "12345"
        mock_jenkins_server.set_build_status(build_id, "running")
        
        status = await jenkins_client.get_build_status(build_id)
        assert status == BuildStatus.RUNNING
        
        # Update mock status
        mock_jenkins_server.set_build_status(build_id, "success")
        
        status = await jenkins_client.get_build_status(build_id)
        assert status == BuildStatus.SUCCESS
```

### 10.3 End-to-End Tests

```typescript
// tests/e2e/task-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Task Workflow', () => {
  test('should complete full issue localization workflow', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    
    // Navigate to dashboard
    await expect(page).toHaveURL('/dashboard');
    
    // Create new task
    await page.click('button:has-text("New Task")');
    await page.fill('#task-name', 'E2E Test Issue');
    await page.selectOption('#project', 'test-project');
    await page.selectOption('#branch', 'main');
    await page.fill('#good-tag', 'v1.0');
    await page.fill('#bad-tag', 'v2.0');
    await page.click('button:has-text("Create Task")');
    
    // Wait for task creation
    await expect(page).toHaveURL(/\/tasks\/.+/);
    
    // Binary search interface should show
    await expect(page.locator('.binary-search-visualizer')).toBeVisible();
    await expect(page.locator('.candidate-card')).toHaveCount(10);
    
    // Select candidates
    await page.click('.candidate-card:nth-child(2)');
    await page.click('.candidate-card:nth-child(5)');
    await page.click('.candidate-card:nth-child(8)');
    
    // Start testing
    await page.click('button:has-text("Start Testing")');
    
    // Wait for builds to trigger
    await expect(page.locator('.build-status')).toBeVisible();
    
    // Submit feedback
    await page.click('button:has-text("Mark as Working")');
    await page.click('button:has-text("Mark as Broken")');
    await page.click('button:has-text("Mark as Working")');
    
    // Continue to next iteration
    await page.click('button:has-text("Next Iteration")');
    
    // Verify range narrowed
    const rangeText = await page.locator('.iteration-info').textContent();
    expect(rangeText).toContain('Range:');
  });
});
```

## 11. Performance Optimization

### 11.1 Database Optimization

```sql
-- Materialized view for task statistics
CREATE MATERIALIZED VIEW task_statistics AS
SELECT 
    user_id,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE status = 'active') as active_tasks,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))/3600) as avg_completion_hours,
    AVG(current_iteration) as avg_iterations_needed
FROM localization_tasks
GROUP BY user_id;

CREATE UNIQUE INDEX ON task_statistics(user_id);

-- Index for tag search performance
CREATE INDEX idx_tags_trgm ON tags USING gin(name gin_trgm_ops);

-- Partitioning for large task_iterations table
CREATE TABLE task_iterations_2024 PARTITION OF task_iterations
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
    
CREATE TABLE task_iterations_2025 PARTITION OF task_iterations
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### 11.2 Caching Strategy

```python
# src/cache/redis_cache.py
import redis
import json
from typing import Optional, Any
from datetime import timedelta

class RedisCache:
    """Redis caching implementation"""
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    
    def set(self, key: str, value: Any, expire: timedelta = None):
        """Set value in cache with optional expiration"""
        json_value = json.dumps(value)
        if expire:
            self.redis_client.setex(key, expire, json_value)
        else:
            self.redis_client.set(key, json_value)
    
    def delete(self, key: str):
        """Delete value from cache"""
        self.redis_client.delete(key)
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        for key in self.redis_client.scan_iter(match=pattern):
            self.redis_client.delete(key)

# Usage in API endpoints
from functools import wraps

def cache_result(expire_seconds: int = 300):
    """Decorator for caching endpoint results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, timedelta(seconds=expire_seconds))
            
            return result
        return wrapper
    return decorator

@app.get("/api/projects/{project_id}/tags")
@cache_result(expire_seconds=3600)
async def get_project_tags(project_id: str):
    """Cached endpoint for getting project tags"""
    pass
```

## 12. Monitoring and Observability

### 12.1 Logging Configuration

```python
# src/logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured logging"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # JSON formatter
    json_formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
        rename_fields={'asctime': 'timestamp'}
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    return logger

# Middleware for request logging
from fastapi import Request
import time
import uuid

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to logs
    with logger.contextvars.bind(request_id=request_id):
        logger.info("Request started", extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host
        })
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        logger.info("Request completed", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration
        })
        
        response.headers["X-Request-ID"] = request_id
        return response
```

### 12.2 Metrics Collection

```python
# src/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Define metrics
task_created_total = Counter('task_created_total', 'Total number of tasks created')
task_completed_total = Counter('task_completed_total', 'Total number of tasks completed')
build_triggered_total = Counter('build_triggered_total', 'Total number of builds triggered', ['service'])
binary_search_iterations = Histogram('binary_search_iterations', 'Number of iterations to find issue')
active_tasks_gauge = Gauge('active_tasks', 'Number of currently active tasks')

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    return Response(content=generate_latest(), media_type="text/plain")

# Update metrics in business logic
async def create_task_with_metrics(...):
    task = await create_task(...)
    task_created_total.inc()
    active_tasks_gauge.inc()
    return task
```

## 13. Configuration Management

### 13.1 Environment Configuration

```python
# src/config.py
from pydantic import BaseSettings, PostgresDsn, RedisDsn
from typing import Optional, Dict, Any

class Settings(BaseSettings):
    # Application
    app_name: str = "Version Issue Locator System"
    environment: str = "development"
    debug: bool = False
    
    # Database
    database_url: PostgresDsn
    db_pool_size: int = 20
    db_max_overflow: int = 40
    
    # Redis
    redis_url: RedisDsn
    redis_ttl: int = 3600
    
    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # External Services
    jenkins_url: Optional[str]
    jenkins_token: Optional[str]
    github_token: Optional[str]
    gitlab_token: Optional[str]
    
    # Celery
    celery_broker_url: str
    celery_result_backend: str
    
    # Monitoring
    sentry_dsn: Optional[str]
    log_level: str = "INFO"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Validate configuration on startup
@app.on_event("startup")
async def validate_configuration():
    """Validate critical configuration on startup"""
    if settings.environment == "production":
        assert settings.secret_key != "dev-secret-key", "Production must use secure secret key"
        assert settings.debug is False, "Debug must be disabled in production"
        assert settings.sentry_dsn is not None, "Sentry DSN required for production"
```

## 14. Documentation and API Examples

### 14.1 OpenAPI Documentation Enhancement

```python
# src/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Version Issue Locator API",
    description="""
    ## Overview
    
    The Version Issue Locator System (VILS) helps development teams identify problematic 
    code versions using binary search methodology. The system integrates with third-party 
    build and testing services.
    
    ## Features
    
    * **Binary Search Algorithm**: Efficiently narrow down problematic commits
    * **Third-party Integration**: Works with Jenkins, GitHub Actions, GitLab CI
    * **Task Management**: Track and manage issue localization sessions
    * **Real-time Updates**: WebSocket support for live build status
    
    ## Authentication
    
    This API uses JWT Bearer token authentication. Obtain a token via `/api/auth/login` 
    and include it in the Authorization header: `Bearer <token>`
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Version Issue Locator API",
        version="1.0.0",
        description="API for version issue localization system",
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add examples
    openapi_schema["paths"]["/api/tasks"]["post"]["requestBody"]["content"]["application/json"]["examples"] = {
        "simple": {
            "summary": "Simple task creation",
            "value": {
                "project_id": "proj-123",
                "branch_id": "branch-456",
                "task_name": "Find login bug",
                "good_tag_name": "v1.0.0",
                "bad_tag_name": "v1.2.0"
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

## 15. Disaster Recovery and Backup

### 15.1 Backup Strategy

```bash
#!/bin/bash
# scripts/backup.sh

# Database backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
DB_NAME="vils_db"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# Upload to S3
aws s3 cp "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz" "s3://vils-backups/postgres/$TIMESTAMP/"

# Cleanup old local backups (keep last 7 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Redis backup
redis-cli --rdb /backups/redis/dump_$TIMESTAMP.rdb
aws s3 cp "/backups/redis/dump_$TIMESTAMP.rdb" "s3://vils-backups/redis/$TIMESTAMP/"
```

### 15.2 Recovery Procedures

```python
# src/recovery/restore.py
import subprocess
import boto3
from datetime import datetime

class DisasterRecovery:
    """Disaster recovery procedures"""
    
    def __init__(self, s3_bucket: str, db_connection: str):
        self.s3_client = boto3.client('s3')
        self.s3_bucket = s3_bucket
        self.db_connection = db_connection
    
    def restore_database(self, backup_timestamp: str):
        """Restore PostgreSQL database from backup"""
        
        # Download backup from S3
        backup_file = f"backup_{backup_timestamp}.sql.gz"
        s3_key = f"postgres/{backup_timestamp}/{backup_file}"
        local_path = f"/tmp/{backup_file}"
        
        self.s3_client.download_file(
            self.s3_bucket,
            s3_key,
            local_path
        )
        
        # Restore database
        restore_command = f"gunzip -c {local_path} | psql {self.db_connection}"
        subprocess.run(restore_command, shell=True, check=True)
        
        print(f"Database restored from {backup_timestamp}")
    
    def verify_backup_integrity(self, backup_path: str) -> bool:
        """Verify backup file integrity"""
        # Implementation of backup verification
        pass
```

## 16. Conclusion

This comprehensive technical design document provides a complete blueprint for implementing the Version Issue Locator System. The system architecture is designed to be:

- **Scalable**: Microservices architecture with horizontal scaling capabilities
- **Reliable**: Comprehensive error handling and recovery mechanisms
- **Secure**: Multi-layer security with encryption and authentication
- **Maintainable**: Clear separation of concerns and extensive documentation
- **Performant**: Optimized database queries and caching strategies

The implementation follows industry best practices and provides a robust solution for identifying problematic code versions through an efficient binary search approach integrated with modern CI/CD pipelines.
