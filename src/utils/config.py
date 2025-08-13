"""Configuration management for Documentation Generator"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Documentation Generator"""
    
    def __init__(self):
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.default_ai_provider = os.getenv('DEFAULT_AI_PROVIDER', 'openai')
        self.default_model = os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')
        self.default_max_tokens = int(os.getenv('DEFAULT_MAX_TOKENS', '4000'))
        self.default_temperature = float(os.getenv('DEFAULT_TEMPERATURE', '0.3'))
        
        # Grafana Loki configuration
        self.loki_enabled = os.getenv('LOKI_ENABLED', 'false').lower() == 'true'
        self.loki_host = os.getenv('LOKI_HOST', 'localhost')
        self.loki_port = int(os.getenv('LOKI_PORT', '3100'))
        self.loki_username = os.getenv('LOKI_USERNAME', '')
        self.loki_password = os.getenv('LOKI_PASSWORD', '')
        self.loki_tenant = os.getenv('LOKI_TENANT', '')
        
        # Prometheus metrics configuration
        self.prometheus_enabled = os.getenv('PROMETHEUS_ENABLED', 'false').lower() == 'true'
        self.prometheus_port = int(os.getenv('PROMETHEUS_PORT', '9090'))
        self.prometheus_path = os.getenv('PROMETHEUS_PATH', '/metrics')
        
        # Syslog configuration (alternative to Splunk HEC)
        self.syslog_enabled = os.getenv('SYSLOG_ENABLED', 'false').lower() == 'true'
        self.syslog_host = os.getenv('SYSLOG_HOST', 'localhost')
        self.syslog_port = int(os.getenv('SYSLOG_PORT', '514'))
        self.syslog_facility = os.getenv('SYSLOG_FACILITY', 'local0')
        
        # Paths
        self.output_dir = '/app/data/output'
        self.templates_dir = '/app/data/templates'
        
        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def get_ai_config(self, provider: str) -> Dict[str, Any]:
        """Get AI provider configuration"""
        if provider.lower() == 'openai':
            return {
                'api_key': self.openai_api_key,
                'provider': 'openai'
            }
        elif provider.lower() == 'anthropic':
            return {
                'api_key': self.anthropic_api_key,
                'provider': 'anthropic'
            }
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    def validate_ai_config(self, provider: str) -> bool:
        """Validate AI provider configuration"""
        try:
            config = self.get_ai_config(provider)
            return config['api_key'] is not None
        except ValueError:
            return False