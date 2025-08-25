"""
Prometheus metrics collection
"""

import time
from typing import Dict, Any, Optional
from functools import wraps
from collections import defaultdict, Counter

from prometheus_client import (
    Counter as PrometheusCounter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST
)

from .config import settings


# Application info
app_info = Info('vils_app_info', 'Application information')
app_info.info({
    'version': '1.0.0',
    'environment': settings.environment
})

# HTTP metrics
http_requests_total = PrometheusCounter(
    'vils_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'vils_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Database metrics
db_connections_active = Gauge(
    'vils_db_connections_active',
    'Active database connections'
)

db_query_duration_seconds = Histogram(
    'vils_db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
)

db_queries_total = PrometheusCounter(
    'vils_db_queries_total',
    'Total database queries',
    ['query_type', 'status']
)

# Task metrics
tasks_created_total = PrometheusCounter(
    'vils_tasks_created_total',
    'Total tasks created',
    ['task_type']
)

tasks_completed_total = PrometheusCounter(
    'vils_tasks_completed_total',
    'Total tasks completed',
    ['task_type', 'status']
)

tasks_active = Gauge(
    'vils_tasks_active',
    'Currently active tasks',
    ['task_type']
)

task_duration_seconds = Histogram(
    'vils_task_duration_seconds',
    'Task execution duration in seconds',
    ['task_type'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600, 7200]
)

# Build metrics
builds_total = PrometheusCounter(
    'vils_builds_total',
    'Total builds executed',
    ['project', 'status']
)

build_duration_seconds = Histogram(
    'vils_build_duration_seconds',
    'Build execution duration in seconds',
    ['project'],
    buckets=[10, 30, 60, 120, 300, 600, 1200, 1800, 3600]
)

# Binary search metrics
binary_search_iterations = Histogram(
    'vils_binary_search_iterations',
    'Number of iterations in binary search',
    ['project'],
    buckets=[1, 2, 3, 5, 7, 10, 15, 20, 30, 50]
)

commits_tested_total = PrometheusCounter(
    'vils_commits_tested_total',
    'Total commits tested',
    ['project', 'result']
)

# WebSocket metrics
websocket_connections_active = Gauge(
    'vils_websocket_connections_active',
    'Active WebSocket connections'
)

websocket_messages_sent_total = PrometheusCounter(
    'vils_websocket_messages_sent_total',
    'Total WebSocket messages sent',
    ['message_type']
)

# Cache metrics
cache_operations_total = PrometheusCounter(
    'vils_cache_operations_total',
    'Total cache operations',
    ['operation', 'result']
)

cache_hit_ratio = Gauge(
    'vils_cache_hit_ratio',
    'Cache hit ratio'
)

# Authentication metrics
auth_attempts_total = PrometheusCounter(
    'vils_auth_attempts_total',
    'Total authentication attempts',
    ['method', 'status']
)

active_users = Gauge(
    'vils_active_users',
    'Currently active users'
)

# Background job metrics
celery_tasks_total = PrometheusCounter(
    'vils_celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_task_duration_seconds = Histogram(
    'vils_celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600, 7200]
)

# System metrics
memory_usage_bytes = Gauge(
    'vils_memory_usage_bytes',
    'Memory usage in bytes'
)

cpu_usage_percent = Gauge(
    'vils_cpu_usage_percent',
    'CPU usage percentage'
)


class MetricsCollector:
    """Metrics collection utility"""
    
    def __init__(self):
        self.request_stats = defaultdict(list)
        self.cache_stats = {'hits': 0, 'misses': 0}
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_db_query(self, query_type: str, duration: float, status: str = 'success'):
        """Record database query metrics"""
        db_queries_total.labels(
            query_type=query_type,
            status=status
        ).inc()
        
        db_query_duration_seconds.labels(
            query_type=query_type
        ).observe(duration)
    
    def record_task_created(self, task_type: str):
        """Record task creation"""
        tasks_created_total.labels(task_type=task_type).inc()
        tasks_active.labels(task_type=task_type).inc()
    
    def record_task_completed(self, task_type: str, status: str, duration: float):
        """Record task completion"""
        tasks_completed_total.labels(
            task_type=task_type,
            status=status
        ).inc()
        
        tasks_active.labels(task_type=task_type).dec()
        
        task_duration_seconds.labels(
            task_type=task_type
        ).observe(duration)
    
    def record_build(self, project: str, status: str, duration: float):
        """Record build execution"""
        builds_total.labels(
            project=project,
            status=status
        ).inc()
        
        build_duration_seconds.labels(project=project).observe(duration)
    
    def record_binary_search_completion(self, project: str, iterations: int):
        """Record binary search completion"""
        binary_search_iterations.labels(project=project).observe(iterations)
    
    def record_commit_test(self, project: str, result: str):
        """Record commit test result"""
        commits_tested_total.labels(
            project=project,
            result=result
        ).inc()
    
    def record_websocket_connection(self, connected: bool):
        """Record WebSocket connection change"""
        if connected:
            websocket_connections_active.inc()
        else:
            websocket_connections_active.dec()
    
    def record_websocket_message(self, message_type: str):
        """Record WebSocket message sent"""
        websocket_messages_sent_total.labels(message_type=message_type).inc()
    
    def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation"""
        result = 'hit' if hit else 'miss'
        cache_operations_total.labels(
            operation=operation,
            result=result
        ).inc()
        
        # Update hit ratio
        if hit:
            self.cache_stats['hits'] += 1
        else:
            self.cache_stats['misses'] += 1
        
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        if total > 0:
            hit_ratio = self.cache_stats['hits'] / total
            cache_hit_ratio.set(hit_ratio)
    
    def record_auth_attempt(self, method: str, status: str):
        """Record authentication attempt"""
        auth_attempts_total.labels(
            method=method,
            status=status
        ).inc()
    
    def update_active_users(self, count: int):
        """Update active users count"""
        active_users.set(count)
    
    def record_celery_task(self, task_name: str, status: str, duration: Optional[float] = None):
        """Record Celery task execution"""
        celery_tasks_total.labels(
            task_name=task_name,
            status=status
        ).inc()
        
        if duration is not None:
            celery_task_duration_seconds.labels(task_name=task_name).observe(duration)
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        import psutil
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage_bytes.set(memory.used)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_usage_percent.set(cpu_percent)
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest()


# Global metrics collector
metrics = MetricsCollector()


def track_time(metric_name: str, labels: Dict[str, str] = None):
    """Decorator to track execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                if metric_name == 'http_request':
                    endpoint = labels.get('endpoint', 'unknown')
                    method = labels.get('method', 'unknown')
                    status_code = getattr(result, 'status_code', 200)
                    metrics.record_http_request(method, endpoint, status_code, duration)
                elif metric_name == 'db_query':
                    query_type = labels.get('query_type', 'unknown')
                    metrics.record_db_query(query_type, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                if metric_name == 'http_request':
                    endpoint = labels.get('endpoint', 'unknown')
                    method = labels.get('method', 'unknown')
                    metrics.record_http_request(method, endpoint, 500, duration)
                elif metric_name == 'db_query':
                    query_type = labels.get('query_type', 'unknown')
                    metrics.record_db_query(query_type, duration, 'error')
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if metric_name == 'db_query':
                    query_type = labels.get('query_type', 'unknown')
                    metrics.record_db_query(query_type, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                if metric_name == 'db_query':
                    query_type = labels.get('query_type', 'unknown')
                    metrics.record_db_query(query_type, duration, 'error')
                
                raise
        
        if func.__code__.co_flags & 0x80:  # Check if function is async
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator