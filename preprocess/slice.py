import sys
sys.path.append("..")
from utils.args import config
from tqdm.auto import tqdm
import json
from pathlib import Path
import random
import pandas as pd
from copy import deepcopy
import logging

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s[line:%(lineno)d]- %(message)s"
logging.basicConfig(filename=config.log_file, level=logging.DEBUG, format=LOG_FORMAT)


class setEncoder(json.JSONEncoder):
    def default(self, obj):
        return list(obj)


def get_max_min_ts(sessions_path):
    max_ts = float('-inf')
    min_ts = float('inf')
    max_aid = int('-inf')
    min_aid = int('inf')
    with open(sessions_path) as f:
        for line in tqdm(f, desc="Finding max timestamp"):
            session = json.loads(line)
            max_ts = max(max_ts, session['events'][-1]['ts'])
            min_ts = min(min_ts, session['events'][0]['ts'])

            for event in session['events']:
                max_aid = max(max_aid, event['aid'])
                min_aid = min(min_aid, event['aid'])
    logging.info("In file " + sessions_path + ", max_aid:" +
                 str(max_aid) + " min_aid:" + str(min_aid) + " max_ts:" + str(max_ts) + " min_ts:" + str(min_ts))
    return max_ts, min_ts


def trim_session(session, max_ts):
    session['events'] = [event for event in session['events'] if event['ts'] < max_ts]
    return session


def ground_truth(events):
    prev_labels = {"clicks": None, "carts": set(), "orders": set()}

    for event in reversed(events):
        event["labels"] = {}

        for label in ['clicks', 'carts', 'orders']:
            if prev_labels[label]:
                if label != 'clicks':
                    event["labels"][label] = prev_labels[label].copy()
                else:
                    event["labels"][label] = prev_labels[label]

        if event["type"] == "clicks":
            prev_labels['clicks'] = event["aid"]
        if event["type"] == "carts":
            prev_labels['carts'].add(event["aid"])
        elif event["type"] == "orders":
            prev_labels['orders'].add(event["aid"])

    return events[:-1]


def split_events(events, split_idx=None):
    test_events = ground_truth(deepcopy(events))
    if not split_idx:
        split_idx = random.randint(1, len(test_events))
    test_events = test_events[:split_idx]
    labels = test_events[-1]['labels']
    for event in test_events:
        del event['labels']
    return test_events, labels

def filter_unknown_items(session_path, known_items):
    filtered_sessions = []
    with open(session_path) as f:
        for line in tqdm(f, desc="Filtering unknown items"):
            session = json.loads(line)
            session['events'] = [event for event in session['events'] if event['aid'] in known_items]
            if len(session['events']) >= 2:
                filtered_sessions.append(session)
    with open(session_path, 'w') as f:
        for session in filtered_sessions:
            f.write(json.dumps(session) + '\n')


def train_test_split(session_chunks, train_path, test_path, max_ts, test_days):
    split_millis = test_days * 24 * 60 * 60 * 1000
    split_ts = max_ts - split_millis
    logging.info("split_ts:" + str(split_ts))
    train_items = set()
    Path(train_path).parent.mkdir(parents=True, exist_ok=True)
    train_file = open(train_path, "w")
    Path(test_path).parent.mkdir(parents=True, exist_ok=True)
    test_file = open(test_path, "w")
    for chunk in tqdm(session_chunks, desc="Splitting sessions"):
        for _, session in chunk.iterrows():
            session = session.to_dict()
            if session['events'][0]['ts'] > split_ts:
                test_file.write(json.dumps(session) + "\n")
            else:
                session = trim_session(session, split_ts)
                if len(session['events']) >= 2:
                    train_items.update([event['aid'] for event in session['events']])
                    train_file.write(json.dumps(session) + "\n")
    train_file.close()
    test_file.close()
    # filter_unknown_items(test_path, train_items)


def create_kaggle_testset(sessions, sessions_output, labels_output):
    last_labels = []
    splitted_sessions = []

    for _, session in tqdm(sessions.iterrows(), desc="Creating trimmed testset", total=len(sessions)):
        session = session.to_dict()
        splitted_events, labels = split_events(session['events'])
        last_labels.append({'session': session['session'], 'labels': labels})
        splitted_sessions.append({'session': session['session'], 'events': splitted_events})

    with open(sessions_output, 'w') as f:
        for session in splitted_sessions:
            f.write(json.dumps(session) + '\n')

    with open(labels_output, 'w') as f:
        for label in last_labels:
            f.write(json.dumps(label, cls=setEncoder) + '\n')


def main(train_set, output_path, days, seed):
    random.seed(seed)
    max_ts, min_ts = get_max_min_ts(train_set)

    session_chunks = pd.read_json(train_set, lines=True, chunksize=100000)
    train_file = output_path + '/train_sessions.jsonl'
    test_file_full = output_path + '/test_sessions_full.jsonl'
    train_test_split(session_chunks, train_file, test_file_full, max_ts, days)

    test_sessions = pd.read_json(test_file_full, lines=True)
    test_sessions_file = output_path + '/test_sessions.jsonl'
    test_labels_file = output_path + '/test_labels.jsonl'
    create_kaggle_testset(test_sessions, test_sessions_file, test_labels_file)


if __name__ == "__main__":
    logging.info("input_file:" + str(config.input_file))
    logging.info("slice_path:" + str(config.slice_path))
    max_ts, min_ts = get_max_min_ts(config.test_file)
    main(config.input_file, config.slice_path, 7, config.seed)

