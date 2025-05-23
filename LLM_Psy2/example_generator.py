from numpy.ma.core import inner
from openai import OpenAI, api_key
import os
import pandas as pd
from tqdm import tqdm
from chat import *
from llama import *
from Qwen import *
from twisted.words.protocols.jabber.jstrports import client

'''
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def completion(
        model,  # text-davinci-003, text-davinci-002, text-curie-001, text-babbage-001, text-ada-001
        prompt,
        # The prompt(s) to generate completions for, encoded as a string, array of strings, array of tokens, or array of token arrays.
        temperature=0,  # [0, 2]: Lower values -> more focused and deterministic; Higher values -> more random.
        n=1,  # Completions to generate for each prompt.
        max_tokens=1024,  # The maximum number of tokens to generate in the chat completion.
        delay=1  # Seconds to sleep after each request.
):
    time.sleep(delay)

    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        temperature=temperature,
        n=n,
        max_tokens=max_tokens
    )

    if n == 1:
        return response['choices'][0]['text']
    else:
        response = response['choices']
        response.sort(key=lambda x: x['index'])
        return [i['text'] for i in response['choices']]

'''
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
            if header in order_columns:
                # Find the index of the previous column
                questions_column_index = i - 1
                shuffle_count += 1

                # Retrieve the column data as a string
                questions_list = df.iloc[:, questions_column_index].astype(str)
                separated_questions = [questions_list[i:i + 30] for i in range(0, len(questions_list), 30)]
                questions_list = ['\n'.join([f"{i + 1}.{q.split('.')[1]}" for i, q in enumerate(questions)]) for
                                  j, questions in enumerate(separated_questions)]

                for k in range(args.test_count):

                    df = pd.read_csv(testing_file)

                    # Insert the updated column into the DataFrame with a unique identifier in the header
                    column_header = f'shuffle{shuffle_count - 1}-test{k}'

                    while (True):
                        result_string_list = []
                        previous_records = []

                        for questions_string in questions_list:
                            result = ''
                            if model in ['llama3', 'llama3.1', 'llama2']:
                                inputs = previous_records + [
                                    {"role": "system", "content": questionnaire["inner_setting"]},
                                    {"role": "user", "content": questionnaire["prompt"] + '\n' + questions_string}
                                ]

                                result=llama(model, questionnaire["inner_setting"],questionnaire["prompt"],questions_string)
                                previous_records.append(
                                    {"role": "user", "content": questionnaire["prompt"] + '\n' + questions_string})
                                previous_records.append({"role": "assistant", "content": result})
                                print("???")
                            elif model in [ 'gpt-4o', 'gpt-4o-2024-05-13', 'gpt-4o-2024-08-06', 'gpt-4o-mini',
                                    'gpt-4o-mini-2024-07-18', 'gpt-4-turbo', 'gpt-4-turbo-2024-04-09',
                                    'gpt-4-turbo-preview', 'gpt-4-0125-preview', 'gpt-4-1106-preview', 'gpt-4',
                                    'gpt-4-0613', 'gpt-4-0314', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo',
                                    'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-instruct']:
                                inputs = previous_records + [
                                    {"role": "system", "content": questionnaire["inner_setting"]},
                                    {"role": "user", "content": questionnaire["prompt"] + '\n' + questions_string}
                                ]
                                result = chat(model, inputs)
                                previous_records.append(
                                    {"role": "user", "content": questionnaire["prompt"] + '\n' + questions_string})
                                previous_records.append({"role": "assistant", "content": result})
                            elif model in ['qwen-max','qwen-plus','qwen-turbo']:
                                inputs = previous_records + [
                                    {"role": "system", "content": questionnaire["inner_setting"]},
                                    {"role": "user", "content": questionnaire["prompt"] + '\n' + questions_string}
                                ]
                                result = Qwen(inputs)
                                previous_records.append(
                                    {"role": "user", "content": questionnaire["prompt"] + '\n' + questions_string})
                                previous_records.append({"role": "assistant", "content": result})

                            else:
                                raise ValueError("The model is not supported or does not exist.")

                            result_string_list.append(result.strip())

                            # Write the prompts and results to the file
                            os.makedirs("prompts", exist_ok=True)
                            os.makedirs("responses", exist_ok=True)

                            with open(f'prompts/{records_file}-{questionnaire["name"]}-shuffle{shuffle_count - 1}.txt',
                                      "a") as file:
                                file.write(f'{inputs}\n====\n')
                            with open(
                                    f'responses/{records_file}-{questionnaire["name"]}-shuffle{shuffle_count - 1}.txt',
                                    "a") as file:
                                file.write(f'{result}\n====\n')

                        result_string = '\n'.join(result_string_list)

                        result_list = convert_results(result_string, column_header)

                        try:
                            if column_header in df.columns:
                                df[column_header] = result_list
                            else:
                                df.insert(i + insert_count + 1, column_header, result_list)
                                insert_count += 1
                            break
                        except:
                            print(f"Unable to capture the responses on {column_header}.")

                    # Write the updated DataFrame back to the CSV file
                    df.to_csv(testing_file, index=False)

                    pbar.update(1)
