from typing import List
import random

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, schemas


async def get_random_question(session: AsyncSession):
    """Gets a random question from the db"""
    result = await session.execute(select(models.Question))
    questions = result.scalars().all()
    if questions:
        return random.choice(questions)
    return None

async def create_question(session: AsyncSession, question: schemas.QuestionCreate):
    """
    Creates one question in the database.
    """
    db_question = models.Question(question=question.question, answer=question.answer)
    session.add(db_question)
    await session.commit()
    await session.refresh(db_question)
    return db_question

async def create_questions(session: AsyncSession, questions: List[schemas.QuestionCreate]):
    """
    Create multiple questions in the database.
    """
    db_questions = [models.Question(question=q.question, answer=q.answer) for q in questions]
    session.add_all(db_questions)
    await session.commit()
    return db_questions
