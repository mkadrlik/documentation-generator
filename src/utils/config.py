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
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
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
        
        # Paths with fallbacks
        fallback_output = os.getenv('FALLBACK_OUTPUT_DIR', '/tmp/documentation-output')
        fallback_templates = os.getenv('FALLBACK_TEMPLATES_DIR', '/tmp/documentation-templates')
        
        self.output_dir = self._setup_directory('/app/data/output', fallback_output)
        self.templates_dir = self._setup_directory('/app/data/templates', fallback_templates)
    
    def _setup_directory(self, primary_path: str, fallback_path: str) -> str:
        """Setup directory with fallback if permissions fail"""
        try:
            os.makedirs(primary_path, exist_ok=True)
            # Test write permissions
            test_file = os.path.join(primary_path, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.unlink(test_file)
            return primary_path
        except (PermissionError, OSError):
            # Fall back to temp directory
            try:
                os.makedirs(fallback_path, exist_ok=True)
                return fallback_path
            except (PermissionError, OSError):
                # Last resort: use current directory
                return os.getcwd()
    
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
        elif provider.lower() == 'openrouter':
            return {
                'api_key': self.openrouter_api_key,
                'provider': 'openrouter'
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