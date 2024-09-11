import csv
import json
import os
import random
import scipy.stats as stats
from statistics import mean, stdev
import numpy as np
import matplotlib.pyplot as plt
import sys
import pandas as pd

def get_questionnaire(questionnaire_name):
    with open('questionnaires.json') as dataset:
            data = json.load(dataset)
    questionnaire = None
    for item in data:
        if item["name"] == questionnaire_name:
            questionnaire = item
            break
    if questionnaire is None:
        raise ValueError(f"Questionnaire '{questionnaire_name}' not found.")

    return questionnaire

def generate_testfile(questionnaire, args):
    test_count = args.test_count  # 获取测试次数，赋值给变量 test_count
    output_file = args.testing_file  # 获取输出文件的路径，赋值给变量 output_file
    csv_output = []  # 初始化一个空列表，用于存储 CSV 输出内容
    questions_list = questionnaire["questions"]  # 从问卷中获取所有问题，赋值给变量 questions_list

    # 获取按原始顺序排列的问题索引
    question_indices = list(questions_list.keys())

    # 创建带有索引的问题
    questions = [f'{index}. {questions_list[question]}' for index, question in enumerate(question_indices, 1)]

    # 将提示和问题添加到 csv_output 列表中
    csv_output.append([f'Prompt: {questionnaire["prompt"]}'] + questions)
    csv_output.append(['order-0'] + question_indices)

    for count in range(test_count):
        # 为每次测试添加空白行
        csv_output.append([f'test{count}'] + [''] * len(question_indices))

    # 转置 csv_output 列表，使其适合 CSV 格式
    csv_output = zip(*csv_output)

    # 写入 CSV 文件
    with open(output_file, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(csv_output)

def run_psychobench(args, generator):
    questionnaire_list = ['GAD'] \
        if args.questionnaire == 'ALL' else args.questionnaire.split(',')
    for questionnaire_name in questionnaire_list:
        # Get questionnaire
        questionnaire = get_questionnaire(questionnaire_name)  # 根据问卷名称从文件中获取问卷数据，并设置测试文件、结果文件和图表文件的路径。
        args.testing_file = f'results/{args.name_exp}-{questionnaire["name"]}.csv' if args.name_exp is not None else f'results/{args.model}-{questionnaire["name"]}.csv'  # 测试文件
        args.results_file = f'results/{args.name_exp}-{questionnaire["name"]}.md' if args.name_exp is not None else f'results/{args.model}-{questionnaire["name"]}.md'  # 结果文件
        args.figures_file = f'{args.name_exp}-{questionnaire["name"]}.png' if args.name_exp is not None else f'{args.model}-{questionnaire["name"]}.png'  # 绘制图标的文件

        os.makedirs("results", exist_ok=True)
        os.makedirs("results/figures", exist_ok=True)  # 创建两个文件夹储存

        # Generation
        generate_testfile(questionnaire, args)

        # Testing
        generator(questionnaire, args)

        # Analysis

