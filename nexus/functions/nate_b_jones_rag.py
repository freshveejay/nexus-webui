"""
title: Nate B. Jones Knowledge Base
author: baseshot
version: 1.0.0
description: RAG filter that searches Nate B. Jones transcript embeddings in Milvus and injects relevant context into the conversation.
category: filter
"""

import json
import requests
from typing import Optional
from pydantic import BaseModel, Field


class Filter:
    """
    Searches the nate_b_jones_transcripts collection in Milvus for relevant
    transcript chunks and injects them as system context before the LLM
    sees the user's message.
    """

    class Valves(BaseModel):
        enabled: bool = Field(default=True, description="Enable/disable RAG injection")
        milvus_url: str = Field(
            default="http://192.168.1.109:19530",
            description="Milvus REST API endpoint",
        )
        embedding_url: str = Field(
            default="http://192.168.1.109:8006/v1/embeddings",
            description="NVIDIA NIM embedding endpoint",
        )
        embedding_model: str = Field(
            default="nvidia/llama-3.2-nv-embedqa-1b-v2",
            description="Embedding model name",
        )
        collection_name: str = Field(
            default="nate_b_jones_transcripts",
            description="Milvus collection to search",
        )
        top_k: int = Field(default=5, description="Number of chunks to retrieve")
        score_threshold: float = Field(
            default=0.25, description="Minimum cosine similarity score"
        )
        max_context_chars: int = Field(
            default=6000, description="Maximum characters of context to inject"
        )

    def __init__(self):
        self.valves = self.Valves()

    def _embed_query(self, text: str) -> Optional[list[float]]:
        """Embed a query using the NVIDIA NIM embedding endpoint."""
        try:
            resp = requests.post(
                self.valves.embedding_url,
                json={
                    "input": [text],
                    "model": self.valves.embedding_model,
                    "input_type": "query",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            print(f"[NateBJones RAG] Embedding error: {e}")
        return None

    def _search_milvus(self, vector: list[float]) -> list[dict]:
        """Search Milvus for nearest transcript chunks."""
        try:
            resp = requests.post(
                f"{self.valves.milvus_url}/v2/vectordb/entities/search",
                json={
                    "collectionName": self.valves.collection_name,
                    "data": [vector],
                    "annsField": "vector",
                    "limit": self.valves.top_k,
                    "outputFields": [
                        "text",
                        "video_title",
                        "video_date",
                        "chunk_index",
                        "source_file",
                    ],
                },
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for hit in data.get("data", []):
                    score = hit.get("distance", 0)
                    if score >= self.valves.score_threshold:
                        results.append(
                            {
                                "text": hit.get("text", ""),
                                "video_title": hit.get("video_title", ""),
                                "video_date": hit.get("video_date", ""),
                                "chunk_index": hit.get("chunk_index", 0),
                                "source_file": hit.get("source_file", ""),
                                "score": round(score, 4),
                            }
                        )
                return results
        except Exception as e:
            print(f"[NateBJones RAG] Milvus search error: {e}")
        return []

    def _format_context(self, results: list[dict]) -> str:
        """Format search results into a context block for the LLM."""
        if not results:
            return ""

        lines = [
            "=== Nate B. Jones Knowledge Base ===",
            f"Retrieved {len(results)} relevant transcript excerpts.\n",
        ]
        char_count = 0
        for i, r in enumerate(results, 1):
            chunk = (
                f"[{i}] \"{r['video_title']}\" ({r['video_date']})\n"
                f"    Score: {r['score']} | Chunk #{r['chunk_index']}\n"
                f"    {r['text']}\n"
            )
            if char_count + len(chunk) > self.valves.max_context_chars:
                break
            lines.append(chunk)
            char_count += len(chunk)

        lines.append(
            "---\nWhen referencing this material, cite the video title and date. "
            "If the context doesn't answer the question, say so rather than guessing."
        )
        return "\n".join(lines)

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """
        Called before messages reach the LLM.
        Embeds the latest user message, searches Milvus, injects context.
        """
        if not self.valves.enabled:
            return body

        messages = body.get("messages", [])
        if not messages:
            return body

        # Get the latest user message
        user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    user_msg = content
                elif isinstance(content, list):
                    # Handle multimodal messages
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            user_msg = part.get("text", "")
                            break
                break

        if not user_msg or len(user_msg.strip()) < 3:
            return body

        # Embed and search
        vector = self._embed_query(user_msg)
        if not vector:
            return body

        results = self._search_milvus(vector)
        if not results:
            return body

        context = self._format_context(results)
        if not context:
            return body

        # Inject as a system message right before the user's message
        context_msg = {
            "role": "system",
            "content": context,
        }

        # Insert before the last user message
        insert_idx = len(messages) - 1
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                insert_idx = i
                break

        messages.insert(insert_idx, context_msg)
        body["messages"] = messages

        return body

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Called after LLM response. Pass-through."""
        return body
