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


def gen_item_pair(input_file, output_file):
    # session_chunks = pd.read_json(input_file, lines=True, chunksize=100000)
    session_item = dict()
    item_session = dict()
    # pair_dict = dict()
    # item_pairs = set()
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
            session_item[session_id] = click_aid
            for aid in click_aid:
                item_session.setdefault(aid, set())
                item_session[aid].add(session_id)
            pair_list = list(combinations(click_aid, 2))

            # for pair in pair_list:
            #     if pair[0] == pair[1]:
            #         continue
            #     pair_dict.setdefault(pair[0], Lossy_Counting(pair[0], 10000))
            #     pair_dict.setdefault(pair[1], Lossy_Counting(pair[1], 10000))
            #     pair_dict[pair[0]].enter_num(pair[1])
            #     pair_dict[pair[1]].enter_num(pair[0])

            for pair in pair_list:
                if pair[0] > pair[1]:
                    pair_str = str(pair[0]) + "," + str(pair[1])
                elif pair[0] < pair[1]:
                    pair_str = str(pair[1]) + "," + str(pair[0])
                else:
                    continue
                hash_code = int(hashlib.md5((pair_str + str(config.seed)).encode('utf8')).hexdigest()[0:10], 16) % 10
                fdout[hash_code].write(pair_str+"\n")
            idx += 1
            if idx >= 50000:
                break
    for fd in fdout:
        fd.close()
    # logging.info("Loop train file done!")
    # pair_set = set()
    # for key in pair_dict.keys():
    #     sort_key = pair_dict[key].topk(5000)
    #     for (r_key, count) in sort_key:
    #         if key > r_key:
    #             pair_set.add(str(r_key) + "," + str(key))
    #         elif key < r_key:
    #             pair_set.add(str(key) + "," + str(r_key))
    #
    # logging.info("item pairs length：{}".format(len(pair_set)))
    return session_item, item_session


def calc_simlarity(session_item, item_session, output_file, alpha=1.0, session_num_threhold=1000):
    item_sim_dict = dict()
    # logging.info("item pairs length：{}".format(len(item_pairs)))
    # fdout = open(output_file, "w")
    pair_path = Path(output_file).parent.joinpath("tmp")

    for i in range(10):
        pair_file = str(pair_path) + "/pair_" + str(i) + ".uniq"
        logging.info("calc_simlarity file " + pair_file)
        with open(pair_file, "r") as f:
        # for item_pair in tqdm(item_pairs, desc="calculate similarities"):
            for item_pair in tqdm(f, desc="calc_simlarity:"+pair_file):
                pair_str = item_pair.strip()
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
                    result += 1 / (alpha + len(session_item[user_u] & session_item[user_v]))
                item_sim_dict.setdefault(item_i, Heap(item_i, 100))
                item_sim_dict[item_i].enter_item([item_j, result])
                item_sim_dict.setdefault(item_j, Heap(item_j, 100))
                item_sim_dict[item_j].enter_item([item_i, result])
                # fdout.write(str(item_i)+","+str(item_j)+","+str(result))
        logging.info("calc_simlarity file " + pair_file + " done!")
    logging.info("Calculate similarity finished!")
    # fdout.close()
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
    session_item, item_session = gen_item_pair(config.input_file, config.output_file)
    uniq_pair(config.output_file)
    item_sim_dict = calc_simlarity(session_item, item_session, config.output_file)
    del session_item, item_session
    output_sim_file(item_sim_dict, config.output_file)


if __name__ == "__main__":
    logging.info("input_file:" + config.input_file)
    logging.info("output_file:" + config.output_file)
    main()