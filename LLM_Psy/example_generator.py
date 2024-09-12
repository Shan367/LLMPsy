import os
import pandas as pd
import time
from tqdm import tqdm
from chat import chat
from llama import llama


def convert_results(result, column_header):
    result = result.strip()  # Remove leading and trailing whitespace
    try:
        result_list = [int(element.strip()[-1]) for element in result.split('\n') if element.strip()]
    except:
        result_list = ["" for element in result.split('\n')]
        print(f"Unable to capture the responses on {column_header}.")

    return result_list


def example_generator(questionnaire, args):
    testing_file = args.testing_file
    model = args.model
    records_file = args.name_exp if args.name_exp is not None else model

    # Read the existing CSV file into a pandas DataFrame
    df = pd.read_csv(testing_file)

    # Find the columns whose headers start with "order"
    order_columns = [col for col in df.columns if col.startswith("order")]
    shuffle_count = 0
    insert_count = 0
    total_iterations = len(order_columns) * args.test_count

    with tqdm(total=total_iterations) as pbar:
        for i, header in enumerate(df.columns):
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
                                elif model in ['gpt-4o', 'gpt-4o-2024-05-13', 'gpt-4o-2024-08-06', 'gpt-4o-mini',
                                               'gpt-4o-mini-2024-07-18', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09',
                                               'gpt-4-turbo-preview', 'gpt-4-0125-preview', 'gpt-4-1106-preview',
                                               'gpt-4',
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
