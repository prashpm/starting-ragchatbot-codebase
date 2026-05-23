import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Add backend to path so test imports resolve the same way uvicorn does
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Import create_app now so 'app' is in sys.modules before any patch() runs.
# The module-level `app = create_app()` succeeds because we guard the static
# mount on os.path.isdir("../frontend"), which is false in the test environment.
from app import create_app  # noqa: E402


@pytest.fixture
def mock_rag_system():
    mock = MagicMock()
    mock.session_manager.create_session.return_value = "test-session-id"
    mock.query.return_value = ("Test answer", ["source1", "source2"])
    mock.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Course A", "Course B"],
    }
    return mock


@pytest.fixture
def client(mock_rag_system):
    """TestClient backed by a no-static-files app with a mocked RAG system.

    The patch replaces app.RAGSystem for the duration of create_app() so the
    new test app closes over the mock instance instead of a live RAGSystem.
    """
    with patch("app.RAGSystem", return_value=mock_rag_system):
        test_app = create_app(serve_static=False)
    return TestClient(test_app)
