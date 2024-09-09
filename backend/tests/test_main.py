import pytest

from httpx import AsyncClient

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app, get_db
from app.database import async_session


client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_static_dir():
    with mock.patch("app.main.Path.exists", return_value=False):
        yield

def test_get_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"error": "Frontend not available"}

@pytest.fixture
async def override_get_db():
    async with async_session() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.mark.asyncio
async def test_add_question():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/add_question", json={"question": "What is 2+2?", "answer": "4"})
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is 2+2?"
    assert data["answer"] == "4"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_current_question():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/current_question")
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "answer" in data

@pytest.mark.asyncio
async def test_upload_batch_questions():
    batch_questions = [
        {"question": "What is the capital of France?", "answer": "Paris"},
        {"question": "What is the capital of Germany?", "answer": "Berlin"},
        {"question": "What is the capital of Italy?", "answer": "Rome"}
    ]
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/upload_questions", json=batch_questions)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for question in batch_questions:
        assert question["question"] in [q["question"] for q in data]
        assert question["answer"] in [q["answer"] for q in data]
