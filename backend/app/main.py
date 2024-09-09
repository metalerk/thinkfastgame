from typing import List

import os
from pathlib import Path

from dotenv import load_dotenv
from redis.asyncio import Redis

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas, crud
from .database import get_db, engine, async_session


load_dotenv()

app = FastAPI()

# static files
frontend_path = Path(__file__).parent.parent / "frontend"

def should_mount_frontend():
    mount_frontend = os.getenv("TEST", "False").lower() == "false"
    return mount_frontend

if should_mount_frontend() and frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # left for now but not in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    if should_mount_frontend() and frontend_path.exists():
        return FileResponse(frontend_path / "index.html")
    else:
        return JSONResponse({"error": "Frontend not available"})

REDIS_URL = os.getenv("REDIS_URL")
redis = None


class ConnectionManager:
    """WebSocket connection manager"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Connected: {len(self.active_connections)} clients connected.")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Disconnected: {len(self.active_connections)} clients connected.")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# stores current question
current_question = None

@app.on_event("startup")
async def startup_event():
    global current_question, redis
    # database tables
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    redis = Redis.from_url(REDIS_URL, decode_responses=True)

    # load the first question from db
    async with async_session() as session:
        current_question = await crud.get_random_question(session)
    if current_question:
        await manager.broadcast(f"New question: {current_question.question}")
    else:
        await manager.broadcast("No questions available.")

@app.on_event("shutdown")
async def shutdown_event():
    if redis:
        await redis.close()

@app.websocket("/ws/quiz")
async def quiz_websocket(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    global current_question
    await manager.connect(websocket)
    try:
        # Send question to the connected user
        if current_question:
            await websocket.send_text(f"Current question: {current_question.question}")
        else:
            await websocket.send_text("No question available at the moment.")
        
        while True:
            answer = await websocket.receive_text()
            if not current_question:
                await websocket.send_text("No active question. Please wait for the next one.")
                continue

            # attempt to acquire a lock for answering using redis
            # IP address as identifier
            client_id = websocket.client.host
            lock_key = f"lock:question:{current_question.id}"
            # client_id instead of websocket.client
            acquired = await redis.setnx(lock_key, client_id)
            if acquired:
                # expiration to prevent deadlocks
                await redis.expire(lock_key, 5)  # 5 seconds

                if answer.strip().lower() == current_question.answer.strip().lower():
                    # winner is the client IP address
                    winner = client_id
                    await websocket.send_text("Correct! You answered first.")
                    await manager.broadcast("Someone has answered the question correctly! Moving to the next question.")
                    
                    # next question
                    async with db as session:
                        next_question = await crud.get_random_question(session)
                        if next_question:
                            current_question = next_question  # Update the global current_question
                            await manager.broadcast(f"New question: {current_question.question}")
                        else:
                            current_question = None
                            await manager.broadcast("No more questions available.")
                else:
                    await websocket.send_text("Wrong answer. Try again!")
            else:
                # lock acquired,someone has answered already
                await websocket.send_text("Sorry, this question was already answered!")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/current_question", response_model=schemas.Question)
async def get_current_question(db: AsyncSession = Depends(get_db)):
    global current_question
    if current_question:
        return current_question
    else:
        return {"id": 0, "question": "No active question", "answer": ""}

@app.post("/add_question", response_model=schemas.Question)
async def add_question(question: schemas.QuestionCreate, db: AsyncSession = Depends(get_db)):
    """Add a question"""
    return await crud.create_question(db, question)

@app.post("/upload_questions", response_model=List[schemas.Question])
async def upload_questions(questions: List[schemas.QuestionCreate], db: AsyncSession = Depends(get_db)):
    """
    Endpoint to upload a batch of quiz questions.
    e.g.:
    POST /upload_questions
    [
        {"question": "What is the capital of France?", "answer": "Paris"},
        {"question": "What is 2+2?", "answer": "4"}
    ]
    """
    try:
        return await crud.create_questions(db, questions)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
