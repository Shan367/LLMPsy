from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import time
import os
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def Qwen(
        model,
        messages,  # [{"role": "system"/"user"/"assistant", "content": "Hello!", "name": "example"}]
        temperature=0,  # [0, 2]: Lower values -> more focused and deterministic; Higher values -> more random.
        n=1,  # Chat completion choices to generate for each input message.
        max_tokens=1024,  # The maximum number of tokens to generate in the chat completion.
        delay=1  # Seconds to sleep after each request.
):
    time.sleep(delay)
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),  # 如果您没有配置环境变量，请在此处用您的API Key进行替换
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 填写DashScope服务的base_url
    )
    response= client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        n=n,
        max_tokens=max_tokens
        )
    if n == 1:
        return response.choices[0].message.content
    else:
        return [i.message.content for i in response.choices]