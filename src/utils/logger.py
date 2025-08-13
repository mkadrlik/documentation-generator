"""Logging configuration for Documentation Generator with Splunk support"""

import logging
import logging.handlers
import json
import os
import socket
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
import requests
import threading
import time

class LokiHandler(logging.Handler):
    """Custom handler for sending logs to Grafana Loki"""
    
    def __init__(self, host: str, port: int, username: str = '', password: str = '', tenant: str = ''):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.tenant = tenant
        self.url = f"http://{host}:{port}/loki/api/v1/push"
        
        # Setup headers
        self.headers = {'Content-Type': 'application/json'}
        if tenant:
            self.headers['X-Scope-OrgID'] = tenant
            
        # Setup session with auth if provided
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
        
        # Buffer for batching logs
        self.log_buffer = []
        self.buffer_lock = threading.Lock()
        self.last_flush = time.time()
        
    def emit(self, record):
        """Buffer log record for Loki"""
        try:
            # Create Loki log entry
            timestamp_ns = str(int(record.created * 1_000_000_000))  # Convert to nanoseconds
            
            # Create labels for Loki
            labels = {
                'job': 'documentation-generator',
                'level': record.levelname.lower(),
                'logger': record.name,
                'module': record.module,
                'function': record.funcName,
                'hostname': socket.gethostname()
            }
            
            # Create log line (JSON format)
            log_line = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'thread': record.thread,
                'process': record.process
            }
            
            # Add exception info if present
            if record.exc_info:
                log_line['exception'] = self.formatException(record.exc_info)
            
            # Buffer the log entry
            with self.buffer_lock:
                self.log_buffer.append({
                    'timestamp': timestamp_ns,
                    'labels': labels,
                    'line': json.dumps(log_line)
                })
                
                # Flush buffer if it's getting full or enough time has passed
                if len(self.log_buffer) >= 10 or (time.time() - self.last_flush) > 5:
                    self._flush_buffer()
            
        except Exception as e:
            # Fallback to stderr if Loki fails
            print(f"Failed to buffer log for Loki: {e}", file=sys.stderr)
    
    def _flush_buffer(self):
        """Flush buffered logs to Loki (runs in separate thread)"""
        if not self.log_buffer:
            return
            
        buffer_copy = self.log_buffer.copy()
        self.log_buffer.clear()
        self.last_flush = time.time()
        
        # Send in background thread
        threading.Thread(
            target=self._send_to_loki,
            args=(buffer_copy,),
            daemon=True
        ).start()
    
    def _send_to_loki(self, log_entries: List[Dict[str, Any]]):
        """Send log entries to Loki (runs in separate thread)"""
        try:
            # Group logs by labels
            streams = {}
            for entry in log_entries:
                label_str = json.dumps(entry['labels'], sort_keys=True)
                if label_str not in streams:
                    streams[label_str] = {
                        'stream': entry['labels'],
                        'values': []
                    }
                streams[label_str]['values'].append([entry['timestamp'], entry['line']])
            
            # Create Loki payload
            payload = {
                'streams': list(streams.values())
            }
            
            response = self.session.post(
                self.url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=5
            )
            
            if response.status_code not in [200, 204]:
                print(f"Loki HTTP error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Failed to send to Loki: {e}")
    
    def close(self):
        """Flush remaining logs when handler is closed"""
        with self.buffer_lock:
            self._flush_buffer()
        super().close()

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process,
            'hostname': socket.gethostname()
        }
        
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)

def setup_logger(name: str, level: Optional[str] = None, config=None) -> logging.Logger:
    """Setup logger with console, file, and optional Splunk/syslog output"""
    
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO')
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler for local logs
    try:
        os.makedirs('/app/logs', exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            '/app/logs/documentation-generator.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")
    
    # Grafana Loki handler
    if config and config.loki_enabled:
        try:
            loki_handler = LokiHandler(
                host=config.loki_host,
                port=config.loki_port,
                username=config.loki_username,
                password=config.loki_password,
                tenant=config.loki_tenant
            )
            logger.addHandler(loki_handler)
            logger.info("Grafana Loki logging enabled")
        except Exception as e:
            logger.warning(f"Could not setup Loki logging: {e}")
    
    # Syslog handler (alternative to Splunk)
    if config and config.syslog_enabled:
        try:
            # Map facility name to constant
            facility_map = {
                'local0': logging.handlers.SysLogHandler.LOG_LOCAL0,
                'local1': logging.handlers.SysLogHandler.LOG_LOCAL1,
                'local2': logging.handlers.SysLogHandler.LOG_LOCAL2,
                'local3': logging.handlers.SysLogHandler.LOG_LOCAL3,
                'local4': logging.handlers.SysLogHandler.LOG_LOCAL4,
                'local5': logging.handlers.SysLogHandler.LOG_LOCAL5,
                'local6': logging.handlers.SysLogHandler.LOG_LOCAL6,
                'local7': logging.handlers.SysLogHandler.LOG_LOCAL7,
                'user': logging.handlers.SysLogHandler.LOG_USER,
                'daemon': logging.handlers.SysLogHandler.LOG_DAEMON,
            }
            
            facility = facility_map.get(config.syslog_facility, logging.handlers.SysLogHandler.LOG_LOCAL0)
            
            syslog_handler = logging.handlers.SysLogHandler(
                address=(config.syslog_host, config.syslog_port),
                facility=facility
            )
            syslog_handler.setFormatter(JSONFormatter())
            logger.addHandler(syslog_handler)
            logger.info("Syslog logging enabled")
        except Exception as e:
            logger.warning(f"Could not setup syslog logging: {e}")
    
    return logger