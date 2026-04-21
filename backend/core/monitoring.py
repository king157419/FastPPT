"""
Production-grade monitoring module for FastPPT backend.

Features:
- Performance monitoring (response time, throughput)
- Error tracking (exception counting, stack traces)
- Log aggregation (structured JSON logging)
- Health check endpoints
- Prometheus metrics export
"""

import time
import logging
import traceback
import psutil
import json
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
from collections import defaultdict
from threading import Lock

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


# ============================================
# Prometheus Metrics
# ============================================

# Request metrics
REQUEST_COUNT = Counter(
    'fastppt_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'fastppt_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# Error metrics
ERROR_COUNT = Counter(
    'fastppt_errors_total',
    'Total error count',
    ['endpoint', 'error_type']
)

# System metrics
MEMORY_USAGE = Gauge('fastppt_memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('fastppt_cpu_usage_percent', 'CPU usage percentage')

# Business metrics
PPT_GENERATION_COUNT = Counter('fastppt_ppt_generated_total', 'Total PPTs generated')
PPT_GENERATION_DURATION = Histogram('fastppt_ppt_generation_seconds', 'PPT generation duration')
RAG_QUERY_COUNT = Counter('fastppt_rag_queries_total', 'Total RAG queries')
RAG_QUERY_DURATION = Histogram('fastppt_rag_query_seconds', 'RAG query duration')


# ============================================
# Structured Logging
# ============================================

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id

        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Configure structured logging."""
    logger = logging.getLogger("fastppt")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger


# ============================================
# Error Tracking
# ============================================

class ErrorTracker:
    """Track and aggregate errors."""

    def __init__(self):
        self.errors: Dict[str, list] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.lock = Lock()

    def record_error(self, endpoint: str, error_type: str, error_message: str, stack_trace: Optional[str] = None):
        """Record an error occurrence."""
        with self.lock:
            error_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'endpoint': endpoint,
                'error_type': error_type,
                'message': error_message,
                'stack_trace': stack_trace
            }

            self.errors[endpoint].append(error_data)
            self.error_counts[f"{endpoint}:{error_type}"] += 1

            # Keep only last 100 errors per endpoint
            if len(self.errors[endpoint]) > 100:
                self.errors[endpoint] = self.errors[endpoint][-100:]

            # Update Prometheus counter
            ERROR_COUNT.labels(endpoint=endpoint, error_type=error_type).inc()

    def get_errors(self, endpoint: Optional[str] = None, limit: int = 50) -> list:
        """Get recent errors."""
        with self.lock:
            if endpoint:
                return self.errors.get(endpoint, [])[-limit:]
            else:
                all_errors = []
                for errors in self.errors.values():
                    all_errors.extend(errors)
                return sorted(all_errors, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics."""
        with self.lock:
            return {
                'total_errors': sum(self.error_counts.values()),
                'error_counts': dict(self.error_counts),
                'endpoints_with_errors': len(self.errors)
            }


# Global error tracker instance
error_tracker = ErrorTracker()


# ============================================
# Performance Monitoring
# ============================================

class PerformanceMonitor:
    """Monitor request performance."""

    def __init__(self):
        self.request_times: Dict[str, list] = defaultdict(list)
        self.lock = Lock()

    def record_request(self, endpoint: str, duration: float, status_code: int):
        """Record request performance."""
        with self.lock:
            self.request_times[endpoint].append({
                'timestamp': datetime.utcnow().isoformat(),
                'duration': duration,
                'status_code': status_code
            })

            # Keep only last 1000 requests per endpoint
            if len(self.request_times[endpoint]) > 1000:
                self.request_times[endpoint] = self.request_times[endpoint][-1000:]

    def get_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics."""
        with self.lock:
            if endpoint:
                times = [r['duration'] for r in self.request_times.get(endpoint, [])]
                if not times:
                    return {}

                return {
                    'endpoint': endpoint,
                    'count': len(times),
                    'avg_duration': sum(times) / len(times),
                    'min_duration': min(times),
                    'max_duration': max(times),
                    'p50': self._percentile(times, 50),
                    'p95': self._percentile(times, 95),
                    'p99': self._percentile(times, 99)
                }
            else:
                return {
                    ep: self.get_stats(ep)
                    for ep in self.request_times.keys()
                }

    @staticmethod
    def _percentile(data: list, percentile: int) -> float:
        """Calculate percentile."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# ============================================
# Middleware
# ============================================

async def monitoring_middleware(request: Request, call_next):
    """Middleware to monitor all requests."""
    start_time = time.time()
    endpoint = f"{request.method} {request.url.path}"

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        performance_monitor.record_request(endpoint, duration, response.status_code)

        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        return response

    except Exception as e:
        duration = time.time() - start_time

        # Record error
        error_tracker.record_error(
            endpoint=endpoint,
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=traceback.format_exc()
        )

        # Log error
        logger = logging.getLogger("fastppt")
        logger.error(f"Request failed: {endpoint}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(e),
                "endpoint": endpoint,
                "duration": duration
            }
        )


# ============================================
# Decorators
# ============================================

def monitor_performance(operation_name: str):
    """Decorator to monitor function performance."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Record to appropriate metric
                if 'ppt' in operation_name.lower():
                    PPT_GENERATION_DURATION.observe(duration)
                    PPT_GENERATION_COUNT.inc()
                elif 'rag' in operation_name.lower():
                    RAG_QUERY_DURATION.observe(duration)
                    RAG_QUERY_COUNT.inc()

                return result

            except Exception as e:
                error_tracker.record_error(
                    endpoint=operation_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    stack_trace=traceback.format_exc()
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if 'ppt' in operation_name.lower():
                    PPT_GENERATION_DURATION.observe(duration)
                    PPT_GENERATION_COUNT.inc()
                elif 'rag' in operation_name.lower():
                    RAG_QUERY_DURATION.observe(duration)
                    RAG_QUERY_COUNT.inc()

                return result

            except Exception as e:
                error_tracker.record_error(
                    endpoint=operation_name,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    stack_trace=traceback.format_exc()
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================
# Health Check
# ============================================

def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics."""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)

    # Update Prometheus gauges
    MEMORY_USAGE.set(memory.used)
    CPU_USAGE.set(cpu_percent)

    return {
        'memory': {
            'total_mb': memory.total / 1024 / 1024,
            'used_mb': memory.used / 1024 / 1024,
            'available_mb': memory.available / 1024 / 1024,
            'percent': memory.percent
        },
        'cpu': {
            'percent': cpu_percent,
            'count': psutil.cpu_count()
        },
        'disk': {
            'percent': psutil.disk_usage('/').percent
        }
    }


async def health_check() -> Dict[str, Any]:
    """Comprehensive health check."""
    try:
        system_metrics = get_system_metrics()
        error_summary = error_tracker.get_error_summary()

        # Determine health status
        status = "healthy"
        if system_metrics['memory']['percent'] > 90:
            status = "degraded"
        if system_metrics['cpu']['percent'] > 90:
            status = "degraded"
        if error_summary['total_errors'] > 100:
            status = "unhealthy"

        return {
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'system': system_metrics,
            'errors': error_summary,
            'uptime_seconds': time.time() - START_TIME
        }

    except Exception as e:
        return {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }


# ============================================
# Metrics Export
# ============================================

def export_prometheus_metrics() -> Response:
    """Export metrics in Prometheus format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ============================================
# Initialization
# ============================================

START_TIME = time.time()

# Setup default logger
logger = setup_logging()


# ============================================
# API Endpoints (to be registered in main.py)
# ============================================

"""
Example usage in main.py:

from fastapi import FastAPI
from core.monitoring import (
    monitoring_middleware,
    health_check,
    export_prometheus_metrics,
    error_tracker,
    performance_monitor
)

app = FastAPI()

# Add monitoring middleware
app.middleware("http")(monitoring_middleware)

# Health check endpoint
@app.get("/health")
async def health():
    return await health_check()

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return export_prometheus_metrics()

# Error logs endpoint
@app.get("/admin/errors")
async def get_errors(endpoint: str = None, limit: int = 50):
    return error_tracker.get_errors(endpoint, limit)

# Performance stats endpoint
@app.get("/admin/performance")
async def get_performance(endpoint: str = None):
    return performance_monitor.get_stats(endpoint)
"""

