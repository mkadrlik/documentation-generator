"""Prometheus metrics for Documentation Generator"""

import time
from typing import Optional
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MetricsCollector:
    """Prometheus metrics collector for Documentation Generator"""
    
    def __init__(self, config=None):
        self.config = config
        self.metrics_enabled = config and config.prometheus_enabled
        
        if not self.metrics_enabled:
            return
            
        # Document generation metrics
        self.documents_generated_total = Counter(
            'documents_generated_total',
            'Total number of documents generated',
            ['doc_type', 'ai_provider', 'model', 'status']
        )
        
        self.document_generation_duration = Histogram(
            'document_generation_duration_seconds',
            'Time spent generating documents',
            ['doc_type', 'ai_provider', 'model'],
            buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0]
        )
        
        self.ai_tokens_used = Histogram(
            'ai_tokens_used_total',
            'Number of AI tokens used for generation',
            ['ai_provider', 'model'],
            buckets=[100, 500, 1000, 2000, 4000, 8000, 16000]
        )
        
        self.ai_requests_total = Counter(
            'ai_requests_total',
            'Total number of AI API requests',
            ['ai_provider', 'model', 'status']
        )
        
        # System metrics
        self.active_generations = Gauge(
            'active_document_generations',
            'Number of documents currently being generated'
        )
        
        self.template_types_available = Gauge(
            'template_types_available',
            'Number of available document template types'
        )
        
        # Application info
        self.app_info = Info(
            'documentation_generator_info',
            'Information about the Documentation Generator'
        )
        
        # Set application info
        self.app_info.info({
            'version': '1.0.0',
            'component': 'documentation-generator',
            'default_ai_provider': config.default_ai_provider if config else 'unknown',
            'default_model': config.default_model if config else 'unknown'
        })
        
        # Start metrics server if enabled
        if self.metrics_enabled:
            try:
                start_http_server(config.prometheus_port)
                logger.info(f"Prometheus metrics server started on port {config.prometheus_port}")
            except Exception as e:
                logger.warning(f"Could not start Prometheus metrics server: {e}")
                self.metrics_enabled = False
    
    def record_document_generation_start(self):
        """Record the start of document generation"""
        if self.metrics_enabled:
            self.active_generations.inc()
    
    def record_document_generation_complete(
        self,
        doc_type: str,
        ai_provider: str,
        model: str,
        duration: float,
        tokens_used: Optional[int] = None,
        success: bool = True
    ):
        """Record completion of document generation"""
        if not self.metrics_enabled:
            return
            
        status = 'success' if success else 'error'
        
        # Record metrics
        self.documents_generated_total.labels(
            doc_type=doc_type,
            ai_provider=ai_provider,
            model=model,
            status=status
        ).inc()
        
        self.document_generation_duration.labels(
            doc_type=doc_type,
            ai_provider=ai_provider,
            model=model
        ).observe(duration)
        
        if tokens_used:
            self.ai_tokens_used.labels(
                ai_provider=ai_provider,
                model=model
            ).observe(tokens_used)
        
        self.active_generations.dec()
    
    def record_ai_request(self, ai_provider: str, model: str, success: bool = True):
        """Record AI API request"""
        if self.metrics_enabled:
            status = 'success' if success else 'error'
            self.ai_requests_total.labels(
                ai_provider=ai_provider,
                model=model,
                status=status
            ).inc()
    
    def update_template_count(self, count: int):
        """Update the number of available template types"""
        if self.metrics_enabled:
            self.template_types_available.set(count)

# Global metrics instance
_metrics_instance = None

def get_metrics(config=None) -> MetricsCollector:
    """Get or create global metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector(config)
    return _metrics_instance

class DocumentGenerationTimer:
    """Context manager for timing document generation"""
    
    def __init__(self, doc_type: str, ai_provider: str, model: str, metrics: MetricsCollector):
        self.doc_type = doc_type
        self.ai_provider = ai_provider
        self.model = model
        self.metrics = metrics
        self.start_time = None
        self.tokens_used = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.metrics.record_document_generation_start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        success = exc_type is None
        
        self.metrics.record_document_generation_complete(
            doc_type=self.doc_type,
            ai_provider=self.ai_provider,
            model=self.model,
            duration=duration,
            tokens_used=self.tokens_used,
            success=success
        )
    
    def set_tokens_used(self, tokens: int):
        """Set the number of tokens used during generation"""
        self.tokens_used = tokens