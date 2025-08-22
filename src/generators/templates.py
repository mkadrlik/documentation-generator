"""Document templates and prompts for different documentation types"""

import json
from pathlib import Path
from typing import Dict, Optional

from utils.logger import setup_logger

logger = setup_logger(__name__)

class DocumentTemplates:
    """Manages document templates and prompts"""
    
    def __init__(self, templates_dir: Optional[str] = None):
        # Allow configurable templates directory (helps tests and non-container runs)
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path('/app/data/templates')

        self.custom_templates_file = self.templates_dir / 'custom_templates.json'
        
        # Ensure templates directory exists (best-effort)
        try:
            self.templates_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If we can't create the desired path (e.g., permissions), fall back silently
            # The caller (e.g., DocumentGenerator) should pass a writable path when possible
            pass
        
        # Load custom templates
        self._load_custom_templates()
        
        # Built-in templates
        self.builtin_templates = {
            'sop': {
                'description': 'Standard Operating Procedure - Step-by-step process documentation',
                'template': self._get_sop_template()
            },
            'runbook': {
                'description': 'Operational Runbook - Troubleshooting and maintenance procedures',
                'template': self._get_runbook_template()
            },
            'architecture': {
                'description': 'High-level Architectural Documentation - System design and components',
                'template': self._get_architecture_template()
            },
            'implementation': {
                'description': 'Implementation-level Documentation - Detailed technical specifications',
                'template': self._get_implementation_template()
            },
            'meeting_summary': {
                'description': 'Meeting Summary - Key decisions, action items, and outcomes',
                'template': self._get_meeting_summary_template()
            },
            'technical_spec': {
                'description': 'Technical Specification - Detailed feature or component specification',
                'template': self._get_technical_spec_template()
            },
            'api_doc': {
                'description': 'API Documentation - Endpoints, parameters, and usage examples',
                'template': self._get_api_doc_template()
            },
            'user_guide': {
                'description': 'User Guide - End-user documentation and tutorials',
                'template': self._get_user_guide_template()
            },
            'technical_doc': {
                'description': 'Technical Documentation - Structured and well formatted documentation for technical scenarios',
                'template': self._get_technical_documentation_template()
            },
        }
    
    def _load_custom_templates(self):
        """Load custom templates from file"""
        if self.custom_templates_file.exists():
            try:
                with open(self.custom_templates_file, 'r') as f:
                    self.custom_templates = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load custom templates: {e}")
                self.custom_templates = {}
        else:
            self.custom_templates = {}
    
    def _save_custom_templates(self):
        """Save custom templates to file"""
        try:
            with open(self.custom_templates_file, 'w') as f:
                json.dump(self.custom_templates, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save custom templates: {e}")
    
    def get_all_types(self) -> Dict[str, Dict[str, str]]:
        """Get all available document types"""
        all_types = {}
        all_types.update(self.builtin_templates)
        all_types.update(self.custom_templates)
        return all_types
    
    def get_template(self, doc_type: str) -> Optional[str]:
        """Get template for a document type"""
        if doc_type in self.builtin_templates:
            return self.builtin_templates[doc_type]['template']
        elif doc_type in self.custom_templates:
            return self.custom_templates[doc_type]['template']
        else:
            return None
    
    def add_custom_type(self, doc_type: str, description: str, template: str) -> bool:
        """Add a custom document type"""
        try:
            self.custom_templates[doc_type] = {
                'description': description,
                'template': template
            }
            self._save_custom_templates()
            logger.info(f"Added custom document type: {doc_type}")
            return True
        except Exception as e:
            logger.error(f"Error adding custom type {doc_type}: {e}")
            return False
    
    def _get_sop_template(self) -> str:
        """Standard Operating Procedure template"""
        return """Create a comprehensive Standard Operating Procedure (SOP) document based on the following meeting content.

**Title:** {title}

**Source Content:**
{content}

**Additional Context:**
{context}

Please create a well-structured SOP document in markdown format that includes:

1. **Purpose and Scope** - What this SOP covers and why it exists
2. **Prerequisites** - Required knowledge, tools, or permissions
3. **Step-by-Step Procedure** - Detailed, numbered steps with clear instructions
4. **Decision Points** - What to do in different scenarios
5. **Quality Checks** - How to verify each step was completed correctly
6. **Troubleshooting** - Common issues and their solutions
7. **References** - Related documents or resources

Format the document with clear headings, bullet points, and code blocks where appropriate. Make it actionable and easy to follow for someone unfamiliar with the process."""
    
    def _get_runbook_template(self) -> str:
        """Operational Runbook template"""
        return """Create a comprehensive Operational Runbook based on the following meeting content.

**Title:** {title}

**Source Content:**
{content}

**Additional Context:**
{context}

Please create a well-structured runbook document in markdown format that includes:

1. **Overview** - System/service description and key components
2. **Architecture Diagram** - High-level system architecture (describe in text)
3. **Monitoring and Alerts** - Key metrics to watch and alert thresholds
4. **Common Issues** - Frequent problems and their symptoms
5. **Troubleshooting Procedures** - Step-by-step diagnostic and resolution steps
6. **Emergency Procedures** - Critical incident response steps
7. **Maintenance Tasks** - Regular maintenance procedures and schedules
8. **Escalation Paths** - When and how to escalate issues
9. **Contact Information** - Key personnel and their roles
10. **References** - Links to logs, dashboards, and related documentation

Focus on operational scenarios, include command examples, and make it practical for on-call engineers."""
    
    def _get_architecture_template(self) -> str:
        """High-level Architecture template"""
        return """Create comprehensive high-level architectural documentation based on the following meeting content.

**Title:** {title}

**Source Content:**
{content}

**Additional Context:**
{context}

Please create a well-structured architecture document in markdown format that includes:

1. **Executive Summary** - Brief overview of the system and its purpose
2. **System Overview** - High-level description of what the system does
3. **Architecture Principles** - Key design principles and constraints
4. **System Architecture** - Major components and their relationships
5. **Data Flow** - How data moves through the system
6. **Integration Points** - External systems and APIs
7. **Security Considerations** - Authentication, authorization, and data protection
8. **Scalability and Performance** - How the system handles load and growth
9. **Deployment Architecture** - Infrastructure and deployment considerations
10. **Technology Stack** - Key technologies and frameworks used
11. **Future Considerations** - Planned improvements and potential challenges

Focus on the big picture, avoid implementation details, and make it accessible to both technical and non-technical stakeholders."""
    
    def _get_implementation_template(self) -> str:
        """Implementation-level Documentation template"""
        return """Create detailed implementation-level documentation based on the following meeting content.

**Title:** {title}

**Source Content:**
{content}

**Additional Context:**
{context}

Please create a comprehensive implementation document in markdown format that includes:

1. **Implementation Overview** - What is being implemented and why
2. **Technical Requirements** - Specific technical requirements and constraints
3. **Detailed Design** - Low-level design decisions and rationale
4. **Code Structure** - File organization, modules, and key classes/functions
5. **Database Schema** - Tables, relationships, and indexes (if applicable)
6. **API Specifications** - Detailed endpoint definitions with examples
7. **Configuration** - Environment variables, config files, and settings
8. **Testing Strategy** - Unit tests, integration tests, and test data
9. **Deployment Instructions** - Step-by-step deployment process
10. **Performance Considerations** - Optimization techniques and benchmarks
11. **Error Handling** - Exception handling and error recovery
12. **Logging and Monitoring** - What to log and how to monitor
13. **Code Examples** - Key implementation snippets and usage examples

Focus on technical details that developers need to understand, maintain, and extend the implementation."""
    
    def _get_meeting_summary_template(self) -> str:
        """Meeting Summary template"""
        return """Create a comprehensive meeting summary based on the following content.

**Meeting Title:** {title}

**Meeting Content:**
{content}

**Additional Context:**
{context}

Please create a well-structured meeting summary in markdown format that includes:

1. **Meeting Details** - Date, attendees, and purpose
2. **Key Decisions** - Important decisions made during the meeting
3. **Action Items** - Tasks assigned with owners and due dates
4. **Discussion Points** - Main topics discussed and outcomes
5. **Next Steps** - What happens next and follow-up meetings
6. **Parking Lot** - Items tabled for future discussion
7. **Resources Mentioned** - Links, documents, or tools referenced

Extract the most important information and present it in a clear, actionable format."""
    
    def _get_technical_spec_template(self) -> str:
        """Technical Specification template"""
        return """Create a detailed technical specification based on the following meeting content.

**Feature/Component:** {title}

**Source Content:**
{content}

**Additional Context:**
{context}

Please create a comprehensive technical specification in markdown format that includes:

1. **Overview** - What is being specified and its purpose
2. **Functional Requirements** - What the system must do
3. **Non-Functional Requirements** - Performance, security, usability requirements
4. **User Stories** - Key user scenarios and acceptance criteria
5. **Technical Approach** - High-level technical solution
6. **Interface Specifications** - APIs, data formats, and protocols
7. **Data Models** - Data structures and relationships
8. **Security Requirements** - Authentication, authorization, and data protection
9. **Performance Requirements** - Response times, throughput, and scalability
10. **Testing Requirements** - Test scenarios and acceptance criteria
11. **Dependencies** - External systems, libraries, and services
12. **Risks and Assumptions** - Potential issues and assumptions made

Focus on providing clear, testable requirements that can guide implementation."""
    
    def _get_api_doc_template(self) -> str:
        """API Documentation template"""
        return """Create comprehensive API documentation based on the following meeting content.

**API Title:** {title}

**Source Content:**
{content}

**Additional Context:**
{context}

Please create detailed API documentation in markdown format that includes:

1. **API Overview** - Purpose and capabilities of the API
2. **Authentication** - How to authenticate with the API
3. **Base URL and Versioning** - API base URL and version information
4. **Endpoints** - Detailed endpoint documentation including:
   - HTTP method and URL
   - Request parameters and body
   - Response format and status codes
   - Example requests and responses
5. **Data Models** - Schema definitions for request/response objects
6. **Error Handling** - Common error codes and their meanings
7. **Rate Limiting** - Request limits and throttling policies
8. **SDKs and Libraries** - Available client libraries
9. **Code Examples** - Sample code in different programming languages
10. **Changelog** - API version history and changes

Make it practical for developers to integrate with the API quickly."""
    
    def _get_user_guide_template(self) -> str:
        """User Guide template"""
        return """Create a comprehensive user guide based on the following meeting content.

**Product/Feature:** {title}

**Source Content:**
{content}

**Additional Context:**
{context}

Please create a user-friendly guide in markdown format that includes:

1. **Getting Started** - Quick start guide for new users
2. **Overview** - What the product/feature does and key benefits
3. **Setup and Installation** - How to get started (if applicable)
4. **Basic Usage** - Core features and common tasks
5. **Step-by-Step Tutorials** - Detailed walkthroughs for key workflows
6. **Advanced Features** - More complex functionality and use cases
7. **Tips and Best Practices** - How to get the most out of the product
8. **Troubleshooting** - Common issues and solutions
9. **FAQ** - Frequently asked questions
10. **Support and Resources** - Where to get help and additional information

Write in a friendly, accessible tone that non-technical users can understand. Include screenshots descriptions where helpful."""

    def _get_technical_documentation_template(self) -> str:
        """Technical Documentation template"""
        return """Create a comprehensive techhical document, written by a technical writer, based on the following content and context.

**Document Title:** {title}

**Initial Content:**
{content}

**Additional Context:**
{context}

Please create a well-structured technical document in markdown format that:

1. Emphasize clarity, conciseness, and accuracy in conveying technical information
2. Follows Microsoft style guide for document formatting
3. Expands the content and context provided by researching online for further context, and add citations for those references inline
4. Adds in any Mermaid flow charts to provide further clarity to contexts
5. Uses the ### markdown as a delimiter to break an existing document into multiple sections within the same document
6. Does not use periods, exclamation points, question marks, etc. on sentences within bulleted or numbered lists
7. Provides code snippets or other bread crumbs for further clarity

Return document in the format outlined in the above steps."""