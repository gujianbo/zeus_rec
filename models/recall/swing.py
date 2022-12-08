import os
import sys
sys.path.append("../..")
from utils.args import config
from tqdm.auto import tqdm
import json
from pathlib import Path
import random
import pandas as pd
from copy import deepcopy
from utils.heap import Heap
import logging
from itertools import combinations
import hashlib

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s[line:%(lineno)d]- %(message)s"
logging.basicConfig(filename=config.log_file, level=logging.DEBUG, format=LOG_FORMAT)


def gen_item_pair(input_file, output_file, debug=0):
    session_item = dict()
    item_session = dict()
    pair_path = Path(output_file).parent.joinpath("tmp")
    pair_path.mkdir(parents=True, exist_ok=True)
    fdout = []
    for i in range(10):
        fd = open(str(pair_path)+"/pair_"+str(i), "w")
        fdout.append(fd)
    idx = 0
    with open(input_file, "r") as f:
        for line in tqdm(f, desc="gen_item_pair"):
            session = json.loads(line.strip())
            session_id = session['session']
            click_aid = set([event['aid'] for event in session['events'] if event["type"] == "clicks"])
            # print(click_aid)
            if len(click_aid) <= 3:
                continue
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
                hash_code = int(hashlib.md5((pair_str + str(config.seed)).encode('utf8')).hexdigest()[0:10], 16) % 10
                fdout[hash_code].write(pair_str+"\n")
            if debug == 1:
                idx += 1
                if idx >= 50000:
                    break
    for fd in fdout:
        fd.close()
    return session_item, item_session


def calc_simlarity(session_item, item_session, output_file, alpha=1.0, session_num_threhold=5000):
    item_sim_dict = dict()
    pair_path = Path(output_file).parent.joinpath("tmp")

    for i in range(10):
        pair_file = str(pair_path) + "/pair_" + str(i) + ".uniq"
        logging.info("calc_simlarity file " + pair_file)
        with open(pair_file, "r") as f:
            for item_pair in tqdm(f, desc="calc_simlarity:"+pair_file):
                pair_str = item_pair.strip()
                item_i, item_j = pair_str.split(",")
                item_i = int(item_i)
                item_j = int(item_j)
                common_sessions = item_session[item_i] & item_session[item_j]
                if len(common_sessions) <= 1:
                    continue
                # 采个样，防止太多，撑爆内存
                elif len(common_sessions) > session_num_threhold:
                    common_sessions = random.sample(common_sessions, session_num_threhold)
                session_pairs = list(combinations(common_sessions, 2))
                result = 0.0
                for (user_u, user_v) in session_pairs:
                    result += 1 / (alpha + len(session_item[user_u] & session_item[user_v]))
                item_sim_dict.setdefault(item_i, Heap(item_i, 100))
                item_sim_dict[item_i].enter_item([item_j, result])
                item_sim_dict.setdefault(item_j, Heap(item_j, 100))
                item_sim_dict[item_j].enter_item([item_i, result])
        logging.info("calc_simlarity file " + pair_file + " done!")
    logging.info("Calculate similarity finished!")
    return item_sim_dict


def uniq_pair(input_file):
    logging.info("start uniq pair file")
    for i in range(10):
        pair_path = Path(input_file).parent.joinpath("tmp")
        pair_file = str(pair_path)+"/pair_"+str(i)
        logging.info("To uniq file:" + pair_file)
        os.system("sort " + pair_file + " | uniq > " + pair_file+".uniq")
        logging.info("Uniq file:" + pair_file + " done!")
    logging.info("Uniq pair file finished!")


def output_sim_file(item_sim_dict, out_path):
    fd = open(out_path, "w")
    for item, sim_items in item_sim_dict.items():
        sim_score = sim_items.top_items()
        for (item_j, score) in sim_score:
            fd.write(str(item) + "\t" + str(item_j) + "\t" + str(score) + "\n")
    fd.close()


def main():
    session_item, item_session = gen_item_pair(config.input_file, config.output_file, config.debug)
    uniq_pair(config.output_file)
    item_sim_dict = calc_simlarity(session_item, item_session, config.output_file)
    del session_item, item_session
    output_sim_file(item_sim_dict, config.output_file)


if __name__ == "__main__":
    logging.info("input_file:" + config.input_file)
    logging.info("output_file:" + config.output_file)
    main()
