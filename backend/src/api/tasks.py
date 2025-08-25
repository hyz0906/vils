"""Task management API endpoints."""

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, selectinload

from ..auth.dependencies import get_current_active_user
from ..database.connection import get_database
from ..models.build import BuildJob, UserFeedback
from ..models.project import Project, Branch, Tag
from ..models.task import LocalizationTask, TaskIteration, TaskSession
from ..models.user import User
from ..services.binary_search import BinarySearchEngine, BinarySearchState
from .schemas import (
    BinarySearchCandidatesResponse,
    CandidateSelection,
    PaginationParams,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    TaskIterationResponse,
    BinarySearchCandidate,
    TagResponse,
)

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> LocalizationTask:
    """Create a new issue localization task.
    
    Args:
        task_data: Task creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created task
        
    Raises:
        HTTPException: If validation fails
    """
    # Verify project exists and user has access
    project = db.query(Project).filter(
        and_(
            Project.id == task_data.project_id,
            Project.created_by == current_user.id
        )
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    # Verify branch exists
    branch = db.query(Branch).filter(
        and_(
            Branch.id == task_data.branch_id,
            Branch.project_id == task_data.project_id
        )
    ).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found"
        )
    
    # Find good and bad tags
    good_tag = db.query(Tag).filter(
        and_(
            Tag.name == task_data.good_tag_name,
            Tag.project_id == task_data.project_id,
            Tag.branch_id == task_data.branch_id
        )
    ).first()
    
    bad_tag = db.query(Tag).filter(
        and_(
            Tag.name == task_data.bad_tag_name,
            Tag.project_id == task_data.project_id,
            Tag.branch_id == task_data.branch_id
        )
    ).first()
    
    if not good_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Good tag '{task_data.good_tag_name}' not found"
        )
    
    if not bad_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bad tag '{task_data.bad_tag_name}' not found"
        )
    
    # Verify tag order (good should come before bad)
    if (good_tag.sequence_number or 0) >= (bad_tag.sequence_number or 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Good tag must have a lower sequence number than bad tag"
        )
    
    # Calculate total tags in range
    total_tags = db.query(func.count(Tag.id)).filter(
        and_(
            Tag.project_id == task_data.project_id,
            Tag.branch_id == task_data.branch_id,
            Tag.sequence_number >= good_tag.sequence_number,
            Tag.sequence_number <= bad_tag.sequence_number
        )
    ).scalar()
    
    # Create task
    task = LocalizationTask(
        user_id=current_user.id,
        project_id=task_data.project_id,
        branch_id=task_data.branch_id,
        task_name=task_data.task_name,
        description=task_data.description,
        good_tag_id=good_tag.id,
        bad_tag_id=bad_tag.id,
        total_tags_in_range=total_tags,
        status="active"
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Create initial task session
    session = TaskSession(
        task_id=task.id,
        session_data={
            "good_tag_sequence": good_tag.sequence_number,
            "bad_tag_sequence": bad_tag.sequence_number,
            "initialization_time": str(task.created_at)
        },
        current_range_start=0,  # Will be updated based on actual tag indices
        current_range_end=total_tags - 1
    )
    
    db.add(session)
    db.commit()
    
    return task


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    project_id: Optional[uuid.UUID] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> List[LocalizationTask]:
    """List user's tasks with optional filtering.
    
    Args:
        status_filter: Optional status filter
        project_id: Optional project ID filter
        pagination: Pagination parameters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of tasks
    """
    query = db.query(LocalizationTask).filter(
        LocalizationTask.user_id == current_user.id
    ).options(
        selectinload(LocalizationTask.project),
        selectinload(LocalizationTask.branch),
        selectinload(LocalizationTask.good_tag),
        selectinload(LocalizationTask.bad_tag),
        selectinload(LocalizationTask.final_problematic_tag)
    )
    
    # Apply filters
    if status_filter:
        query = query.filter(LocalizationTask.status == status_filter)
    
    if project_id:
        query = query.filter(LocalizationTask.project_id == project_id)
    
    # Apply pagination
    query = query.order_by(LocalizationTask.created_at.desc())
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    return query.all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> LocalizationTask:
    """Get detailed task information.
    
    Args:
        task_id: Task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Task details
        
    Raises:
        HTTPException: If task not found
    """
    task = db.query(LocalizationTask).filter(
        and_(
            LocalizationTask.id == task_id,
            LocalizationTask.user_id == current_user.id
        )
    ).options(
        selectinload(LocalizationTask.project),
        selectinload(LocalizationTask.branch),
        selectinload(LocalizationTask.good_tag),
        selectinload(LocalizationTask.bad_tag),
        selectinload(LocalizationTask.final_problematic_tag)
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.get("/{task_id}/candidates", response_model=BinarySearchCandidatesResponse)
async def get_binary_search_candidates(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, Any]:
    """Generate binary search candidates for task.
    
    Args:
        task_id: Task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Binary search candidates
        
    Raises:
        HTTPException: If task not found or already completed
    """
    # Get task
    task = db.query(LocalizationTask).filter(
        and_(
            LocalizationTask.id == task_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not active"
        )
    
    # Get tags in range
    tags = db.query(Tag).filter(
        and_(
            Tag.project_id == task.project_id,
            Tag.branch_id == task.branch_id,
            Tag.sequence_number >= task.good_tag.sequence_number,
            Tag.sequence_number <= task.bad_tag.sequence_number
        )
    ).order_by(Tag.sequence_number).all()
    
    if len(tags) < 3:  # Need at least good, bad, and one in between
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough tags in range for binary search"
        )
    
    # Initialize binary search engine
    engine = BinarySearchEngine(tags)
    
    # Get current search state
    session = db.query(TaskSession).filter(
        TaskSession.task_id == task_id
    ).first()
    
    if not session:
        # Initialize session
        good_index = 0  # Index of good tag in sorted list
        bad_index = len(tags) - 1  # Index of bad tag in sorted list
        
        session = TaskSession(
            task_id=task_id,
            current_range_start=good_index,
            current_range_end=bad_index,
            session_data={"initialized": True}
        )
        db.add(session)
        db.commit()
    else:
        good_index = session.current_range_start
        bad_index = session.current_range_end
    
    # Check if search is complete
    if engine.is_complete(good_index, bad_index):
        # Mark task as completed
        task.status = "completed"
        task.final_problematic_tag_id = tags[bad_index].id
        db.commit()
        
        # Return the final result
        return {
            "iteration_number": task.current_iteration,
            "current_range": {"start": good_index, "end": bad_index},
            "candidates": [],
            "total_tags": len(tags),
            "is_complete": True,
            "problematic_tag": TagResponse.from_orm(tags[bad_index])
        }
    
    # Generate candidates
    candidates = engine.generate_candidates(good_index, bad_index)
    
    # Convert to response format
    candidate_responses = []
    for candidate in candidates:
        tag = next(tag for tag in tags if str(tag.id) == candidate.tag.id)
        candidate_responses.append(
            BinarySearchCandidate(
                position=candidate.position,
                tag=TagResponse.from_orm(tag),
                selected=False
            )
        )
    
    return {
        "iteration_number": task.current_iteration + 1,
        "current_range": {"start": good_index, "end": bad_index},
        "candidates": candidate_responses,
        "total_tags": len(tags)
    }


@router.post("/{task_id}/select-candidates")
async def select_candidates_for_testing(
    task_id: uuid.UUID,
    selection: CandidateSelection,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, Any]:
    """Select candidates for build testing.
    
    Args:
        task_id: Task ID
        selection: Selected candidate indices
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Selection confirmation
        
    Raises:
        HTTPException: If task not found or invalid selection
    """
    # Get task
    task = db.query(LocalizationTask).filter(
        and_(
            LocalizationTask.id == task_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not active"
        )
    
    # Validate selection
    if len(selection.candidate_indices) < 3 or len(selection.candidate_indices) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must select between 3 and 5 candidates"
        )
    
    # Create new iteration
    iteration = TaskIteration(
        task_id=task_id,
        iteration_number=task.current_iteration + 1,
        search_range_start=0,  # Will be updated with actual values
        search_range_end=0,    # Will be updated with actual values
        candidates_generated={
            "candidate_count": 10,
            "selection_indices": selection.candidate_indices,
            "timestamp": str(task.updated_at)
        },
        selected_candidates={
            "indices": selection.candidate_indices,
            "count": len(selection.candidate_indices)
        }
    )
    
    db.add(iteration)
    
    # Update task iteration counter
    task.current_iteration += 1
    
    db.commit()
    db.refresh(iteration)
    
    return {
        "message": "Candidates selected successfully",
        "iteration_id": iteration.id,
        "selected_count": len(selection.candidate_indices),
        "next_step": "trigger_builds"
    }


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> LocalizationTask:
    """Update task information.
    
    Args:
        task_id: Task ID
        task_update: Task update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated task
        
    Raises:
        HTTPException: If task not found
    """
    task = db.query(LocalizationTask).filter(
        and_(
            LocalizationTask.id == task_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update fields
    if task_update.task_name is not None:
        task.task_name = task_update.task_name
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.resolution_notes is not None:
        task.resolution_notes = task_update.resolution_notes
    
    db.commit()
    db.refresh(task)
    
    return task


@router.put("/{task_id}/pause")
async def pause_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, str]:
    """Pause an active task.
    
    Args:
        task_id: Task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If task not found or not active
    """
    task = db.query(LocalizationTask).filter(
        and_(
            LocalizationTask.id == task_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not active"
        )
    
    task.status = "paused"
    db.commit()
    
    return {"message": "Task paused successfully"}


@router.put("/{task_id}/resume")
async def resume_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, str]:
    """Resume a paused task.
    
    Args:
        task_id: Task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If task not found or not paused
    """
    task = db.query(LocalizationTask).filter(
        and_(
            LocalizationTask.id == task_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not paused"
        )
    
    task.status = "active"
    db.commit()
    
    return {"message": "Task resumed successfully"}


@router.delete("/{task_id}")
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, str]:
    """Delete a task and all associated data.
    
    Args:
        task_id: Task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If task not found
    """
    task = db.query(LocalizationTask).filter(
        and_(
            LocalizationTask.id == task_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Delete task (cascades to related data)
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}


@router.get("/{task_id}/iterations", response_model=List[TaskIterationResponse])
async def get_task_iterations(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> List[TaskIteration]:
    """Get all iterations for a task.
    
    Args:
        task_id: Task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of task iterations
        
    Raises:
        HTTPException: If task not found
    """
    # Verify task access
    task = db.query(LocalizationTask).filter(
        and_(
            LocalizationTask.id == task_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Get iterations
    iterations = db.query(TaskIteration).filter(
        TaskIteration.task_id == task_id
    ).order_by(TaskIteration.iteration_number).all()
    
    return iterations