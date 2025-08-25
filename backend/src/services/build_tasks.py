"""
Background tasks for build operations
"""

from celery import current_app
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import asyncio
import subprocess
import json
import os
import tempfile
import shutil

from ..core.database import get_db
from ..models.build_job import BuildJob, BuildStatus
from ..models.localization_task import LocalizationTask, TaskStatus
from ..services.websocket import websocket_manager
from ..services.build_service import BuildService
from ..core.celery_app import celery_app


@celery_app.task(bind=True, retry_kwargs={'max_retries': 3})
def run_build(self, build_job_id: str, commit_hash: str, build_config: Dict[str, Any]):
    """
    Execute a build job for a specific commit
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get build job
        build_job = db.query(BuildJob).filter(BuildJob.id == build_job_id).first()
        if not build_job:
            raise ValueError(f"Build job {build_job_id} not found")
            
        # Update build job status
        build_job.status = BuildStatus.RUNNING
        build_job.started_at = db.bind.execute("SELECT NOW()").scalar()
        db.commit()
        
        # Notify WebSocket clients
        asyncio.create_task(websocket_manager.broadcast({
            "type": "build_status",
            "data": {
                "build_id": build_job_id,
                "status": "running",
                "commit": commit_hash
            }
        }))
        
        # Create temporary directory for build
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = os.path.join(temp_dir, "repo")
            
            # Clone repository
            clone_result = subprocess.run([
                "git", "clone", build_config["repository_url"], repo_dir
            ], capture_output=True, text=True, timeout=300)
            
            if clone_result.returncode != 0:
                raise Exception(f"Failed to clone repository: {clone_result.stderr}")
                
            # Checkout specific commit
            checkout_result = subprocess.run([
                "git", "checkout", commit_hash
            ], cwd=repo_dir, capture_output=True, text=True, timeout=60)
            
            if checkout_result.returncode != 0:
                raise Exception(f"Failed to checkout commit {commit_hash}: {checkout_result.stderr}")
            
            # Run build command
            build_command = build_config.get("build_command", "make build")
            build_result = subprocess.run(
                build_command.split(),
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )
            
            # Capture build output
            build_output = {
                "stdout": build_result.stdout,
                "stderr": build_result.stderr,
                "returncode": build_result.returncode
            }
            
            # Run test command if provided
            test_output = None
            if build_config.get("test_command"):
                test_result = subprocess.run(
                    build_config["test_command"].split(),
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=1800
                )
                
                test_output = {
                    "stdout": test_result.stdout,
                    "stderr": test_result.stderr,
                    "returncode": test_result.returncode
                }
            
            # Determine if build was successful
            success = build_result.returncode == 0
            if test_output:
                success = success and test_output["returncode"] == 0
                
            # Update build job with results
            build_job.status = BuildStatus.SUCCESS if success else BuildStatus.FAILED
            build_job.completed_at = db.bind.execute("SELECT NOW()").scalar()
            build_job.build_output = build_output
            build_job.test_output = test_output
            build_job.artifacts_path = None  # Could store artifacts here
            
            db.commit()
            
            # Notify WebSocket clients
            asyncio.create_task(websocket_manager.broadcast({
                "type": "build_status",
                "data": {
                    "build_id": build_job_id,
                    "status": "success" if success else "failed",
                    "commit": commit_hash,
                    "output": build_output
                }
            }))
            
            return {
                "build_job_id": build_job_id,
                "commit": commit_hash,
                "success": success,
                "output": build_output,
                "test_output": test_output
            }
            
    except Exception as e:
        # Handle build failure
        db = next(get_db())
        build_job = db.query(BuildJob).filter(BuildJob.id == build_job_id).first()
        if build_job:
            build_job.status = BuildStatus.FAILED
            build_job.completed_at = db.bind.execute("SELECT NOW()").scalar()
            build_job.build_output = {"error": str(e)}
            db.commit()
        
        # Notify WebSocket clients
        asyncio.create_task(websocket_manager.broadcast({
            "type": "build_status", 
            "data": {
                "build_id": build_job_id,
                "status": "failed",
                "commit": commit_hash,
                "error": str(e)
            }
        }))
        
        # Retry if not max retries reached
        if self.request.retries < self.retry_kwargs['max_retries']:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
            
        raise


@celery_app.task
def process_localization_iteration(task_id: str, selected_commit: str, test_result: str):
    """
    Process a binary search iteration result
    """
    try:
        db = next(get_db())
        
        # Get localization task
        task = db.query(LocalizationTask).filter(LocalizationTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        # Update task with iteration result
        from ..services.binary_search import BinarySearchService
        search_service = BinarySearchService(db)
        
        # Process the iteration
        result = search_service.process_iteration_result(
            task_id=task_id,
            selected_commit=selected_commit,
            test_result=test_result
        )
        
        # Notify WebSocket clients
        asyncio.create_task(websocket_manager.broadcast({
            "type": "task_update",
            "data": {
                "task_id": task_id,
                "status": result["status"],
                "current_iteration": result.get("current_iteration"),
                "current_candidates": result.get("current_candidates"),
                "problematic_commit": result.get("problematic_commit")
            }
        }))
        
        return result
        
    except Exception as e:
        # Mark task as failed
        db = next(get_db())
        task = db.query(LocalizationTask).filter(LocalizationTask.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
            
        # Notify WebSocket clients
        asyncio.create_task(websocket_manager.broadcast({
            "type": "task_update",
            "data": {
                "task_id": task_id,
                "status": "failed",
                "error_message": str(e)
            }
        }))
        
        raise


@celery_app.task
def health_check():
    """
    Health check task for monitoring
    """
    try:
        # Check database connection
        db = next(get_db())
        db.execute("SELECT 1")
        
        # Check Redis connection
        from ..core.redis import redis_manager
        if redis_manager.redis:
            asyncio.create_task(redis_manager.redis.ping())
            
        return {"status": "healthy", "timestamp": db.bind.execute("SELECT NOW()").scalar()}
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@celery_app.task
def cleanup_old_builds(days_old: int = 30):
    """
    Clean up old build jobs and artifacts
    """
    try:
        db = next(get_db())
        
        # Delete old build jobs
        cutoff_date = db.bind.execute(f"SELECT NOW() - INTERVAL '{days_old} days'").scalar()
        
        old_builds = db.query(BuildJob).filter(
            BuildJob.created_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for build in old_builds:
            # Clean up artifacts if they exist
            if build.artifacts_path and os.path.exists(build.artifacts_path):
                shutil.rmtree(build.artifacts_path, ignore_errors=True)
                
            db.delete(build)
            deleted_count += 1
            
        db.commit()
        
        return {"deleted_builds": deleted_count}
        
    except Exception as e:
        return {"error": str(e)}