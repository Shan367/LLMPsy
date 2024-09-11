from openai import OpenAI
import os
import pandas as pd
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import time
from tqdm import tqdm
import requests
import json


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


# 对使用ollama搭建的llama模型进行访问
def llama(model, messages):
    # 设置请求的URL
    url = "http://localhost:11434/api/generate"
    # 设置请求的头部信息
    headers = {
        "Content-Type": "application/json"
    }
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


def convert_results(result, column_header):
    result = result.strip()  # Remove leading and trailing whitespace
    result_list = []
    try:
        # 逐行处理，并确保只处理符合预期的行格式
        for element in result.split('\n'):
            element = element.strip()
            if element and element[-1].isdigit():  # 检查最后一个字符是否是数字
                result_list.append(int(element[-1]))
            else:
                result_list.append("")  # 如果格式不符合预期，添加空白
                print(f"Warning: Unexpected format in '{element}' for column '{column_header}'")
    except Exception as e:
        print(f"Error parsing results for column '{column_header}': {e}")
        result_list = ["" for element in result.split('\n')]  # 出现错误时返回空白列表

    return result_list


def generators(questionnaire, args):
    print("Starting generators function...")
    testing_file = args.testing_file
    model = args.model
    records_file = args.name_exp if args.name_exp is not None else model
    df = pd.read_csv(testing_file)
    insert_count = 0
    total_iterations = args.test_count

    def convert_results(result_string, column_header):
        results = [line.strip() for line in result_string.split('\n') if line.strip()]
        print(f"Converted results: {results}")  # 输出转换后的结果列表以供调试
        return results

    print("Starting the script...")

    with tqdm(total=total_iterations) as pbar:
        for i, header in enumerate(df.columns):
            print(f"Checking column: {header}")
            if "order" in header or "test" in header:
                print(f"Processing questions in column: {header}")
                questions_list = df.iloc[:, i].dropna().astype(str).tolist()
                print(f"Questions list: {questions_list}")
                for k in range(args.test_count):
                    df = pd.read_csv(testing_file)
                    column_header = f'test{k}'
                    insert_count = 0  # 初始化插入计数

                    while True:
                        print(f"Starting loop for test {k}")
                        result_string_list = []
                        previous_records = []
                        inputs = []  # 初始化inputs

                        for questions_string in questions_list:
                            print(f"Processing question: {questions_string}")
                            result = ''
                            try:
                                # 从 questionnaire 中提取问题文本
                                question_text = questionnaire["questions"].get(questions_string, "")
                                if not question_text:
                                    print(f"Question text for {questions_string} not found! Using default text.")
                                    question_text = f"Default question text for {questions_string}"  # 使用默认文本

                                # 组合完整的问题内容
                                question = (f"{questionnaire['inner_setting']}\n"
                                            f"{questionnaire['prompt']}\n"
                                            f"Question {questions_string}: {question_text}")

                                print(f"Sending question to model: {question}")
                                # 根据模型类型使用不同的访问方式
                                if model in ['llama3', 'llama3.1', 'llama2']:
                                    result = llama(model, question)
                                elif model in [ 'gpt-4o', 'gpt-4o-2024-05-13', 'gpt-4o-2024-08-06', 'gpt-4o-mini',
                                    'gpt-4o-mini-2024-07-18', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09',
                                    'gpt-4-turbo-preview', 'gpt-4-0125-preview', 'gpt-4-1106-preview', 'gpt-4',
                                    'gpt-4-0613', 'gpt-4-0314', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo',
                                    'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-instruct']:
                                    inputs = previous_records + [
                                        {"role": "system", "content": questionnaire["inner_setting"]},
                                        {"role": "user", "content": questionnaire["prompt"] + '\n' + question_text}
                                    ]
                                    result = chat(model, inputs)
                                    previous_records.append({"role": "user", "content": question_text})
                                    previous_records.append({"role": "assistant", "content": result})
                                    print(f"Model result: {result}")
                                else:
                                     print("There is not this result")
                            except Exception as e:
                                print(f"An error occurred during model interaction: {e}")
                                continue  # 继续处理下一个问题

                            # 将结果添加到列表中
                            result_string_list.append(result.strip())
                            inputs.append(question)

                        try:
                            os.makedirs("prompts", exist_ok=True)
                            os.makedirs("responses", exist_ok=True)

                            with open(f'prompts/{records_file}-{questionnaire["name"]}-test{k}.txt', "a") as file:
                                file.write(f'{inputs}\n====\n')

                            with open(f'responses/{records_file}-{questionnaire["name"]}-test{k}.txt', "a") as file:
                                file.write(f'{result}\n====\n')

                            result_string = '\n'.join(result_string_list)
                            result_list = convert_results(result_string, column_header)

                            # 确保结果列表长度与数据帧的行数匹配
                            if len(result_list) != len(df):
                                print(
                                    f"Warning: Length of result list ({len(result_list)}) does not match DataFrame rows ({len(df)}). Skipping.")
                                break

                            # 输出调试信息
                            print(f"Attempting to write the following result list to {column_header}: {result_list}")

                            if column_header in df.columns:
                                df[column_header] = result_list
                            else:
                                df.insert(i + insert_count + 1, column_header, result_list)
                                insert_count += 1

                            print(f"Successfully processed test {k} for {header}.")
                            break
                        except Exception as e:
                            print(f"An error occurred while processing the results: {e}")
                            break
                    pbar.update(1)

    print("Script finished.")

    # 输出 DataFrame 以确认写入
    print(f"Final DataFrame:\n{df.head()}")

    # 将修改后的 DataFrame 保存回 CSV 文件
    df.to_csv(testing_file, index=False)
