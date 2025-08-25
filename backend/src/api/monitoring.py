"""
Monitoring and health check endpoints
"""

import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.metrics import metrics, CONTENT_TYPE_LATEST
from ..core.logging import get_logger
from ..core.redis import redis_manager
from ..models.user import User
from ..models.localization_task import LocalizationTask
from ..models.build_job import BuildJob

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
logger = get_logger(__name__)


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Basic health check endpoint
    """
    try:
        # Check database
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "unhealthy"
        
    try:
        # Check Redis
        if redis_manager.redis:
            await redis_manager.redis.ping()
            redis_status = "healthy"
        else:
            redis_status = "not_connected"
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        redis_status = "unhealthy"
    
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy"
    
    health_data = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "redis": redis_status
        }
    }
    
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail=health_data)
    
    return health_data


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with metrics
    """
    try:
        start_time = datetime.utcnow()
        
        # Database health
        db_start = datetime.utcnow()
        try:
            # Test query
            db.execute("SELECT COUNT(*) FROM users")
            db_duration = (datetime.utcnow() - db_start).total_seconds()
            db_status = {
                "status": "healthy",
                "response_time": db_duration
            }
        except Exception as e:
            db_status = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Redis health
        redis_start = datetime.utcnow()
        try:
            if redis_manager.redis:
                await redis_manager.redis.ping()
                redis_duration = (datetime.utcnow() - redis_start).total_seconds()
                redis_status = {
                    "status": "healthy",
                    "response_time": redis_duration
                }
            else:
                redis_status = {
                    "status": "not_connected"
                }
        except Exception as e:
            redis_status = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # System resources
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_status = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "used": disk.used,
                "percent": (disk.used / disk.total) * 100
            }
        }
        
        # Application metrics
        try:
            total_users = db.query(User).count()
            active_tasks = db.query(LocalizationTask).filter(
                LocalizationTask.status.in_(['active', 'running'])
            ).count()
            total_tasks = db.query(LocalizationTask).count()
            running_builds = db.query(BuildJob).filter(
                BuildJob.status == 'running'
            ).count()
            
            app_metrics = {
                "total_users": total_users,
                "active_tasks": active_tasks,
                "total_tasks": total_tasks,
                "running_builds": running_builds
            }
        except Exception as e:
            app_metrics = {"error": str(e)}
        
        total_duration = (datetime.utcnow() - start_time).total_seconds()
        
        overall_status = (
            "healthy" 
            if db_status["status"] == "healthy" and redis_status["status"] == "healthy"
            else "unhealthy"
        )
        
        health_data = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time": total_duration,
            "services": {
                "database": db_status,
                "redis": redis_status
            },
            "system": system_status,
            "application": app_metrics
        }
        
        if overall_status == "unhealthy":
            raise HTTPException(status_code=503, detail=health_data)
        
        return health_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint
    """
    try:
        # Update system metrics
        metrics.update_system_metrics()
        
        # Get metrics in Prometheus format
        metrics_data = metrics.get_metrics()
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
        
    except Exception as e:
        logger.error("Failed to generate metrics", error=str(e))
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/stats")
async def get_application_stats(db: Session = Depends(get_db)):
    """
    Application statistics endpoint
    """
    try:
        # Date ranges
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        
        # User statistics
        total_users = db.query(User).count()
        active_users_today = db.query(User).filter(
            User.last_login >= today
        ).count()
        new_users_today = db.query(User).filter(
            User.created_at >= today
        ).count()
        
        # Task statistics
        total_tasks = db.query(LocalizationTask).count()
        active_tasks = db.query(LocalizationTask).filter(
            LocalizationTask.status.in_(['active', 'running'])
        ).count()
        completed_tasks_today = db.query(LocalizationTask).filter(
            LocalizationTask.status == 'completed',
            LocalizationTask.updated_at >= today
        ).count()
        failed_tasks_today = db.query(LocalizationTask).filter(
            LocalizationTask.status == 'failed',
            LocalizationTask.updated_at >= today
        ).count()
        
        # Weekly trends
        tasks_this_week = db.query(LocalizationTask).filter(
            LocalizationTask.created_at >= last_week
        ).count()
        tasks_last_week = db.query(LocalizationTask).filter(
            LocalizationTask.created_at >= last_week - timedelta(days=7),
            LocalizationTask.created_at < last_week
        ).count()
        
        # Build statistics
        total_builds = db.query(BuildJob).count()
        successful_builds_today = db.query(BuildJob).filter(
            BuildJob.status == 'success',
            BuildJob.completed_at >= today
        ).count()
        failed_builds_today = db.query(BuildJob).filter(
            BuildJob.status == 'failed',
            BuildJob.completed_at >= today
        ).count()
        
        # System statistics
        memory = psutil.virtual_memory()
        
        stats = {
            "timestamp": now.isoformat(),
            "users": {
                "total": total_users,
                "active_today": active_users_today,
                "new_today": new_users_today
            },
            "tasks": {
                "total": total_tasks,
                "active": active_tasks,
                "completed_today": completed_tasks_today,
                "failed_today": failed_tasks_today,
                "this_week": tasks_this_week,
                "last_week": tasks_last_week,
                "weekly_change": tasks_this_week - tasks_last_week
            },
            "builds": {
                "total": total_builds,
                "successful_today": successful_builds_today,
                "failed_today": failed_builds_today
            },
            "system": {
                "memory_usage_percent": memory.percent,
                "cpu_usage_percent": psutil.cpu_percent(interval=1),
                "uptime_seconds": psutil.boot_time()
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error("Failed to generate application stats", error=str(e))
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/logs")
async def get_recent_logs(
    level: str = "INFO",
    lines: int = 100,
    service: str = None
):
    """
    Get recent application logs
    """
    try:
        import os
        from pathlib import Path
        
        log_dir = Path("logs")
        log_file = log_dir / "app.log"
        
        if not log_file.exists():
            return {"logs": [], "message": "Log file not found"}
        
        # Read last N lines from log file
        logs = []
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            for line in recent_lines:
                try:
                    import json
                    log_entry = json.loads(line.strip())
                    
                    # Filter by level
                    if level and log_entry.get('level', '').upper() != level.upper():
                        continue
                    
                    # Filter by service
                    if service and log_entry.get('service') != service:
                        continue
                    
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    # Handle non-JSON log lines
                    logs.append({"message": line.strip(), "level": "UNKNOWN"})
        
        return {
            "logs": logs,
            "total_lines": len(logs),
            "filter": {
                "level": level,
                "lines": lines,
                "service": service
            }
        }
        
    except Exception as e:
        logger.error("Failed to retrieve logs", error=str(e))
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/performance")
async def get_performance_metrics(db: Session = Depends(get_db)):
    """
    Performance metrics endpoint
    """
    try:
        # Database performance
        db_start = datetime.utcnow()
        db.execute("SELECT 1")
        db_latency = (datetime.utcnow() - db_start).total_seconds()
        
        # Redis performance
        redis_latency = None
        if redis_manager.redis:
            redis_start = datetime.utcnow()
            await redis_manager.redis.ping()
            redis_latency = (datetime.utcnow() - redis_start).total_seconds()
        
        # Memory usage
        import gc
        gc.collect()
        
        performance = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "latency_seconds": db_latency,
                "status": "healthy" if db_latency < 0.1 else "slow"
            },
            "redis": {
                "latency_seconds": redis_latency,
                "status": "healthy" if redis_latency and redis_latency < 0.01 else "slow"
            } if redis_latency else {"status": "not_available"},
            "memory": {
                "usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "available_mb": psutil.virtual_memory().available / 1024 / 1024
            }
        }
        
        return performance
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(status_code=500, detail={"error": str(e)})