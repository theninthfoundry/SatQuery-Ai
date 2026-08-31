"""Unified LLM synthesis client for SatQuery AI.

Supports multi-provider execution:
- 'local': 100% offline deterministic rule & template synthesizer (Default, ₹0, Zero-VRAM/GeoChat)
- 'openai': Optional OpenAI GPT-4o / GPT-4o-mini synthesis grounded in deterministic geospatial facts
- 'gemini': Optional Google Gemini 1.5/2.0 Flash synthesis
- 'ollama': Local self-hosted Ollama LLM (e.g., Llama-3, Mistral, Gemma)
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

SYSTEM_GROUNDING_PROMPT = """You are SatQuery AI, an expert Earth Observation and Remote Sensing Vision-Language Assistant.
You strictly adhere to the 'Orchestrator vs. Calculator' principle:
- All numbers, area measurements (m² and ha), bounding coordinates, and confidence percentages are computed by deterministic geospatial tools (GDAL, Shapely, PyProj, ChangeNet).
- DO NOT invent, hallucinate, or modify any coordinates, areas, or percentages.
- Explain the scientific significance clearly, concisely, and professionally for defense and disaster response analysts."""


class UnifiedLLMClient:
    """Multi-provider LLM connector with automatic offline failover."""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "local").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def synthesize(
        self,
        query: str,
        task_intent: str,
        pipeline_result: Dict[str, Any],
        default_answer: str,
    ) -> str:
        """Synthesize final user-facing response using the configured LLM provider."""
        # 1. Check if external LLM is configured and available
        if self.openai_api_key and (self.provider == "openai" or self.provider == "auto"):
            res = self._call_openai(query, task_intent, pipeline_result)
            if res:
                return res

        if self.gemini_api_key and (self.provider == "gemini" or self.provider == "auto"):
            res = self._call_gemini(query, task_intent, pipeline_result)
            if res:
                return res

        if self.provider == "ollama":
            res = self._call_ollama(query, task_intent, pipeline_result)
            if res:
                return res

        # 2. Pure local deterministic fallback (100% reliable)
        return default_answer

    def _call_openai(self, query: str, task_intent: str, pipeline_result: Dict[str, Any]) -> Optional[str]:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}",
            }
            prompt_content = f"User Question: {query}\nTask Intent: {task_intent}\nDeterministic Pipeline Facts:\n{json.dumps(pipeline_result, default=str)}\n\nSynthesize an expert remote sensing answer in 2-3 concise sentences based ONLY on the above facts."

            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_GROUNDING_PROMPT},
                    {"role": "user", "content": prompt_content},
                ],
                "temperature": 0.2,
                "max_tokens": 250,
            }

            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["choices"][0]["message"]["content"].strip()
        except Exception:
            return None

    def _call_gemini(self, query: str, task_intent: str, pipeline_result: Dict[str, Any]) -> Optional[str]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
            headers = {"Content-Type": "application/json"}
            prompt_content = f"{SYSTEM_GROUNDING_PROMPT}\n\nUser Question: {query}\nTask Intent: {task_intent}\nFacts:\n{json.dumps(pipeline_result, default=str)}\n\nSynthesize a concise 2-sentence remote sensing answer."

            payload = {
                "contents": [{"parts": [{"text": prompt_content}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 250},
            }

            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            return None

    def _call_ollama(self, query: str, task_intent: str, pipeline_result: Dict[str, Any]) -> Optional[str]:
        try:
            url = f"{self.ollama_host}/api/generate"
            headers = {"Content-Type": "application/json"}
            prompt_content = f"{SYSTEM_GROUNDING_PROMPT}\n\nQuestion: {query}\nTask: {task_intent}\nFacts:\n{json.dumps(pipeline_result, default=str)}\n\nAnswer:"

            payload = {
                "model": "llama3",
                "prompt": prompt_content,
                "stream": False,
            }

            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=4) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data.get("response", "").strip()
        except Exception:
            return None


llm_client = UnifiedLLMClient()
