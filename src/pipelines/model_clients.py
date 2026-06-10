import os
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class ModelResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class BaseModelClient:
    uses_real_generation = False

    def generate(self, prompt: str) -> ModelResponse:
        raise NotImplementedError


class MockClient(BaseModelClient):
    def __init__(self, name: str):
        self.name = name

    def generate(self, prompt: str) -> ModelResponse:
        words = [word.strip(".,:;()").lower() for word in prompt.split()]
        keywords = []
        for word in words:
            if len(word) > 4 and word not in keywords:
                keywords.append(word)
        text = "mock_output: " + ";".join(keywords[:12])
        return ModelResponse(text=text, input_tokens=len(words), output_tokens=len(text.split()))


class OpenAIClient(BaseModelClient):
    uses_real_generation = True

    def __init__(self, model_id: str):
        self.model_id = model_id

    def generate(self, prompt: str) -> ModelResponse:
        if not os.getenv("OPENAI_API_KEY"):
            return ModelResponse(
                text="[ERRO: OPENAI_API_KEY ausente. Execute com mock ou configure .env.]",
                input_tokens=len(prompt.split()),
                output_tokens=0,
            )
        from openai import OpenAI

        client = OpenAI()
        response = client.responses.create(model=self.model_id, input=prompt)
        text = response.output_text
        usage = getattr(response, "usage", None)
        return ModelResponse(
            text=text,
            input_tokens=getattr(usage, "input_tokens", len(prompt.split())) if usage else len(prompt.split()),
            output_tokens=getattr(usage, "output_tokens", len(text.split())) if usage else len(text.split()),
        )


class OllamaClient(BaseModelClient):
    uses_real_generation = True

    def __init__(self, model_id: str, base_url: str | None = None):
        self.model_id = model_id
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")

    def generate(self, prompt: str) -> ModelResponse:
        payload = {
            "model": self.model_id,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "seed": 42},
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            return ModelResponse(
                text=f"[ERRO: Ollama indisponivel para {self.model_id}: {exc}]",
                input_tokens=len(prompt.split()),
                output_tokens=0,
            )
        text = body.get("response", "")
        return ModelResponse(text=text, input_tokens=len(prompt.split()), output_tokens=len(text.split()))


class OpenAICompatibleClient(BaseModelClient):
    uses_real_generation = True

    def __init__(self, model: dict):
        self.model_id = model.get("model_id", "")
        self.base_url = model.get("base_url") or os.getenv(model.get("base_url_env", "OPENAI_COMPATIBLE_BASE_URL"), "")
        self.api_key = os.getenv(model.get("api_key_env", "OPENAI_COMPATIBLE_API_KEY"), "")
        self.request_delay_seconds = float(model.get("request_delay_seconds") or 0)
        self.max_retries = int(model.get("max_retries") or 4)
        self.timeout_seconds = int(model.get("timeout_seconds") or 180)

    def generate(self, prompt: str) -> ModelResponse:
        if not self.base_url or not self.api_key:
            return ModelResponse(
                text=f"[ERRO: base_url/api_key ausentes para modelo compativel OpenAI {self.model_id}]",
                input_tokens=len(prompt.split()),
                output_tokens=0,
            )
        payload = {"model": self.model_id, "messages": [{"role": "user", "content": prompt}], "temperature": 0}
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        last_error = None
        for attempt in range(self.max_retries + 1):
            if self.request_delay_seconds:
                time.sleep(self.request_delay_seconds)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    body = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code != 429 or attempt >= self.max_retries:
                    return ModelResponse(
                        text=f"[ERRO: provedor compativel OpenAI indisponivel para {self.model_id}: {exc}]",
                        input_tokens=len(prompt.split()),
                        output_tokens=0,
                    )
                retry_after = exc.headers.get("Retry-After")
                wait_seconds = float(retry_after) if retry_after and retry_after.isdigit() else min(60, 2 ** attempt * 5)
                time.sleep(wait_seconds)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    return ModelResponse(
                        text=f"[ERRO: provedor compativel OpenAI indisponivel para {self.model_id}: {last_error}]",
                        input_tokens=len(prompt.split()),
                        output_tokens=0,
                    )
                time.sleep(min(30, 2 ** attempt * 3))
        text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = body.get("usage", {})
        return ModelResponse(
            text=text,
            input_tokens=usage.get("prompt_tokens", len(prompt.split())),
            output_tokens=usage.get("completion_tokens", len(text.split())),
        )


def build_client(model: dict) -> BaseModelClient:
    provider = model.get("provider")
    if provider == "openai":
        return OpenAIClient(model.get("model_id", ""))
    if provider == "ollama":
        return OllamaClient(model.get("model_id", ""), model.get("base_url"))
    if provider == "openai_compatible":
        return OpenAICompatibleClient(model)
    return MockClient(model.get("name", "mock"))
