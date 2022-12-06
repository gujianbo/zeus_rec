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
parser.add_argument("--output_file", type=str, default='', help="output_file")


config = parser.parse_args()