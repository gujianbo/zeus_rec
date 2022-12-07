import sys
import os
import numpy as np


class Lossy_Counting():
    def __init__(self, anchor, window_capacity):
        self.anchor = anchor
        self.window_len = 0
        self.window_capacity = window_capacity
        self.real_num_dict = dict()
        self.num_dict = dict()

    def enter_num(self, num):
        self.real_num_dict.setdefault(num, 0)
        self.real_num_dict[num] += 1
        self.num_dict.setdefault(num, 0)
        self.num_dict[num] += 1
        self.window_len += 1
        if self.window_len >= self.window_capacity:
            self.flush()

    def flush(self):
        keys = list(self.real_num_dict.keys())
        for key in keys:
            if self.num_dict[key] <= 1:
                self.num_dict.pop(key)
                self.real_num_dict.pop(key)
            else:
                self.num_dict[key] -= 1
        self.window_len = 0

    def topk(self, tk):
        return sorted(self.real_num_dict.items(), key=lambda k: k[1], reverse=True)[:tk]

if __name__=="__main__":
    lc = Lossy_Counting(1, 100000)
    num_dict = dict()

    for i in range(1000000):
        rand = int(np.random.normal(50, 20))
        num_dict.setdefault(rand, 0)
        num_dict[rand] += 1
        lc.enter_num(rand)

    sort_num_dict = sorted(num_dict.items(), key=lambda k: k[1], reverse=True)[:100]
    sort_lc_dict = sorted(lc.real_num_dict.items(), key=lambda k: k[1], reverse=True)[:100]

    print(sort_num_dict)
    print(sort_lc_dict)
