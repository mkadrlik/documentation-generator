# Documentation Generator MCP Server

An MCP (Model Context Protocol) server that transforms meeting notes, transcriptions, and group chats into structured documentation of various types.

## Features

- **Multiple Document Types**: SOPs, Runbooks, Architecture docs, Implementation docs, and more
- **AI-Powered Generation**: Uses OpenAI or Anthropic models for intelligent document creation
- **Modular Architecture**: Easy to add new document types and templates
- **Persistent Storage**: Saves generated documents with metadata
- **Docker Support**: Runs in containers for easy deployment

## Supported Document Types

1. **SOP (Standard Operating Procedure)** - Step-by-step process documentation
2. **Runbook** - Operational troubleshooting and maintenance procedures
3. **Architecture** - High-level system design documentation
4. **Implementation** - Detailed technical specifications
5. **Meeting Summary** - Key decisions and action items
6. **Technical Spec** - Feature specifications with requirements
7. **API Documentation** - Endpoint documentation with examples
8. **User Guide** - End-user documentation and tutorials

## MCP Tools

- `list_document_types` - List all available documentation types
- `generate_documentation` - Generate documentation from meeting content
- `get_document_template` - View the template for a document type
- `add_document_type` - Add custom document types
- `list_generated_documents` - List previously generated documents
- `get_generated_document` - Retrieve a generated document

## Setup

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# AI Provider Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Default AI Settings
DEFAULT_AI_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_MAX_TOKENS=4000
DEFAULT_TEMPERATURE=0.3

# Logging
LOG_LEVEL=INFO

# Grafana Integration (optional)
LOKI_ENABLED=true
LOKI_HOST=your-loki-host.com
LOKI_PORT=3100
LOKI_USERNAME=your-username
LOKI_PASSWORD=your-password

# Prometheus Metrics (optional)
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Syslog Integration (alternative)
SYSLOG_ENABLED=false
SYSLOG_HOST=localhost
SYSLOG_PORT=514
SYSLOG_FACILITY=local0
```

### Docker Deployment

```bash
# Build and run
docker compose up --build -d

# Check logs
docker compose logs -f

# Stop
docker compose down
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
cd src
python main.py
```

## Usage Examples

### Generate an SOP

```json
{
  "tool": "generate_documentation",
  "arguments": {
    "content": "Meeting notes about our deployment process...",
    "doc_type": "sop",
    "title": "Production Deployment Process",
    "context": "This is for our web application deployment",
    "ai_provider": "openai",
    "model": "gpt-4o-mini"
  }
}
```

### Add Custom Document Type

```json
{
  "tool": "add_document_type",
  "arguments": {
    "doc_type": "incident_report",
    "description": "Post-incident analysis and lessons learned",
    "template": "Create an incident report based on: {content}..."
  }
}
```

## Architecture

```
documentation-generator/
├── src/
│   ├── main.py                 # MCP server entry point
│   ├── generators/
│   │   ├── document_generator.py  # Main document generation logic
│   │   ├── ai_client.py           # AI provider integration
│   │   └── templates.py           # Document templates and prompts
│   ├── utils/
│   │   ├── config.py              # Configuration management
│   │   └── logger.py              # Logging setup
│   └── templates/                 # Template storage
├── data/
│   ├── output/                    # Generated documents
│   └── templates/                 # Custom templates
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Adding New Document Types

1. **Via MCP Tool** (Recommended):
   Use the `add_document_type` tool to add new types dynamically.

2. **Via Code**:
   Add new templates to `src/generators/templates.py` in the `builtin_templates` dictionary.

## Template Format

Templates use Python string formatting with these variables:
- `{title}` - Document title
- `{content}` - Source meeting content
- `{context}` - Additional context provided

Example template:
```python
template = '''Create a {doc_type} document titled "{title}".

Source content: {content}

Additional context: {context}

Please format as markdown with clear sections...'''
```

## Logging and Monitoring

The Documentation Generator supports comprehensive logging and metrics for Grafana integration:

### **Console Logging**
Always enabled for development and debugging.

### **File Logging**
Structured JSON logs written to `/app/logs/documentation-generator.log` with automatic rotation.

### **Grafana Loki Integration**
Direct integration with Grafana Loki for centralized logging:

```bash
LOKI_ENABLED=true
LOKI_HOST=your-loki-host.com
LOKI_PORT=3100
LOKI_USERNAME=your-username
LOKI_PASSWORD=your-password
LOKI_TENANT=your-tenant-id
```

### **Prometheus Metrics**
Comprehensive metrics for Grafana dashboards:

```bash
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

**Available Metrics:**
- `documents_generated_total` - Total documents generated by type and AI provider
- `document_generation_duration_seconds` - Time spent generating documents
- `ai_tokens_used_total` - AI tokens consumed by provider and model
- `ai_requests_total` - AI API requests by provider and status
- `active_document_generations` - Currently active generations
- `template_types_available` - Number of available document templates

### **Syslog Integration**
Alternative centralized logging option:

```bash
SYSLOG_ENABLED=true
SYSLOG_HOST=your-syslog-server.com
SYSLOG_PORT=514
SYSLOG_FACILITY=local0
```

### **Log Format**
All network logs use structured JSON format with Loki labels:

```json
{
  "timestamp": "2025-08-13T14:30:00.123Z",
  "level": "INFO",
  "logger": "main",
  "message": "Generated SOP document: Production Deployment",
  "module": "document_generator",
  "function": "generate_document",
  "hostname": "doc-generator-01",
  "doc_type": "sop",
  "ai_provider": "openai"
}
```

### **Grafana Dashboard Queries**

**Document Generation Rate:**
```promql
rate(documents_generated_total[5m])
```

**Average Generation Time:**
```promql
rate(document_generation_duration_seconds_sum[5m]) / rate(document_generation_duration_seconds_count[5m])
```

**AI Token Usage:**
```promql
rate(ai_tokens_used_total[5m])
```

## Integration with Docker MCP Gateway

This server is designed to work with Docker MCP Gateway. Configure your gateway to route documentation requests to this service.

## License

MIT License