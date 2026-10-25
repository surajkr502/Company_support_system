import re
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from graph import compiled_graph

router = APIRouter()

GREETINGS = {"hi", "hello", "hey", "thanks", "thank you", "bye"}
GREETING_ANSWER = "Hello! Ask me anything about BigCompany's policies, engineering guidelines, or onboarding."
MAX_ATTEMPTS = 2


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str
    question: str


def is_quota_error(err: Exception) -> bool:
    msg = str(err).upper()
    return "RESOURCE_EXHAUSTED" in msg or "429" in msg or "QUOTA" in msg


@router.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    normalized = re.sub(r"[^\w\s]", "", question).lower().strip()
    if normalized in GREETINGS:
        return AnswerResponse(answer=GREETING_ANSWER, question=question)

    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = compiled_graph.invoke({"question": question, "retry_count": 0})
            answer = result.get("generation") or "I could not generate an answer."
            return AnswerResponse(answer=answer, question=result["question"])
        except Exception as e:
            print(f"RAG ERROR (attempt {attempt}/{MAX_ATTEMPTS}):", repr(e), flush=True)
            if is_quota_error(e):
                # Quota errors are not retried, so no extra requests are wasted.
                raise HTTPException(
                    status_code=429,
                    detail="Gemini free-tier quota is used up for this model. "
                           "Try again later or change GEMINI_CHAT_MODEL in backend/.env.",
                )
            last_error = e
            if attempt < MAX_ATTEMPTS:
                time.sleep(2)

    raise HTTPException(status_code=500, detail=f"Backend error: {last_error}")