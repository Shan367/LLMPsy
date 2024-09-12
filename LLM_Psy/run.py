""""本处代码的作用是获取参数以及运行其他处代码进行提问"""
import argparse
from utils import *
from example_generator import example_generator

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    #模型
    parser.add_argument('--model', required=True, type=str, default='llama3',
                        help='The name of the model to test')
    #问卷
    parser.add_argument('--questionnaire', required=True, type=str,
                        help='Comma-separated list of questionnaires')
    #洗牌次数
    parser.add_argument('--shuffle-count', required=True, type=int, default=0,
                        help='Numbers of different orders. If set zero, run only the original order. If set n > 0, run the original order along with its n permutations. Defaults to zero.')
    #测试次数
    parser.add_argument('--test-count', required=True, type=int, default=1,
                        help='Numbers of runs for a same order. Defaults to one.')
    #运行后的结果
    parser.add_argument('--name-exp', type=str, default=None,
                        help='Name of this run. Is used to name the result files.')
    #显著性水平
    parser.add_argument('--significance-level', type=float, default=0.01,
                        help='The significance level for testing the difference of means between human and LLM. Defaults to 0.01.')
    #调试步骤
    parser.add_argument('--mode', type=str, default='auto',
                        help='For debugging.')


    args = parser.parse_args()

    run(args, example_generator)