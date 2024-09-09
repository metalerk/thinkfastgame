from unittest import mock
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

def mock_static_dir():
    with mock.patch.object(Path, "exists", return_value=False):
        yield

def test_add_question():
    """Test to add a single question"""
    response = client.post("/add_question", json={"question": "What is 2+2?", "answer": "4"})
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is 2+2?"
    assert data["answer"] == "4"
    assert "id" in data

def test_get_current_question():
    """Test to fetch the current question"""
    response = client.get("/current_question")
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "answer" in data

def test_get_homepage():
    """Test to serve the homepage or static content"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"error": "Frontend not available"}
