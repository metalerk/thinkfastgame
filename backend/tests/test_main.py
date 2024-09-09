import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from app.main import app, get_db
from app.database import async_session


client = TestClient(app)

@pytest.fixture
async def override_get_db():
    async with async_session() as session:
        yield session

# fixture to override the get_db dependency
app.dependency_overrides[get_db] = override_get_db

# add a single question
@pytest.mark.asyncio
async def test_add_question():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/add_question", json={"question": "What is 2+2?", "answer": "4"})
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is 2+2?"
    assert data["answer"] == "4"
    assert "id" in data

# fetches the current question
@pytest.mark.asyncio
async def test_get_current_question():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/current_question")
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "answer" in data

# uploads a batch of questions
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

# websocket connection
@pytest.mark.asyncio
async def test_websocket_connection():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        async with ac.websocket_connect("/ws/quiz") as websocket:
            assert websocket
            message = await websocket.receive_text()
            assert "Current question:" in message
