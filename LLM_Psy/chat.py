from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import time
# 对openai的大模型进行访问的函数
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def chat(
        model,
        messages,  # [{"role": "system"/"user"/"assistant", "content": "Hello!", "name": "example"}]
        temperature=0,  # [0, 2]: Lower values -> more focused and deterministic; Higher values -> more random.
        n=1,  # Chat completion choices to generate for each input message.
        max_tokens=1024,  # The maximum number of tokens to generate in the chat completion.
        delay=1  # Seconds to sleep after each request.
):
    time.sleep(delay)
    client = OpenAI()
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        n=n
    )

    if n == 1:
        return completion['choices'][0]['message']['content']
    else:
        return [i['message']['content'] for i in completion['choices']]
