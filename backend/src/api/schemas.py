"""Pydantic schemas for API requests and responses."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator


# Base schemas
class BaseResponse(BaseModel):
    """Base response model."""
    
    class Config:
        from_attributes = True


# User schemas
class UserBase(BaseModel):
    """Base user schema."""
    
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """User creation schema."""
    
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator("password")
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)


class UserResponse(UserBase, BaseResponse):
    """User response schema."""
    
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Authentication schemas
class TokenRequest(BaseModel):
    """Token request schema."""
    
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    
    refresh_token: str


# Project schemas
class ProjectBase(BaseModel):
    """Base project schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    repository_url: str
    repository_type: str = Field(..., regex="^(gerrit|repo|codehub|github|gitlab)$")
    default_branch: str = "main"


class ProjectCreate(ProjectBase):
    """Project creation schema."""
    
    pass


class ProjectUpdate(BaseModel):
    """Project update schema."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    repository_url: Optional[str] = None
    repository_type: Optional[str] = Field(None, regex="^(gerrit|repo|codehub|github|gitlab)$")
    default_branch: Optional[str] = None


class BranchResponse(BaseResponse):
    """Branch response schema."""
    
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    last_commit_hash: Optional[str]
    last_sync_at: Optional[datetime]
    tags_count: int = 0


class TagResponse(BaseResponse):
    """Tag response schema."""
    
    id: uuid.UUID
    project_id: uuid.UUID
    branch_id: uuid.UUID
    name: str
    commit_hash: str
    tag_date: Optional[datetime]
    author_email: Optional[str]
    message: Optional[str]
    sequence_number: Optional[int]


class ProjectResponse(ProjectBase, BaseResponse):
    """Project response schema."""
    
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    branches_count: int = 0
    tags_count: int = 0


# Task schemas
class TaskBase(BaseModel):
    """Base task schema."""
    
    task_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TaskCreate(TaskBase):
    """Task creation schema."""
    
    project_id: uuid.UUID
    branch_id: uuid.UUID
    good_tag_name: str
    bad_tag_name: str


class TaskUpdate(BaseModel):
    """Task update schema."""
    
    task_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    resolution_notes: Optional[str] = None


class TaskIterationResponse(BaseResponse):
    """Task iteration response schema."""
    
    id: uuid.UUID
    task_id: uuid.UUID
    iteration_number: int
    search_range_start: int
    search_range_end: int
    candidates_generated: Dict[str, Any]
    selected_candidates: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]


class TaskResponse(TaskBase, BaseResponse):
    """Task response schema."""
    
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    branch_id: uuid.UUID
    status: str
    total_tags_in_range: Optional[int]
    current_iteration: int
    final_problematic_tag_id: Optional[uuid.UUID]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    # Nested objects
    project_name: Optional[str] = None
    branch_name: Optional[str] = None
    good_tag: Optional[TagResponse] = None
    bad_tag: Optional[TagResponse] = None
    final_problematic_tag: Optional[TagResponse] = None


# Binary search schemas
class BinarySearchCandidate(BaseModel):
    """Binary search candidate schema."""
    
    position: int
    tag: TagResponse
    selected: bool = False


class BinarySearchCandidatesResponse(BaseModel):
    """Binary search candidates response."""
    
    iteration_number: int
    current_range: Dict[str, int]
    candidates: List[BinarySearchCandidate]
    total_tags: int


class CandidateSelection(BaseModel):
    """Candidate selection schema."""
    
    candidate_indices: List[int] = Field(..., min_items=3, max_items=5)


# Build schemas
class BuildJobBase(BaseModel):
    """Base build job schema."""
    
    build_service: str = Field(..., regex="^(jenkins|github_actions|gitlab_ci)$")


class BuildTriggerRequest(BaseModel):
    """Build trigger request schema."""
    
    task_id: uuid.UUID
    iteration_id: uuid.UUID
    tag_ids: List[uuid.UUID] = Field(..., min_items=1, max_items=10)
    build_service: str = Field(..., regex="^(jenkins|github_actions|gitlab_ci)$")
    build_parameters: Optional[Dict[str, Any]] = None


class BuildJobResponse(BuildJobBase, BaseResponse):
    """Build job response schema."""
    
    id: uuid.UUID
    task_id: uuid.UUID
    iteration_id: uuid.UUID
    tag_id: uuid.UUID
    external_build_id: Optional[str]
    build_url: Optional[str]
    status: str
    logs_url: Optional[str]
    artifacts_url: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    # Nested objects
    tag_name: Optional[str] = None


# Feedback schemas
class BuildFeedbackRequest(BaseModel):
    """Build feedback request schema."""
    
    feedback_type: str = Field(..., regex="^(working|broken|inconclusive)$")
    notes: Optional[str] = None


class UserFeedbackResponse(BaseResponse):
    """User feedback response schema."""
    
    id: uuid.UUID
    task_id: uuid.UUID
    iteration_id: uuid.UUID
    build_job_id: uuid.UUID
    tag_id: uuid.UUID
    feedback_type: str
    notes: Optional[str]
    created_by: uuid.UUID
    created_at: datetime


# Service configuration schemas
class ServiceConfigBase(BaseModel):
    """Base service config schema."""
    
    service_type: str
    service_name: str
    base_url: str
    is_active: bool = True


class ServiceConfigCreate(ServiceConfigBase):
    """Service config creation schema."""
    
    api_key: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None


class ServiceConfigUpdate(BaseModel):
    """Service config update schema."""
    
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ServiceConfigResponse(ServiceConfigBase, BaseResponse):
    """Service config response schema."""
    
    id: uuid.UUID
    config_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    # API key is never returned in responses for security


# Pagination schemas
class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_prev: bool