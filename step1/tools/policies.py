""" 회사 정책 관련 TOOL """
import re

import numpy as np
from openai import OpenAI
import requests
from langchain_core.tools import tool

from step1.settings import OPENAI_API_KEY

response = requests.get(
    "https://storage.googleapis.com/benchmarks-artifacts/travel-db/swiss_faq.md"
)
response.raise_for_status()
faq_text = response.text

docs = [{"page_content": txt} for txt in re.split(r"(?=\n##)", faq_text)]


class VectorStoreRetriever:
    def __init__(self, docs: list, vectors: list, oai_client):
        self._arr = np.array(vectors)
        self._docs = docs
        self._client = oai_client

    @classmethod
    def from_docs(cls, docs, openai_client):
        """
        RAG - 문서를 임배딩하여 Vectors에 저장 후 클래스 반환
        :param docs: 문서
        :param openai_client: openai_client
        :return: VectorStoreRetriever
        """
        embeddings = openai_client.embeddings.create(
            model="text-embedding-3-small", input=[doc["page_content"] for doc in docs]
        )
        vectors = [emb.embedding for emb in embeddings.data]
        return cls(docs, vectors, openai_client)

    def query(self, query: str, k: int = 5) -> list[dict]:
        embed = self._client.embeddings.create(
            model="text-embedding-3-small", input=[query]
        )

        # "@" is just a matrix multiplication in python
        scores = np.array(embed.data[0].embedding) @ self._arr.T
        top_k_idx = np.argpartition(scores, -k)[-k:]
        top_k_idx_sorted = top_k_idx[np.argsort(-scores[top_k_idx])]
        return [
            {**self._docs[idx], "similarity": scores[idx]} for idx in top_k_idx_sorted
        ]


openai_client = OpenAI(api_key=OPENAI_API_KEY)
retriever = VectorStoreRetriever.from_docs(docs, openai_client)  # VectorStoreRetriever 클래스 반환


@tool
def lookup_policy(query: str) -> str:
    """
    회사 정책 정보(문서)를 가져와 임배딩 + Query 조회
    :param query:
    :return: Page 콘텐츠
    """
    docs = retriever.query(query, k=2)
    return "\n\n".join([doc["page_content"] for doc in docs])
