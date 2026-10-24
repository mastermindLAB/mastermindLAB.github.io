"""Policy Q&A agent — Mosaic AI Agent Framework + LangChain retriever.

Defines a retrieval-augmented agent that answers policyholder and call-centre
questions strictly from indexed policy wordings. Authored as a ``mlflow.models``
``ChatAgent``-style module so it can be logged with code (``models-from-code``)
and deployed to Model Serving / the Agent Evaluation review app.
"""
from __future__ import annotations

import os

import mlflow
from databricks_langchain import (
    ChatDatabricks,
    DatabricksVectorSearch,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# ---- Configurable via env (set by the driver / serving environment) --------
CATALOG = os.environ.get("INSURANCE_CATALOG", "insurance_dev")
SCHEMA = os.environ.get("INSURANCE_SCHEMA", "lakehouse")
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")
INDEX_NAME = f"{CATALOG}.{SCHEMA}.policy_doc_index"
VS_ENDPOINT = "insurance-vs-endpoint"

SYSTEM_PROMPT = (
    "You are an insurance policy assistant. Answer ONLY from the provided "
    "policy context. If the answer is not in the context, say you cannot "
    "confirm it and advise contacting an agent. Never invent coverage, limits "
    "or exclusions. Quote the relevant clause when helpful."
)


def _format_docs(docs) -> str:
    return "\n\n".join(f"[{d.metadata.get('title', '?')}] {d.page_content}" for d in docs)


def build_chain():
    """Assemble the RAG chain (retriever -> prompt -> LLM -> string)."""
    retriever = DatabricksVectorSearch(
        endpoint=VS_ENDPOINT,
        index_name=INDEX_NAME,
        columns=["doc_id", "title", "content"],
    ).as_retriever(search_kwargs={"k": 4})

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT + "\n\nContext:\n{context}"),
            ("user", "{question}"),
        ]
    )
    llm = ChatDatabricks(endpoint=LLM_ENDPOINT, temperature=0.1)

    return (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


# Tells MLflow models-from-code which object is the servable model.
chain = build_chain()
mlflow.models.set_model(chain)
