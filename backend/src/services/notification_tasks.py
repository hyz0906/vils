"""
Background tasks for notifications and cleanup
"""

from celery import current_app
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..core.database import get_db
from ..core.redis import redis_manager
from ..core.celery_app import celery_app
from ..models.user import User
from ..models.localization_task import LocalizationTask, TaskStatus
from ..services.websocket import websocket_manager


@celery_app.task
def send_notification_email(user_id: str, subject: str, message: str, html_message: str = None):
    """
    Send notification email to user
    """
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.email:
            return {"error": "User not found or no email address"}
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = "noreply@vils.example.com"
        msg['To'] = user.email
        
        # Add plain text part
        text_part = MIMEText(message, 'plain')
        msg.attach(text_part)
        
        # Add HTML part if provided
        if html_message:
            html_part = MIMEText(html_message, 'html')
            msg.attach(html_part)
        
        # Send email (placeholder - would need real SMTP configuration)
        # For now, just log the notification
        print(f"📧 Email notification to {user.email}: {subject}")
        
        return {
            "success": True,
            "user_email": user.email,
            "subject": subject
        }
        
    except Exception as e:
        return {"error": str(e)}


@celery_app.task
def send_task_completion_notification(task_id: str):
    """
    Send notification when a localization task is completed
    """
    try:
        db = next(get_db())
        task = db.query(LocalizationTask).filter(LocalizationTask.id == task_id).first()
        
        if not task:
            return {"error": "Task not found"}
        
        # Prepare notification message
        if task.status == TaskStatus.COMPLETED:
            if task.problematic_commit:
                subject = f"🎯 Task Completed: Issue located in commit {task.problematic_commit[:8]}"
                message = f"""
Your localization task "{task.description}" has been completed successfully!

Project: {task.project.name}
Problematic commit: {task.problematic_commit}
Total iterations: {task.current_iteration}

The binary search algorithm has successfully identified the commit that introduced the issue.
You can view the full details in the VILS dashboard.
                """
                html_message = f"""
<h2>🎯 Task Completed Successfully!</h2>
<p>Your localization task "<strong>{task.description}</strong>" has been completed!</p>

<h3>Results:</h3>
<ul>
    <li><strong>Project:</strong> {task.project.name}</li>
    <li><strong>Problematic commit:</strong> <code>{task.problematic_commit}</code></li>
    <li><strong>Total iterations:</strong> {task.current_iteration}</li>
</ul>

<p>The binary search algorithm has successfully identified the commit that introduced the issue.</p>
<p><a href="http://localhost:3000/tasks/{task.id}">View task details</a></p>
                """
            else:
                subject = f"✅ Task Completed: No issue found"
                message = f"""
Your localization task "{task.description}" has been completed.

Project: {task.project.name}
Status: No problematic commit found
Total iterations: {task.current_iteration}

The binary search did not identify a specific commit that introduced the issue.
This could mean the issue is not in the tested commit range.
                """
                html_message = f"""
<h2>✅ Task Completed</h2>
<p>Your localization task "<strong>{task.description}</strong>" has been completed.</p>

<h3>Results:</h3>
<ul>
    <li><strong>Project:</strong> {task.project.name}</li>
    <li><strong>Status:</strong> No problematic commit found</li>
    <li><strong>Total iterations:</strong> {task.current_iteration}</li>
</ul>

<p>The binary search did not identify a specific commit that introduced the issue.</p>
<p><a href="http://localhost:3000/tasks/{task.id}">View task details</a></p>
                """
        else:
            subject = f"❌ Task Failed: {task.description}"
            message = f"""
Your localization task "{task.description}" has failed.

Project: {task.project.name}
Error: {task.error_message or "Unknown error"}

Please check the task details and try again if needed.
            """
            html_message = f"""
<h2>❌ Task Failed</h2>
<p>Your localization task "<strong>{task.description}</strong>" has encountered an error.</p>

<h3>Details:</h3>
<ul>
    <li><strong>Project:</strong> {task.project.name}</li>
    <li><strong>Error:</strong> {task.error_message or "Unknown error"}</li>
</ul>

<p><a href="http://localhost:3000/tasks/{task.id}">View task details</a></p>
            """
        
        # Send email notification
        send_notification_email.delay(
            user_id=str(task.user_id),
            subject=subject,
            message=message,
            html_message=html_message
        )
        
        # Send WebSocket notification
        websocket_manager.send_to_user(str(task.user_id), {
            "type": "notification",
            "data": {
                "title": subject,
                "message": message[:200] + "..." if len(message) > 200 else message,
                "type": "success" if task.status == TaskStatus.COMPLETED else "error",
                "task_id": str(task.id)
            }
        })
        
        return {"success": True, "task_id": task_id}
        
    except Exception as e:
        return {"error": str(e)}


@celery_app.task
def cleanup_old_notifications():
    """
    Clean up old notifications and cache entries
    """
    try:
        # Clean up Redis cache entries older than 24 hours
        deleted_keys = 0
        
        # This is a placeholder - Redis doesn't have built-in TTL scanning
        # In practice, you'd use Redis key patterns and expiration
        
        # Clean up WebSocket connection tracking
        if redis_manager.redis:
            # Remove expired user sessions
            import asyncio
            asyncio.create_task(redis_manager.redis.eval("""
                local keys = redis.call('keys', 'user_session:*')
                local deleted = 0
                for i=1,#keys do
                    local ttl = redis.call('ttl', keys[i])
                    if ttl == -1 then  -- No expiration set
                        redis.call('expire', keys[i], 86400)  -- Set 24 hour expiration
                    elseif ttl == -2 then  -- Key doesn't exist
                        deleted = deleted + 1
                    end
                end
                return deleted
            """, 0))
        
        return {"deleted_cache_entries": deleted_keys}
        
    except Exception as e:
        return {"error": str(e)}


@celery_app.task
def send_daily_summary(user_id: str):
    """
    Send daily summary of user's tasks
    """
    try:
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {"error": "User not found"}
        
        # Get yesterday's date range
        yesterday = datetime.utcnow() - timedelta(days=1)
        start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get user's tasks from yesterday
        tasks = db.query(LocalizationTask).filter(
            LocalizationTask.user_id == user.id,
            LocalizationTask.created_at >= start_of_yesterday,
            LocalizationTask.created_at <= end_of_yesterday
        ).all()
        
        if not tasks:
            return {"message": "No tasks created yesterday"}
        
        # Prepare summary
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in tasks if t.status == TaskStatus.FAILED]
        active_tasks = [t for t in tasks if t.status == TaskStatus.ACTIVE]
        
        subject = f"📊 Daily Summary - {len(tasks)} tasks"
        
        message = f"""
Daily Task Summary for {yesterday.strftime('%Y-%m-%d')}

Total tasks: {len(tasks)}
✅ Completed: {len(completed_tasks)}
❌ Failed: {len(failed_tasks)}
🔄 Active: {len(active_tasks)}

Tasks created yesterday:
"""
        
        for task in tasks:
            status_icon = "✅" if task.status == TaskStatus.COMPLETED else "❌" if task.status == TaskStatus.FAILED else "🔄"
            message += f"  {status_icon} {task.description} ({task.project.name})\n"
        
        html_message = f"""
<h2>📊 Daily Task Summary</h2>
<p><strong>Date:</strong> {yesterday.strftime('%Y-%m-%d')}</p>

<div style="display: flex; gap: 20px; margin: 20px 0;">
    <div style="padding: 10px; background: #f0f9ff; border-radius: 8px;">
        <strong>Total Tasks</strong><br/>
        <span style="font-size: 24px;">{len(tasks)}</span>
    </div>
    <div style="padding: 10px; background: #f0fdf4; border-radius: 8px;">
        <strong>Completed</strong><br/>
        <span style="font-size: 24px; color: #16a34a;">{len(completed_tasks)}</span>
    </div>
    <div style="padding: 10px; background: #fef2f2; border-radius: 8px;">
        <strong>Failed</strong><br/>
        <span style="font-size: 24px; color: #dc2626;">{len(failed_tasks)}</span>
    </div>
    <div style="padding: 10px; background: #fffbeb; border-radius: 8px;">
        <strong>Active</strong><br/>
        <span style="font-size: 24px; color: #d97706;">{len(active_tasks)}</span>
    </div>
</div>

<h3>Tasks Created Yesterday:</h3>
<ul>
"""
        
        for task in tasks:
            status_color = "#16a34a" if task.status == TaskStatus.COMPLETED else "#dc2626" if task.status == TaskStatus.FAILED else "#d97706"
            html_message += f"""
    <li>
        <strong style="color: {status_color};">{task.description}</strong>
        <br/>Project: {task.project.name} | Status: {task.status.value}
        <br/><a href="http://localhost:3000/tasks/{task.id}">View details</a>
    </li>
"""
        
        html_message += """
</ul>
<p><a href="http://localhost:3000/tasks">View all tasks</a></p>
        """
        
        # Send email
        send_notification_email.delay(
            user_id=user_id,
            subject=subject,
            message=message,
            html_message=html_message
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "tasks_count": len(tasks)
        }
        
    except Exception as e:
        return {"error": str(e)}


@celery_app.task
def broadcast_system_notification(title: str, message: str, notification_type: str = "info"):
    """
    Broadcast system notification to all connected users
    """
    try:
        # Send WebSocket broadcast
        websocket_manager.broadcast({
            "type": "notification",
            "data": {
                "title": title,
                "message": message,
                "type": notification_type,
                "system": True
            }
        })
        
        return {
            "success": True,
            "title": title,
            "type": notification_type
        }
        
    except Exception as e:
        return {"error": str(e)}