import os
from typing import List, Literal
from typing_extensions import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph


# ============================================================
# 1. Load environment variables
# ============================================================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MAX_REWRITES = int(os.getenv("MAX_REWRITES", "2"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY was not found. Add it to your .env file."
    )


# ============================================================
# 2. BigCompany Inc. Knowledge Base
# ============================================================
company_documents = [
    Document(
        page_content=(
            "BigCompany Inc. Remote Work Policy: Employees may work remotely up to "
            "3 days per week. All employees must be in the office on Tuesdays and "
            "Thursdays for team collaboration days. Remote work requests must be "
            "approved by the direct manager. Employees working remotely must be "
            "available on Slack during core hours (10 AM - 4 PM local time)."
        ),
        metadata={"source": "hr_handbook", "topic": "remote_work"},
    ),
    Document(
        page_content=(
            "BigCompany Inc. Vacation Policy: Full-time employees receive 20 days "
            "of paid time off (PTO) per year. PTO requests must be submitted at "
            "least 2 weeks in advance through the HR portal. Unused PTO can be "
            "carried over up to 5 days into the next year. Managers must approve "
            "all PTO requests within 3 business days."
        ),
        metadata={"source": "hr_handbook", "topic": "vacation"},
    ),
    Document(
        page_content=(
            "BigCompany Inc. Travel Reimbursement Policy: Employees traveling for "
            "business purposes can expense flights (economy class), hotels (up to "
            "$200/night), meals (up to $75/day), and ground transportation. All "
            "expenses must be submitted within 30 days of travel with receipts "
            "attached. Conference attendance requires pre-approval from department "
            "heads. The annual conference budget per employee is $3,000."
        ),
        metadata={"source": "finance_guidelines", "topic": "travel"},
    ),
    Document(
        page_content=(
            "BigCompany Inc. Code Review Policy: All code changes must be reviewed "
            "by at least one other engineer before merging. Pull requests should be "
            "reviewed within 24 hours. The reviewer must check for correctness, "
            "test coverage, security vulnerabilities, and adherence to the team "
            "style guide. Automated tests must pass before a PR can be merged."
        ),
        metadata={"source": "engineering_handbook", "topic": "code_review"},
    ),
    Document(
        page_content=(
            "BigCompany Inc. Deployment Security Requirements: All new services "
            "must pass a security review before deployment to production. Services "
            "must use HTTPS for all communications, implement authentication via "
            "the company SSO system, log all access attempts, and encrypt "
            "sensitive data at rest using AES-256. Database credentials must be "
            "stored in the company vault service, never in code or config files."
        ),
        metadata={"source": "engineering_handbook", "topic": "security"},
    ),
    Document(
        page_content=(
            "BigCompany Inc. Product Roadmap Q1 2026: The team is focused on three "
            "main initiatives: (1) Launching the mobile app v2.0 with offline "
            "support, (2) Migrating the payment system to the new provider by "
            "March, and (3) Implementing AI-powered search across all products. "
            "The mobile app launch is the highest priority."
        ),
        metadata={"source": "product_docs", "topic": "roadmap"},
    ),
    Document(
        page_content=(
            "BigCompany Inc. New Employee Onboarding: During your first week, you "
            "will receive your laptop and access credentials, complete mandatory "
            "security training, meet with your manager and team members, set up "
            "your development environment using the setup guide at "
            "docs.bigcompany.com/setup, and attend the company culture "
            "orientation session on Friday."
        ),
        metadata={"source": "onboarding_guide", "topic": "onboarding"},
    ),
]


# ============================================================
# 3. Local Embeddings, Vector Store, and Retriever
#    Groq provides chat models; this example uses local embeddings.
# ============================================================
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = InMemoryVectorStore.from_documents(
    documents=company_documents,
    embedding=embeddings,
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


# ============================================================
# 4. Groq Chat Model
# ============================================================
llm = ChatGroq(
    model=GROQ_MODEL,
    temperature=0,
    api_key=GROQ_API_KEY,
    max_retries=2,
    timeout=60,
)


# ============================================================
# 5. Document Grader
# ============================================================
class GradeDocuments(BaseModel):
    """Structured relevance grade for a retrieved document."""

    binary_score: Literal["yes", "no"] = Field(
        description="Whether the document is relevant to the user's question."
    )


grader_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You grade whether a retrieved company document is relevant to the "
            "user's question. Answer 'yes' if it contains information that helps "
            "answer the question; otherwise answer 'no'.",
        ),
        (
            "human",
            "Retrieved document:\n\n{document}\n\n"
            "User question: {question}",
        ),
    ]
)

retrieval_grader = grader_prompt | llm.with_structured_output(GradeDocuments)


# ============================================================
# 6. Question Rewriter
# ============================================================
rewrite_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Rewrite the user's question to improve retrieval from a company "
            "knowledge base. Preserve the original intent. Return only the "
            "rewritten question, with no explanation.",
        ),
        ("human", "{question}"),
    ]
)

question_rewriter = rewrite_prompt | llm | StrOutputParser()


# ============================================================
# 7. RAG Answer Generator
# ============================================================
rag_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant for BigCompany Inc. employees. Answer "
            "using ONLY the supplied company-document context. If the context "
            "does not contain the answer, clearly say that you could not find "
            "the answer in the available company documents. Do not invent "
            "company policies. Be concise and include the source name(s) when "
            "available.",
        ),
        (
            "human",
            "Context:\n{context}\n\nQuestion: {question}",
        ),
    ]
)

rag_chain = rag_prompt | llm | StrOutputParser()


# ============================================================
# 8. LangGraph State
# ============================================================
class GraphState(TypedDict, total=False):
    question: str
    documents: List[Document]
    generation: str
    needs_rewrite: str
    retry_count: int


# ============================================================
# 9. Graph Nodes
# ============================================================
def retrieve(state: GraphState) -> GraphState:
    """Retrieve documents relevant to the current question."""
    question = state["question"]
    documents = retriever.invoke(question)

    return {
        "documents": documents,
        "question": question,
    }


def grade_documents(state: GraphState) -> GraphState:
    """Grade retrieved documents and keep relevant ones."""
    question = state["question"]
    documents = state.get("documents", [])
    filtered_docs = []

    for doc in documents:
        score = retrieval_grader.invoke(
            {
                "question": question,
                "document": doc.page_content,
            }
        )

        if score.binary_score == "yes":
            filtered_docs.append(doc)

    needs_rewrite = "yes" if not filtered_docs else "no"

    return {
        "documents": filtered_docs,
        "question": question,
        "needs_rewrite": needs_rewrite,
    }


def generate(state: GraphState) -> GraphState:
    """Generate an answer using the relevant document context."""
    question = state["question"]
    documents = state.get("documents", [])

    context_parts = []
    for doc in documents:
        source = doc.metadata.get("source", "unknown source")
        context_parts.append(f"Source: {source}\n{doc.page_content}")

    context = "\n\n".join(context_parts)

    generation = rag_chain.invoke(
        {
            "context": context if context else "No relevant documents were found.",
            "question": question,
        }
    )

    return {
        "documents": documents,
        "question": question,
        "generation": generation,
    }


def transform_query(state: GraphState) -> GraphState:
    """Rewrite the question before retrying retrieval."""
    question = state["question"]
    better_question = question_rewriter.invoke({"question": question})

    return {
        "question": better_question,
        "retry_count": state.get("retry_count", 0) + 1,
    }


# ============================================================
# 10. Routing
# ============================================================
def decide_to_generate(
    state: GraphState,
) -> Literal["transform_query", "generate"]:
    """Retry retrieval with a rewritten query up to MAX_REWRITES times."""
    retry_count = state.get("retry_count", 0)

    if state.get("needs_rewrite") == "yes" and retry_count < MAX_REWRITES:
        return "transform_query"

    return "generate"


# ============================================================
# 11. Build and Compile the Graph
# ============================================================
workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)

workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges("grade_documents", decide_to_generate)
workflow.add_edge("transform_query", "retrieve")
workflow.add_edge("generate", END)

compiled_graph = workflow.compile()


# ============================================================
# 12. Run a Test Question
# ============================================================
if __name__ == "__main__":
    print("BigCompany Agentic RAG (Groq) is ready.")

    user_question = input("\nAsk a company question: ").strip()

    if not user_question:
        print("Please enter a question.")
    else:
        result = compiled_graph.invoke(
            {
                "question": user_question,
                "retry_count": 0,
            }
        )
        print("\nAssistant:")
        print(result.get("generation", "No answer was generated."))
