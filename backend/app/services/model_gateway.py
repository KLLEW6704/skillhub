import base64

import httpx

from app.core.config import Settings


class ModelGatewayError(RuntimeError):
    pass


class DashScopeVisionModel:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.model_name = self.settings.dashscope_model

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_bytes: bytes,
        image_media_type: str,
    ) -> str:
        api_key = self.settings.dashscope_api_key
        if not api_key:
            raise ModelGatewayError("未配置 DASHSCOPE_API_KEY")
        encoded = base64.b64encode(image_bytes).decode("ascii")
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_media_type};base64,{encoded}"
                            },
                        },
                    ],
                },
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        endpoint = f"{self.settings.dashscope_base_url.rstrip('/')}/chat/completions"
        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                )
            if response.is_error:
                try:
                    detail = response.json().get("error", {}).get("message")
                except (ValueError, AttributeError):
                    detail = None
                raise ModelGatewayError(
                    f"模型服务返回 HTTP {response.status_code}"
                    + (f"：{str(detail)[:300]}" if detail else "")
                )
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ModelGatewayError("模型服务返回了无法识别的内容")
            return content
        except ModelGatewayError:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise ModelGatewayError(f"模型服务连接或响应失败：{type(exc).__name__}") from None
