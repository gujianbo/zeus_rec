import os
from utils.args import config
import tqdm
import json


def get_max_ts(sessions_path):
    max_ts = float('-inf')
    min_ts = float('inf')
    with open(sessions_path) as f:
        for line in tqdm(f, desc="Finding max timestamp"):
            session = json.loads(line)
            max_ts = max(max_ts, session['events'][-1]['ts'])
            min_ts = min(min_ts, session['events'][0]['ts'])
    return max_ts, min_ts

if __name__ == "__main__":
    print("input_file", config.input_file)
    print("output_file", config.output_file)
    max_ts, min_ts = get_max_ts(config.input_file)
    print(max_ts, min_ts)
