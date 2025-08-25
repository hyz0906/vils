"""Project management API endpoints."""

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, selectinload

from ..auth.dependencies import get_current_active_user
from ..database.connection import get_database
from ..models.project import Project, Branch, Tag
from ..models.user import User
from .schemas import (
    BranchResponse,
    PaginationParams,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TagResponse,
)

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Project:
    """Create a new project configuration.
    
    Args:
        project_data: Project creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created project
        
    Raises:
        HTTPException: If project already exists
    """
    # Check if project with same name and repository already exists for this user
    existing_project = db.query(Project).filter(
        and_(
            Project.name == project_data.name,
            Project.repository_url == project_data.repository_url,
            Project.created_by == current_user.id
        )
    ).first()
    
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name and repository URL already exists"
        )
    
    # Create new project
    project = Project(
        name=project_data.name,
        repository_url=project_data.repository_url,
        repository_type=project_data.repository_type,
        default_branch=project_data.default_branch,
        created_by=current_user.id
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Create default branch
    default_branch = Branch(
        project_id=project.id,
        name=project_data.default_branch
    )
    
    db.add(default_branch)
    db.commit()
    
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> List[Project]:
    """List all projects accessible to user.
    
    Args:
        pagination: Pagination parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of projects with counts
    """
    # Query projects with branch and tag counts
    query = db.query(
        Project,
        func.count(Branch.id.distinct()).label('branches_count'),
        func.count(Tag.id.distinct()).label('tags_count')
    ).outerjoin(Branch).outerjoin(Tag).filter(
        Project.created_by == current_user.id
    ).group_by(Project.id)
    
    # Apply pagination
    query = query.order_by(Project.created_at.desc())
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    results = query.all()
    
    # Convert to response format
    projects = []
    for project, branches_count, tags_count in results:
        project_dict = project.__dict__.copy()
        project_dict['branches_count'] = branches_count or 0
        project_dict['tags_count'] = tags_count or 0
        projects.append(project_dict)
    
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, Any]:
    """Get project details with counts.
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Project details with counts
        
    Raises:
        HTTPException: If project not found
    """
    # Query project with counts
    result = db.query(
        Project,
        func.count(Branch.id.distinct()).label('branches_count'),
        func.count(Tag.id.distinct()).label('tags_count')
    ).outerjoin(Branch).outerjoin(Tag).filter(
        and_(
            Project.id == project_id,
            Project.created_by == current_user.id
        )
    ).group_by(Project.id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project, branches_count, tags_count = result
    
    # Convert to response format
    project_dict = project.__dict__.copy()
    project_dict['branches_count'] = branches_count or 0
    project_dict['tags_count'] = tags_count or 0
    
    return project_dict


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Project:
    """Update project information.
    
    Args:
        project_id: Project ID
        project_update: Project update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated project
        
    Raises:
        HTTPException: If project not found
    """
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.created_by == current_user.id
        )
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update fields
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, str]:
    """Delete project and all associated data.
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If project not found
    """
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.created_by == current_user.id
        )
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Delete project (cascades to branches, tags, tasks, etc.)
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}


@router.get("/{project_id}/branches", response_model=List[BranchResponse])
async def list_branches(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> List[Dict[str, Any]]:
    """List all branches for a project.
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of branches with tag counts
        
    Raises:
        HTTPException: If project not found
    """
    # Verify project access
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.created_by == current_user.id
        )
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Query branches with tag counts
    results = db.query(
        Branch,
        func.count(Tag.id).label('tags_count')
    ).outerjoin(Tag).filter(
        Branch.project_id == project_id
    ).group_by(Branch.id).order_by(Branch.name).all()
    
    # Convert to response format
    branches = []
    for branch, tags_count in results:
        branch_dict = branch.__dict__.copy()
        branch_dict['tags_count'] = tags_count or 0
        branches.append(branch_dict)
    
    return branches


@router.get("/{project_id}/branches/{branch_id}/tags", response_model=List[TagResponse])
async def list_tags(
    project_id: uuid.UUID,
    branch_id: uuid.UUID,
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search in tag names"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> List[Tag]:
    """List tags for a branch.
    
    Args:
        project_id: Project ID
        branch_id: Branch ID
        pagination: Pagination parameters
        search: Optional search term
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of tags
        
    Raises:
        HTTPException: If project or branch not found
    """
    # Verify project access
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.created_by == current_user.id
        )
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify branch exists
    branch = db.query(Branch).filter(
        and_(
            Branch.id == branch_id,
            Branch.project_id == project_id
        )
    ).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found"
        )
    
    # Query tags
    query = db.query(Tag).filter(
        and_(
            Tag.project_id == project_id,
            Tag.branch_id == branch_id
        )
    )
    
    # Apply search filter
    if search:
        query = query.filter(
            Tag.name.ilike(f"%{search}%")
        )
    
    # Apply pagination and ordering
    query = query.order_by(Tag.sequence_number.desc().nulls_last(), Tag.created_at.desc())
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    return query.all()


@router.post("/{project_id}/sync")
async def sync_project_data(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, Any]:
    """Synchronize project data from repository.
    
    Note: This is a placeholder for repository synchronization logic.
    In a real implementation, this would connect to the actual repository
    (Gerrit, GitHub, GitLab, etc.) and fetch branches and tags.
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Sync status and statistics
        
    Raises:
        HTTPException: If project not found
    """
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.created_by == current_user.id
        )
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # TODO: Implement actual repository synchronization
    # This would involve:
    # 1. Connecting to the repository service (Gerrit, GitHub, etc.)
    # 2. Fetching branch information
    # 3. Fetching tag information with commit hashes
    # 4. Updating the database with new data
    # 5. Calculating sequence numbers for proper ordering
    
    # For now, return a placeholder response
    return {
        "message": "Sync initiated",
        "project_id": project_id,
        "status": "pending",
        "note": "Repository synchronization not yet implemented"
    }


@router.post("/{project_id}/branches/{branch_id}/tags/import")
async def import_tags(
    project_id: uuid.UUID,
    branch_id: uuid.UUID,
    tags_data: List[Dict[str, Any]],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, Any]:
    """Import tags for a branch (for demo/testing purposes).
    
    Args:
        project_id: Project ID
        branch_id: Branch ID
        tags_data: List of tag data dictionaries
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Import statistics
        
    Raises:
        HTTPException: If project or branch not found
    """
    # Verify project access
    project = db.query(Project).filter(
        and_(
            Project.id == project_id,
            Project.created_by == current_user.id
        )
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify branch exists
    branch = db.query(Branch).filter(
        and_(
            Branch.id == branch_id,
            Branch.project_id == project_id
        )
    ).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found"
        )
    
    # Import tags
    imported_count = 0
    skipped_count = 0
    
    for i, tag_data in enumerate(tags_data):
        # Check if tag already exists
        existing_tag = db.query(Tag).filter(
            and_(
                Tag.project_id == project_id,
                Tag.branch_id == branch_id,
                Tag.name == tag_data.get('name')
            )
        ).first()
        
        if existing_tag:
            skipped_count += 1
            continue
        
        # Create new tag
        tag = Tag(
            project_id=project_id,
            branch_id=branch_id,
            name=tag_data.get('name', f'tag-{i}'),
            commit_hash=tag_data.get('commit_hash', f'hash-{i}'),
            sequence_number=tag_data.get('sequence_number', i),
            author_email=tag_data.get('author_email'),
            message=tag_data.get('message'),
            tag_date=tag_data.get('tag_date')
        )
        
        db.add(tag)
        imported_count += 1
    
    db.commit()
    
    return {
        "message": "Tags imported successfully",
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "total_processed": len(tags_data)
    }