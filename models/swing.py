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
from itertools import combinations

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s[line:%(lineno)d]- %(message)s"
logging.basicConfig(filename=config.log_file, level=logging.DEBUG, format=LOG_FORMAT)


def gen_item_pair(input_file):
    # session_chunks = pd.read_json(input_file, lines=True, chunksize=100000)
    session_item = dict()
    item_session = dict()
    item_pairs = set()
    with open(input_file, "r") as f:
        for line in tqdm(f, desc="gen_item_pair"):
            session = json.loads(line.strip())
            session_id = session['session']
            click_aid = set([event['aid'] for event in session['events'] if event["type"] == "clicks"])
            # print(click_aid)
            session_item[session_id] = click_aid
            for aid in click_aid:
                item_session.setdefault(aid, set())
                item_session[aid].add(session_id)
            pair_list = list(combinations(click_aid, 2))
            for pair in pair_list:
                if pair[0] > pair[1]:
                    pair_str = str(pair[0]) + "," + str(pair[1])
                elif pair[0] < pair[1]:
                    pair_str = str(pair[1]) + "," + str(pair[0])
                else:
                    continue
                item_pairs.add(pair_str)
    return item_pairs, session_item, item_session


def calc_simlarity(item_pairs, session_item, item_session, alpha=1.0, session_num_threhold=200):
    item_sim_dict = dict()
    logging.info("item pairs length：{}".format(len(item_pairs)))

    for pair_str in tqdm(item_pairs, desc="calculate similarities"):
        item_i, item_j = pair_str.split(",")
        item_i = int(item_i)
        item_j = int(item_j)
        common_sessions = item_session[item_i] & item_session[item_j]
        # 采个样，防止太多，撑爆内存
        if len(common_sessions) > session_num_threhold:
            common_sessions = random.sample(common_sessions, session_num_threhold)
        session_pairs = list(combinations(common_sessions, 2))
        result = 0.0
        for (user_u, user_v) in session_pairs:
            result += 1 / (alpha + list(session_item[user_u] & session_item[user_v]).__len__())
        item_sim_dict.setdefault(item_i, dict())
        item_sim_dict[item_i][item_j] = result
        item_sim_dict.setdefault(item_j, dict())
        item_sim_dict[item_j][item_i] = result
    logging.info("Calculate similarity finished!")
    return item_sim_dict


def output_sim_file(item_sim_dict, out_path, top_k=100):
    fd = open(out_path, "w")
    for item, sim_items in item_sim_dict.items():
        sim_score = sorted(sim_items.items(), key=lambda k: k[1], reverse=True)[:top_k]
        for (item_j, score) in sim_score:
            fd.write(str(item) + "\t" + str(item_j) + "\t" + str(score) + "\n")
    fd.close()


def main():
    item_pairs, session_item, item_session = gen_item_pair(config.input_file)
    item_sim_dict = calc_simlarity(item_pairs, session_item, item_session)
    del session_item, item_session
    output_sim_file(item_sim_dict, config.output_file)


if __name__ == "__main__":
    logging.info("input_file:" + config.input_file)
    logging.info("output_file:" + config.output_file)
    main()