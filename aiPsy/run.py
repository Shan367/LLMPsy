import argparse
from utils import *
from generators import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    #输入你选择的模型 有llama还有chatgpt
    parser.add_argument('--model',  required=True, type=str, default='llama3',
                        help='The name of the model to test')
    #输入你选择的问卷
    parser.add_argument('--questionnaire', required=True, type=str,
                        help='Comma-separated list of questionnaires')
    #输入你选择的测验次数
    parser.add_argument('--test-count', required=True, type=int, default=1,
                        help='Numbers of runs for a same order. Defaults to one.')
    #输入你选择结果文件的名称
    parser.add_argument('--name-exp', type=str, default=None,
                        help='Name of this run. Is used to name the result files.')
    args = parser.parse_args()
    run_psychobench(args, generators)
