from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import rag


app = FastAPI(
    title="BigCompany Agentic RAG API",
    description="An AI assistant that answers questions about BigCompany Inc. policies.",
)

# CORS (Cross-Origin Resource Sharing) allows the frontend
# to make requests to this backend.
# Without this, the browser would block the frontend from
# talking to the backend because they run on different ports.
#
# - Frontend runs on: http://localhost:3000
# - Backend runs on:  http://localhost:8000





# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"http://192\.168\.\d+\.\d+:3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag.router)



@app.get("/")
def read_root():
    return {"message": "BigCompany Agentic RAG API is running!"}
