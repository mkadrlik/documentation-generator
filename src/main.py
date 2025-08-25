#!/usr/bin/env python3
"""
Documentation Generator MCP Server

Transforms meeting notes, transcriptions, and group chats into structured documentation.
Supports multiple document types with modular architecture for easy extension.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from generators.document_generator import DocumentGenerator
from utils.config import Config
from utils.logger import setup_logger

# Setup configuration first
config = Config()

# Setup logging with config
logger = setup_logger(__name__, config=config)

class DocumentationGeneratorServer:
    """MCP Server for generating documentation from meeting content"""
    
    def __init__(self):
        self.config = config  # Use the global config instance
        self.generator = DocumentGenerator(self.config)
        logger.info("Documentation Generator MCP Server initialized")
    
    def get_available_tools(self) -> List[Tool]:
        """Return list of available MCP tools"""
        return [
            Tool(
                name="list_document_types",
                description="List all available documentation types that can be generated",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="generate_documentation",
                description="Generate documentation from meeting content (notes, transcriptions, or chats)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The meeting content (notes, transcription, or chat log)"
                        },
                        "doc_type": {
                            "type": "string",
                            "description": "Type of documentation to generate (sop, runbook, architecture, implementation, etc.)"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title for the generated document"
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context or requirements for the documentation",
                            "default": ""
                        },
                        "ai_provider": {
                            "type": "string",
                            "description": "AI provider to use (openai, anthropic, openrouter)",
                            "default": "openai"
                        },
                        "model": {
                            "type": "string",
                            "description": "AI model to use",
                            "default": "gpt-4o-mini"
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens for AI generation",
                            "default": 4000
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for AI generation (0.0-1.0)",
                            "default": 0.3
                        }
                    },
                    "required": ["content", "doc_type", "title"]
                }
            ),
            Tool(
                name="get_document_template",
                description="Get the template/prompt for a specific document type",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doc_type": {
                            "type": "string",
                            "description": "Type of documentation template to retrieve"
                        }
                    },
                    "required": ["doc_type"]
                }
            ),
            Tool(
                name="transform_text",
                description="Transform arbitrary text using a provided prompt via the configured AI provider",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "The text to transform"},
                        "prompt": {"type": "string", "description": "Prompt or template to apply to the text (may include {content})"},
                        "ai_provider": {"type": "string", "description": "AI provider to use (optional)"},
                        "model": {"type": "string", "description": "Model to use (optional)"},
                        "max_tokens": {"type": "integer", "description": "Max tokens for generation (optional)"},
                        "temperature": {"type": "number", "description": "Temperature for generation (optional)"}
                    },
                    "required": ["text", "prompt"]
                }
            ),
            Tool(
                name="add_document_type",
                description="Add a new document type with custom template/prompt",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doc_type": {
                            "type": "string",
                            "description": "Name of the new document type"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of what this document type generates"
                        },
                        "template": {
                            "type": "string",
                            "description": "Template/prompt for generating this document type"
                        }
                    },
                    "required": ["doc_type", "description", "template"]
                }
            ),
            Tool(
                name="list_generated_documents",
                description="List all previously generated documents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "doc_type": {
                            "type": "string",
                            "description": "Filter by document type (optional)",
                            "default": ""
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_generated_document",
                description="Retrieve a previously generated document",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "ID or filename of the document to retrieve"
                        }
                    },
                    "required": ["document_id"]
                }
            )
        ]
    
    async def handle_list_document_types(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List all available documentation types"""
        try:
            doc_types = self.generator.get_available_types()
            
            result = "# Available Documentation Types\n\n"
            for doc_type, info in doc_types.items():
                result += f"## {doc_type}\n"
                result += f"**Description:** {info['description']}\n\n"
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Error listing document types: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def handle_generate_documentation(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Generate documentation from meeting content"""
        try:
            content = arguments["content"]
            doc_type = arguments["doc_type"]
            title = arguments["title"]
            context = arguments.get("context", "")
            ai_provider = arguments.get("ai_provider", self.config.default_ai_provider)
            model = arguments.get("model", self.config.default_model)
            max_tokens = arguments.get("max_tokens", self.config.default_max_tokens)
            temperature = arguments.get("temperature", self.config.default_temperature)
            
            # Generate the documentation
            result = await self.generator.generate_document(
                content=content,
                doc_type=doc_type,
                title=title,
                context=context,
                ai_provider=ai_provider,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return [TextContent(type="text", text=result["markdown"])]
            
        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def handle_get_document_template(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get template for a document type"""
        try:
            doc_type = arguments["doc_type"]
            template = self.generator.get_template(doc_type)
            
            result = f"# Template for {doc_type}\n\n```\n{template}\n```"
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def handle_add_document_type(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Add a new document type"""
        try:
            doc_type = arguments["doc_type"]
            description = arguments["description"]
            template = arguments["template"]
            
            success = self.generator.add_document_type(doc_type, description, template)
            
            if success:
                return [TextContent(type="text", text=f"Successfully added document type: {doc_type}")]
            else:
                return [TextContent(type="text", text=f"Failed to add document type: {doc_type}")]
                
        except Exception as e:
            logger.error(f"Error adding document type: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def handle_transform_text(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Transform arbitrary text using a provided prompt and AI client."""
        try:
            text = arguments.get("text", "")
            prompt = arguments.get("prompt", "")
            ai_provider = arguments.get("ai_provider", self.config.default_ai_provider)
            model = arguments.get("model", self.config.default_model)
            max_tokens = arguments.get("max_tokens", self.config.default_max_tokens)
            temperature = arguments.get("temperature", self.config.default_temperature)

            if "{content}" in prompt:
                final_prompt = prompt.format(content=text)
            else:
                # If prompt doesn't include placeholder, append the text to the prompt
                final_prompt = f"{prompt}\n\n{text}"

            # Call AI client
            result_text = await self.generator.ai_client.generate_text(
                prompt=final_prompt,
                provider=ai_provider,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return [TextContent(type="text", text=result_text)]

        except Exception as e:
            logger.error(f"Error transforming text: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def handle_list_generated_documents(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List generated documents"""
        try:
            doc_type_filter = arguments.get("doc_type", "")
            documents = self.generator.list_generated_documents(doc_type_filter)
            
            if not documents:
                return [TextContent(type="text", text="No generated documents found.")]
            
            result = "# Generated Documents\n\n"
            for doc in documents:
                result += f"- **{doc['title']}** ({doc['doc_type']}) - {doc['created_at']}\n"
                result += f"  ID: `{doc['id']}`\n\n"
            
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def handle_get_generated_document(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get a generated document"""
        try:
            document_id = arguments["document_id"]
            document = self.generator.get_generated_document(document_id)
            
            if document:
                return [TextContent(type="text", text=document["content"])]
            else:
                return [TextContent(type="text", text=f"Document not found: {document_id}")]
                
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]


class CustomServer(Server):
    """Custom Server class with simplified initialization options"""
    
    def create_initialization_options(self) -> Dict[str, Any]:
        """Create simplified initialization options"""
        return {
            "name": "documentation-generator",
            "version": "1.0.0"
        }

def create_server() -> Server:
    """Create and configure the MCP server"""
    server = Server("documentation-generator")
    doc_server = DocumentationGeneratorServer()
    
    # Register tools
    tools = doc_server.get_available_tools()
    for tool in tools:
        @server.call_tool()
        async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "list_document_types":
                return await doc_server.handle_list_document_types(arguments)
            elif name == "generate_documentation":
                return await doc_server.handle_generate_documentation(arguments)
            elif name == "get_document_template":
                return await doc_server.handle_get_document_template(arguments)
            elif name == "add_document_type":
                return await doc_server.handle_add_document_type(arguments)
            elif name == "transform_text":
                return await doc_server.handle_transform_text(arguments)
            elif name == "list_generated_documents":
                return await doc_server.handle_list_generated_documents(arguments)
            elif name == "get_generated_document":
                return await doc_server.handle_get_generated_document(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    # Register list_tools handler
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return tools
    
    return server


async def main():
    """Main entry point"""
    logger.info("Starting Documentation Generator MCP Server...")
    
    # Debug: Print environment variables
    import os
    logger.info("Environment variables:")
    for key, value in sorted(os.environ.items()):
        logger.info(f"  {key}={value}")
    
    # Initialize server
    server = create_server()
    
    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        # Debug: Print initialization options
        init_options = server.create_initialization_options()
        logger.info(f"Initialization options type: {type(init_options)}")
        
        if hasattr(init_options, '__dict__'):
            logger.info("Initialization options attributes:")
            for key, value in init_options.__dict__.items():
                logger.info(f"  {key}={value}")
        
        # Use the original initialization options but catch and log any errors
        try:
            # Run server with debugging
            logger.info("Running server with stdio transport...")
            await server.run(read_stream, write_stream, init_options)
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fall back to original behavior
            logger.info("Falling back to original behavior...")
            await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())