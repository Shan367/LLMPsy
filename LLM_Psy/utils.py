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

from example_generator import example_generator


def get_questionnaire(questionnaire_name):
    try:
        with open('questionnaires.json') as dataset:
            data = json.load(dataset)
    except FileNotFoundError:
        raise FileNotFoundError("The 'questionnaires.json' file does not exist.")

    # Matching by questionnaire_name in dataset
    questionnaire = None
    for item in data:
        if item["name"] == questionnaire_name:
            questionnaire = item

    if questionnaire is None:
        raise ValueError("Questionnaire not found.")

    return questionnaire

def generate_testfile(questionnaire, args):
    test_count = args.test_count
    do_shuffle = args.shuffle_count
    output_file = args.testing_file
    csv_output = []
    questions_list = questionnaire["questions"]  # get all questions

    for shuffle_count in range(do_shuffle + 1):
        question_indices = list(questions_list.keys())  # get the question indices

        # Shuffle the question indices
        if shuffle_count != 0:
            random.shuffle(question_indices)

        # Shuffle the questions order based on the shuffled indices
        questions = [f'{index}. {questions_list[question]}' for index, question in enumerate(question_indices, 1)]

        csv_output.append([f'Prompt: {questionnaire["prompt"]}'] + questions)
        csv_output.append([f'order-{shuffle_count}'] + question_indices)
        for count in range(test_count):
            csv_output.append([f'shuffle{shuffle_count}-test{count}'] + [''] * len(question_indices))

    csv_output = zip(*csv_output)

    # Write the csv file
    with open(output_file, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(csv_output)


def run(args,generator):
    questionaireList=['GAD-7']\
        if args.questionnaire=='ALL' else args.questionnaire.split(',')
    # Get questionnaire ,creat csv for questionaire
    for questionnaireName in questionaireList:
        questionnaire=get_questionnaire(questionnaireName)
        args.testing_file = f'results/{args.name_exp}-{questionnaire["name"]}.csv' if args.name_exp is not None else f'results/{args.model}-{questionnaire["name"]}.csv'
        args.results_file = f'results/{args.name_exp}-{questionnaire["name"]}.md' if args.name_exp is not None else f'results/{args.model}-{questionnaire["name"]}.md'
        args.figures_file = f'{args.name_exp}-{questionnaire["name"]}.png' if args.name_exp is not None else f'{args.model}-{questionnaire["name"]}.png'
        os.makedirs("results", exist_ok=True)
        os.makedirs("results/figures", exist_ok=True)

        # Generation
        if args.mode in ['generation', 'auto']:
            generate_testfile(questionnaire, args)
        if args.mode in ['testing', 'auto']:
            generator(questionnaire, args)