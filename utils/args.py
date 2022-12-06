# -*- encoding: utf-8 -*-
'''
@Time    :   2022/06/14 15:33:57
@Author  :   Chu Xioakai
@Contact :   xiaokaichu@gmail.com
'''
import argparse

parser = argparse.ArgumentParser(description='Pipeline commandline argument')

# parameters for dataset settings
parser.add_argument("--input_file", type=str, default='', help="input_file")
parser.add_argument("--slice_path", type=str, default='', help="slice_path")
parser.add_argument("--test_file", type=str, default='', help="test_file")
parser.add_argument("--output_file", type=str, default='', help="output_file")
parser.add_argument('--seed', type=int, default=42)


config = parser.parse_args()