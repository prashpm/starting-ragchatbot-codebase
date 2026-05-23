def test_query_creates_session_when_none_given(client, mock_rag_system):
    response = client.post("/api/query", json={"query": "What is Python?"})
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-id"
    assert data["answer"] == "Test answer"
    assert data["sources"] == ["source1", "source2"]
    mock_rag_system.session_manager.create_session.assert_called_once()


def test_query_reuses_existing_session(client, mock_rag_system):
    response = client.post(
        "/api/query",
        json={"query": "What is Python?", "session_id": "existing-session"},
    )
    assert response.status_code == 200
    assert response.json()["session_id"] == "existing-session"
    mock_rag_system.session_manager.create_session.assert_not_called()


def test_query_returns_500_on_rag_error(client, mock_rag_system):
    mock_rag_system.query.side_effect = RuntimeError("vector store unavailable")
    response = client.post("/api/query", json={"query": "anything"})
    assert response.status_code == 500
    assert "vector store unavailable" in response.json()["detail"]


def test_get_courses(client, mock_rag_system):
    response = client.get("/api/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["total_courses"] == 2
    assert data["course_titles"] == ["Course A", "Course B"]


def test_get_courses_returns_500_on_error(client, mock_rag_system):
    mock_rag_system.get_course_analytics.side_effect = RuntimeError("db error")
    response = client.get("/api/courses")
    assert response.status_code == 500
    assert "db error" in response.json()["detail"]
