import requests
import json
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
# 对使用ollama搭建的llama模型进行访问
def llama(model, inner,prompt,message):
    # 设置请求的URL
    url = "http://localhost:11434/api/generate"
    # 设置请求的头部信息
    headers = {
        "Content-Type": "application/json"
    }
    messages=inner+prompt+message+"Again, you just give the score, you don't have to say anything else.For example,Here is my scores"
    payload = {
        "model": model,
        "prompt": messages
    }

    # 发送POST请求
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    # 解析并合并JSON对象
    responses = response.text.split('\n')
    complete_response = ''
    for res in responses:
        if res.strip():  # 检查字符串是否为空
            try:
                json_res = json.loads(res)
                complete_response += json_res.get("response", "")
            except json.JSONDecodeError:
                print("Could not parse part of the response:", res)
    print(complete_response)
    return complete_response
