"""Build management API endpoints."""

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session, selectinload

from ..auth.dependencies import get_current_active_user
from ..database.connection import get_database
from ..integrations.build_services import BuildServiceFactory
from ..models.build import BuildJob, UserFeedback
from ..models.project import Tag
from ..models.service import ServiceConfig
from ..models.task import LocalizationTask, TaskIteration
from ..models.user import User
from .schemas import (
    BuildFeedbackRequest,
    BuildJobResponse,
    BuildTriggerRequest,
    UserFeedbackResponse,
)

router = APIRouter()


@router.post("/trigger", response_model=List[BuildJobResponse])
async def trigger_builds(
    request: BuildTriggerRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> List[BuildJob]:
    """Trigger builds for selected tags via external service.
    
    Args:
        request: Build trigger request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of created build jobs
        
    Raises:
        HTTPException: If validation fails or service unavailable
    """
    # Verify task access
    task = db.query(LocalizationTask).filter(
        and_(
            LocalizationTask.id == request.task_id,
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
    
    # Verify iteration exists
    iteration = db.query(TaskIteration).filter(
        and_(
            TaskIteration.id == request.iteration_id,
            TaskIteration.task_id == request.task_id
        )
    ).first()
    
    if not iteration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task iteration not found"
        )
    
    # Get service configuration
    service_config = db.query(ServiceConfig).filter(
        and_(
            ServiceConfig.service_type == "build_service",
            ServiceConfig.service_name == request.build_service,
            ServiceConfig.is_active == True
        )
    ).first()
    
    if not service_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Build service '{request.build_service}' not configured"
        )
    
    # Verify tags exist and belong to the project
    tags = db.query(Tag).filter(
        and_(
            Tag.id.in_(request.tag_ids),
            Tag.project_id == task.project_id,
            Tag.branch_id == task.branch_id
        )
    ).all()
    
    if len(tags) != len(request.tag_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some tags were not found or don't belong to the project"
        )
    
    # Create build service instance
    try:
        config_data = service_config.config_data or {}
        if service_config.api_key_encrypted:
            config_data['api_token'] = service_config.api_key_encrypted
        
        build_service = BuildServiceFactory.create_service(
            request.build_service,
            config_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize build service: {str(e)}"
        )
    
    # Trigger builds for each tag
    build_jobs = []
    build_parameters = request.build_parameters or {}
    
    for tag in tags:
        try:
            # Trigger build
            build_result = await build_service.trigger_build(
                project=task.project.name,
                branch=task.branch.name,
                tag=tag.name,
                parameters=build_parameters
            )
            
            # Create build job record
            build_job = BuildJob(
                task_id=request.task_id,
                iteration_id=request.iteration_id,
                tag_id=tag.id,
                external_build_id=build_result.get('build_id'),
                build_service=request.build_service,
                build_url=build_result.get('url'),
                status=build_result.get('status', 'pending')
            )
            
            db.add(build_job)
            build_jobs.append(build_job)
            
        except Exception as e:
            # Create a failed build job record
            build_job = BuildJob(
                task_id=request.task_id,
                iteration_id=request.iteration_id,
                tag_id=tag.id,
                build_service=request.build_service,
                status="failed"
            )
            
            db.add(build_job)
            build_jobs.append(build_job)
            
            # Log the error (in a real app, use proper logging)
            print(f"Failed to trigger build for tag {tag.name}: {str(e)}")
    
    db.commit()
    
    # Refresh all build jobs to get IDs
    for job in build_jobs:
        db.refresh(job)
    
    return build_jobs


@router.get("/{build_id}", response_model=BuildJobResponse)
async def get_build_status(
    build_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, Any]:
    """Get current build status from external service.
    
    Args:
        build_id: Build job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Build job with updated status
        
    Raises:
        HTTPException: If build not found
    """
    # Get build job with task verification
    build_job = db.query(BuildJob).join(
        LocalizationTask, BuildJob.task_id == LocalizationTask.id
    ).options(
        selectinload(BuildJob.tag)
    ).filter(
        and_(
            BuildJob.id == build_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not build_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Build job not found"
        )
    
    # Update status from external service if possible
    if build_job.external_build_id and build_job.status in ["pending", "running"]:
        try:
            # Get service configuration
            service_config = db.query(ServiceConfig).filter(
                and_(
                    ServiceConfig.service_type == "build_service",
                    ServiceConfig.service_name == build_job.build_service,
                    ServiceConfig.is_active == True
                )
            ).first()
            
            if service_config:
                config_data = service_config.config_data or {}
                if service_config.api_key_encrypted:
                    config_data['api_token'] = service_config.api_key_encrypted
                
                build_service = BuildServiceFactory.create_service(
                    build_job.build_service,
                    config_data
                )
                
                # Get updated status
                updated_status = await build_service.get_build_status(
                    build_job.external_build_id
                )
                
                # Update if status changed
                if updated_status != build_job.status:
                    build_job.status = updated_status
                    
                    # Set completion time if build finished
                    if updated_status in ["success", "failed", "cancelled"]:
                        from datetime import datetime
                        build_job.completed_at = datetime.utcnow()
                    
                    db.commit()
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to update build status: {str(e)}")
    
    # Prepare response
    response_data = {
        "id": build_job.id,
        "task_id": build_job.task_id,
        "iteration_id": build_job.iteration_id,
        "tag_id": build_job.tag_id,
        "external_build_id": build_job.external_build_id,
        "build_service": build_job.build_service,
        "build_url": build_job.build_url,
        "status": build_job.status,
        "logs_url": build_job.logs_url,
        "artifacts_url": build_job.artifacts_url,
        "started_at": build_job.started_at,
        "completed_at": build_job.completed_at,
        "created_at": build_job.created_at,
        "tag_name": build_job.tag.name if build_job.tag else None
    }
    
    return response_data


@router.post("/{build_id}/feedback", response_model=UserFeedbackResponse)
async def submit_build_feedback(
    build_id: uuid.UUID,
    feedback: BuildFeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> UserFeedback:
    """Submit user feedback for a build.
    
    Args:
        build_id: Build job ID
        feedback: User feedback data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created feedback record
        
    Raises:
        HTTPException: If build not found
    """
    # Get build job with task verification
    build_job = db.query(BuildJob).join(
        LocalizationTask, BuildJob.task_id == LocalizationTask.id
    ).filter(
        and_(
            BuildJob.id == build_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not build_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Build job not found"
        )
    
    # Check if feedback already exists for this build
    existing_feedback = db.query(UserFeedback).filter(
        UserFeedback.build_job_id == build_id
    ).first()
    
    if existing_feedback:
        # Update existing feedback
        existing_feedback.feedback_type = feedback.feedback_type
        existing_feedback.notes = feedback.notes
        db.commit()
        db.refresh(existing_feedback)
        return existing_feedback
    
    # Create new feedback record
    user_feedback = UserFeedback(
        task_id=build_job.task_id,
        iteration_id=build_job.iteration_id,
        build_job_id=build_job.id,
        tag_id=build_job.tag_id,
        feedback_type=feedback.feedback_type,
        notes=feedback.notes,
        created_by=current_user.id
    )
    
    db.add(user_feedback)
    db.commit()
    db.refresh(user_feedback)
    
    return user_feedback


@router.get("/{build_id}/logs")
async def get_build_logs(
    build_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, str]:
    """Retrieve build logs from external service.
    
    Args:
        build_id: Build job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Build logs
        
    Raises:
        HTTPException: If build not found
    """
    # Get build job with task verification
    build_job = db.query(BuildJob).join(
        LocalizationTask, BuildJob.task_id == LocalizationTask.id
    ).filter(
        and_(
            BuildJob.id == build_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not build_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Build job not found"
        )
    
    if not build_job.external_build_id:
        return {"logs": "No external build ID available"}
    
    try:
        # Get service configuration
        service_config = db.query(ServiceConfig).filter(
            and_(
                ServiceConfig.service_type == "build_service",
                ServiceConfig.service_name == build_job.build_service,
                ServiceConfig.is_active == True
            )
        ).first()
        
        if not service_config:
            return {"logs": "Build service configuration not found"}
        
        config_data = service_config.config_data or {}
        if service_config.api_key_encrypted:
            config_data['api_token'] = service_config.api_key_encrypted
        
        build_service = BuildServiceFactory.create_service(
            build_job.build_service,
            config_data
        )
        
        # Get logs from external service
        logs = await build_service.get_build_logs(build_job.external_build_id)
        
        return {"logs": logs}
        
    except Exception as e:
        return {"logs": f"Error retrieving logs: {str(e)}"}


@router.post("/{build_id}/cancel")
async def cancel_build(
    build_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, Any]:
    """Cancel a build job.
    
    Args:
        build_id: Build job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Cancellation result
        
    Raises:
        HTTPException: If build not found
    """
    # Get build job with task verification
    build_job = db.query(BuildJob).join(
        LocalizationTask, BuildJob.task_id == LocalizationTask.id
    ).filter(
        and_(
            BuildJob.id == build_id,
            LocalizationTask.user_id == current_user.id
        )
    ).first()
    
    if not build_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Build job not found"
        )
    
    if build_job.status in ["success", "failed", "cancelled"]:
        return {
            "message": "Build is already completed",
            "status": build_job.status
        }
    
    success = False
    
    if build_job.external_build_id:
        try:
            # Get service configuration
            service_config = db.query(ServiceConfig).filter(
                and_(
                    ServiceConfig.service_type == "build_service",
                    ServiceConfig.service_name == build_job.build_service,
                    ServiceConfig.is_active == True
                )
            ).first()
            
            if service_config:
                config_data = service_config.config_data or {}
                if service_config.api_key_encrypted:
                    config_data['api_token'] = service_config.api_key_encrypted
                
                build_service = BuildServiceFactory.create_service(
                    build_job.build_service,
                    config_data
                )
                
                # Cancel build in external service
                success = await build_service.cancel_build(build_job.external_build_id)
        except Exception as e:
            print(f"Failed to cancel build externally: {str(e)}")
    
    # Update local status regardless of external cancellation result
    build_job.status = "cancelled"
    if not build_job.completed_at:
        from datetime import datetime
        build_job.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Build cancelled" if success else "Build marked as cancelled locally",
        "external_cancellation": success,
        "status": build_job.status
    }


@router.get("/task/{task_id}", response_model=List[BuildJobResponse])
async def get_task_builds(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> List[Dict[str, Any]]:
    """Get all build jobs for a task.
    
    Args:
        task_id: Task ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of build jobs for the task
        
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
    
    # Get build jobs with tag information
    build_jobs = db.query(BuildJob).options(
        selectinload(BuildJob.tag)
    ).filter(
        BuildJob.task_id == task_id
    ).order_by(BuildJob.created_at.desc()).all()
    
    # Convert to response format
    results = []
    for job in build_jobs:
        results.append({
            "id": job.id,
            "task_id": job.task_id,
            "iteration_id": job.iteration_id,
            "tag_id": job.tag_id,
            "external_build_id": job.external_build_id,
            "build_service": job.build_service,
            "build_url": job.build_url,
            "status": job.status,
            "logs_url": job.logs_url,
            "artifacts_url": job.artifacts_url,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "created_at": job.created_at,
            "tag_name": job.tag.name if job.tag else None
        })
    
    return results