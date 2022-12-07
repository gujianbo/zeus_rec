from copy import deepcopy
import numpy as np
import math


class Heap:
    def __init__(self, anchor, capacity):
        self.anchor = anchor
        self.capacity = capacity
        self.data = []

    def enter_item(self, item):
        if len(self.data) >= self.capacity and item[1] > self.data[0][1]:
            self.data[0] = item
            idx = 0
            while idx < len(self.data):
                left = 2 * idx + 1
                right = 2 * idx + 2
                if right < len(self.data):
                    if self.data[left][1] >= self.data[idx][1] and self.data[right][1] >= self.data[idx][1]:
                        break
                    elif self.data[left][1] >= self.data[right][1]:
                        tmp = self.data[right]
                        self.data[right] = self.data[idx]
                        self.data[idx] = tmp
                        idx = right
                    else:
                        tmp = self.data[left]
                        self.data[left] = self.data[idx]
                        self.data[idx] = tmp
                        idx = left
                elif left < len(self.data):
                    if self.data[left][1] >= self.data[idx][1]:
                        break
                    else:
                        tmp = self.data[left]
                        self.data[left] = self.data[idx]
                        self.data[idx] = tmp
                        idx = left
                else:
                    break

        elif len(self.data) < self.capacity:
            self.data.append(item)
            idx = len(self.data) - 1
            while idx >= 0:
                parent = math.floor((idx - 1) / 2)
                if self.data[idx][1] >= self.data[parent][1]:
                    break
                tmp = self.data[parent]
                self.data[parent] = self.data[idx]
                self.data[idx] = tmp
                idx = parent

    def top_items(self):
        top_item = []
        while len(self.data) > 0:
            top_item.insert(0, self.data[0])
            data_len = len(self.data)
            self.data[0] = deepcopy(self.data[data_len-1])
            self.data.pop()

            idx = 0
            while idx < len(self.data):
                left = 2 * idx + 1
                right = 2 * idx + 2
                if right < len(self.data):
                    if self.data[left][1] >= self.data[idx][1] and self.data[right][1] >= self.data[idx][1]:
                        break
                    elif self.data[left][1] >= self.data[right][1]:
                        tmp = self.data[right]
                        self.data[right] = self.data[idx]
                        self.data[idx] = tmp
                        idx = right
                    else:
                        tmp = self.data[left]
                        self.data[left] = self.data[idx]
                        self.data[idx] = tmp
                        idx = left
                elif left < len(self.data):
                    if self.data[left][1] >= self.data[idx][1]:
                        break
                    else:
                        tmp = self.data[left]
                        self.data[left] = self.data[idx]
                        self.data[idx] = tmp
                        idx = left
                else:
                    break
        return top_item


if __name__ == "__main__":
    h = Heap(1, 100)
    num_dict = dict()
    for i in range(200000):
        rand = int(np.random.normal(50, 20))
        h.enter_item([i, rand])
        num_dict[i] = rand
    sort_num_dict = sorted(num_dict.items(), key=lambda k: k[1], reverse=True)[:100]
    print(sort_num_dict)
    top_items = h.top_items()
    print(top_items)