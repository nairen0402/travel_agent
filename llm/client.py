# llm/client.py

import requests
from requests.exceptions import ReadTimeout, RequestException

BASE_URL = "https://api-gateway.netdb.csie.ncku.edu.tw"
API_KEY = "310a74d867f37d99be699d13858837f61ab69457c6cefabb79d99d24dfade99b"  # ⚠️ 之後記得用環境變數

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Connection": "close"
}


def call_llm(prompt: str, model: str = "gpt-oss:20b") -> str: #change llm
    url = f"{BASE_URL}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        resp = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            timeout=180 # 建議設定具體秒數，避免無限等待
        )
        resp.raise_for_status()

    except ReadTimeout:
        return "⚠️ LLM 回應逾時，請稍後再試（模型忙碌）"

    except RequestException as e:
        return f"❌ LLM 連線失敗：{e}"

    return resp.json().get("response", "").strip()