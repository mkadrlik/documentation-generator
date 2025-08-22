import os
import sys
import asyncio
import tempfile

import pytest

# Ensure src is on path so we can import the server module
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, ROOT)

# Make tests use writable fallback dirs instead of /app
_tmp = tempfile.mkdtemp(prefix="docgen_test_")
os.environ['FALLBACK_OUTPUT_DIR'] = os.path.join(_tmp, 'output')
os.environ['FALLBACK_TEMPLATES_DIR'] = os.path.join(_tmp, 'templates')

# Provide dummy openai and anthropic modules so importing the ai_client won't fail during tests
import types
sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('anthropic', types.ModuleType('anthropic'))
sys.modules.setdefault('prometheus_client', types.ModuleType('prometheus_client'))

# Populate the fake prometheus_client with the names used by utils.metrics
fake_prom = sys.modules['prometheus_client']
class _NoopMetric:
    def __init__(self, *args, **kwargs):
        pass
    def labels(self, *args, **kwargs):
        return self
    def inc(self, *args, **kwargs):
        pass
    def observe(self, *args, **kwargs):
        pass
    def set(self, *args, **kwargs):
        pass

def _start_http_server(port):
    return None

setattr(fake_prom, 'Counter', _NoopMetric)
setattr(fake_prom, 'Histogram', _NoopMetric)
setattr(fake_prom, 'Gauge', _NoopMetric)
setattr(fake_prom, 'Info', _NoopMetric)
setattr(fake_prom, 'start_http_server', _start_http_server)

from main import DocumentationGeneratorServer


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_transform_text_with_placeholder(monkeypatch):
    srv = DocumentationGeneratorServer()

    captured = {}

    async def fake_generate_text(prompt, provider=None, model=None, max_tokens=None, temperature=None):
        # ensure prompt was formatted and contains the content in-place
        captured['prompt'] = prompt
        return "FAKE_RESULT_WITH_PLACEHOLDER"

    # patch ai_client.generate_text
    monkeypatch.setattr(srv.generator.ai_client, 'generate_text', fake_generate_text)

    result = run_async(srv.handle_transform_text({
        'text': 'Hello world',
        'prompt': 'Please rewrite the following: {content}'
    }))

    assert isinstance(result, list) and len(result) == 1
    assert result[0].text == 'FAKE_RESULT_WITH_PLACEHOLDER'
    assert 'Hello world' in captured['prompt']


def test_transform_text_without_placeholder(monkeypatch):
    srv = DocumentationGeneratorServer()

    captured = {}

    async def fake_generate_text(prompt, provider=None, model=None, max_tokens=None, temperature=None):
        captured['prompt'] = prompt
        return "FAKE_RESULT_NO_PLACEHOLDER"

    monkeypatch.setattr(srv.generator.ai_client, 'generate_text', fake_generate_text)

    result = run_async(srv.handle_transform_text({
        'text': 'Summary text',
        'prompt': 'Summarize:'
    }))

    assert result[0].text == 'FAKE_RESULT_NO_PLACEHOLDER'
    # prompt should include the original prompt and the text appended
    assert 'Summarize:' in captured['prompt']
    assert 'Summary text' in captured['prompt']
