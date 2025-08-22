"""Document generator with AI integration"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from .ai_client import AIClient
from .templates import DocumentTemplates
from utils.logger import setup_logger
from utils.metrics import get_metrics, DocumentGenerationTimer

logger = setup_logger(__name__)

class DocumentGenerator:
    """Main document generator class"""
    
    def __init__(self, config):
        self.config = config
        self.ai_client = AIClient(config)

        # Pass configured templates directory to avoid hard-coded /app path during tests
        self.templates = DocumentTemplates(templates_dir=self.config.templates_dir)
        self.output_dir = Path(self.config.output_dir)
        self.metadata_file = self.output_dir / "documents_metadata.json"
        self.metrics = get_metrics(self.config)

        # Load existing metadata
        self._load_metadata()

        # Update template count metric
        self.metrics.update_template_count(len(self.templates.get_all_types()))
    
    def _load_metadata(self):
        """Load document metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save document metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save metadata: {e}")
    
    def get_available_types(self) -> Dict[str, Dict[str, str]]:
        """Get all available document types"""
        return self.templates.get_all_types()
    
    def get_template(self, doc_type: str) -> Optional[str]:
        """Get template for a document type"""
        return self.templates.get_template(doc_type)
    
    def add_document_type(self, doc_type: str, description: str, template: str) -> bool:
        """Add a new document type"""
        result = self.templates.add_custom_type(doc_type, description, template)
        if result:
            # Update template count metric
            self.metrics.update_template_count(len(self.templates.get_all_types()))
        return result
    
    async def generate_document(
        self,
        content: str,
        doc_type: str,
        title: str,
        context: str = "",
        ai_provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generate documentation from content"""
        
        # Get template
        template = self.templates.get_template(doc_type)
        if not template:
            raise ValueError(f"Unknown document type: {doc_type}")
        
        # Prepare prompt
        prompt = self._build_prompt(template, content, title, context)
        
        # Generate with AI using metrics timer
        logger.info(f"Generating {doc_type} document: {title}")
        
        with DocumentGenerationTimer(doc_type, ai_provider or self.config.default_ai_provider, 
                                    model or self.config.default_model, self.metrics) as timer:
            markdown_content = await self.ai_client.generate_text(
                prompt=prompt,
                provider=ai_provider or self.config.default_ai_provider,
                model=model or self.config.default_model,
                max_tokens=max_tokens or self.config.default_max_tokens,
                temperature=temperature or self.config.default_temperature
            )
            
            # Estimate tokens used (rough approximation: 1 token ≈ 4 characters)
            estimated_tokens = len(markdown_content) // 4
            timer.set_tokens_used(estimated_tokens)
        
        # Save document
        doc_id = str(uuid.uuid4())
        filename = f"{doc_id}_{doc_type}_{title.replace(' ', '_')}.md"
        filepath = self.output_dir / filename
        
        # Write markdown file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Update metadata
        self.metadata[doc_id] = {
            'id': doc_id,
            'title': title,
            'doc_type': doc_type,
            'filename': filename,
            'created_at': datetime.now().isoformat(),
            'ai_provider': ai_provider or self.config.default_ai_provider,
            'model': model or self.config.default_model,
            'max_tokens': max_tokens or self.config.default_max_tokens,
            'temperature': temperature or self.config.default_temperature,
            'context': context
        }
        self._save_metadata()
        
        logger.info(f"Generated document saved: {filename}")
        
        return {
            'id': doc_id,
            'filename': filename,
            'markdown': markdown_content,
            'metadata': self.metadata[doc_id]
        }
    
    def _build_prompt(self, template: str, content: str, title: str, context: str) -> str:
        """Build the AI prompt from template and inputs"""
        prompt = template.format(
            title=title,
            content=content,
            context=context if context else "No additional context provided."
        )
        return prompt
    
    def list_generated_documents(self, doc_type_filter: str = "") -> List[Dict[str, Any]]:
        """List all generated documents"""
        documents = []
        for doc_id, metadata in self.metadata.items():
            if not doc_type_filter or metadata['doc_type'] == doc_type_filter:
                documents.append(metadata)
        
        # Sort by creation date (newest first)
        documents.sort(key=lambda x: x['created_at'], reverse=True)
        return documents
    
    def get_generated_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a generated document by ID"""
        if document_id not in self.metadata:
            # Try to find by filename
            for doc_id, metadata in self.metadata.items():
                if metadata['filename'] == document_id or document_id in metadata['filename']:
                    document_id = doc_id
                    break
            else:
                return None
        
        metadata = self.metadata[document_id]
        filepath = self.output_dir / metadata['filename']
        
        if not filepath.exists():
            logger.warning(f"Document file not found: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                'metadata': metadata,
                'content': content
            }
        except Exception as e:
            logger.error(f"Error reading document {document_id}: {e}")
            return None