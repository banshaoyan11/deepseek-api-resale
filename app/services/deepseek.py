# app/services/deepseek.py
import httpx
from typing import Dict, Any, Optional
import tiktoken
from app.config import settings

class DeepSeekService:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL

    async def chat_completions(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy chat completions request to DeepSeek API"""
        request_data = {**request_data, "stream": False, "thinking": {"type": "disabled"}}
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=request_data
            )

            if response.status_code != 200:
                raise Exception(f"DeepSeek API error: {response.status_code} - {response.text}")

            return response.json()

    async def anthropic_messages(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy Anthropic-format messages request to DeepSeek API"""
        request_data = {**request_data, "stream": False}
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = await client.post(
                f"{self.base_url}/anthropic/v1/messages",
                headers=headers,
                json=request_data
            )

            if response.status_code != 200:
                raise Exception(f"DeepSeek API error: {response.status_code} - {response.text}")

            return response.json()

    def estimate_token_count(self, text: str, model: str = "deepseek-v4-flash") -> int:
        """Estimate token count for input text"""
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
            return len(encoding.encode(text))
        except:
            return len(text) // 4

    def estimate_anthropic_tokens(self, request_data: Dict[str, Any]) -> int:
        """Estimate token count for Anthropic-format messages"""
        total_text = ""
        system = request_data.get("system", "")
        if isinstance(system, str):
            total_text += system
        elif isinstance(system, list):
            for block in system:
                if isinstance(block, dict):
                    total_text += str(block.get("text", ""))

        messages = request_data.get("messages", [])
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get("content", "")
                if isinstance(content, str):
                    total_text += content
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            total_text += str(block.get("text", ""))

        return self.estimate_token_count(total_text)

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD"""
        input_cost = (input_tokens / 1_000_000) * settings.API_PRICING_INPUT
        output_cost = (output_tokens / 1_000_000) * settings.API_PRICING_OUTPUT
        return input_cost + output_cost

deepseek_service = DeepSeekService()
