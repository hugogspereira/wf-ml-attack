import numpy as np

import const_rf
import multiprocessing as mp
import pandas as pd
from importlib import import_module
import tqdm


def parallel(para_list, n_jobs=1):
    pool = mp.Pool(n_jobs)
    data_dict = tqdm.tqdm(pool.imap(extract_feature, para_list), total=len(para_list))
    pool.close()
    return data_dict


def extract_feature(para):
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # project root
    from FeatureExtraction import packets_per_slot
    
    f, feature_func = para
    file_name = f.split('/')[-1]

    with open(f, 'r') as f:
        tcp_dump = f.readlines()

    seq = pd.Series(tcp_dump[:const_rf.max_trace_length]) \
        .str.split(const_rf.split_mark, expand=True) \
        .apply(pd.to_numeric, errors='coerce')
    seq = seq.dropna()
    
    times = np.array(seq.iloc[:, 0])
    length_seq = np.array(seq.iloc[:, 1]).astype("int")
    fun = import_module('FeatureExtraction.' + feature_func)
    feature = fun.fun(times, length_seq)
    if '-' in file_name:
        label = file_name.split('-')
        label = int(label[0])
    else:
        label = const_rf.MONITORED_SITE_NUM

    return feature, label


def process_dataset(file_name, suffix):
    output_dir = const_rf.output_dir + defence + '-' + suffix + '-' + feature_func

    para_list = []
    file = open(file_name, 'r')
    lines = file.readlines()
    for line in lines:
        l = line.strip()
        para_list.append((traces_path + l, feature_func))

    data_dict = {'dataset': [], 'label': []}
    raw_data_dict = parallel(para_list, n_jobs=15)
    features, label = zip(*raw_data_dict)

    features = np.array(features)
    if len(features.shape) < 3:
        features = features[:, np.newaxis, :]
    labels = np.array(label)

    print(suffix + " dataset shape:{}, label shape:{}".format(features.shape, labels.shape))
    data_dict['dataset'], data_dict['label'] = features, labels
    np.save(output_dir, data_dict)

    print('save to %s' % (output_dir + ".npy"))


if __name__ == '__main__':

    defence = 'Undefence'
    traces_path = './../../../data/features/'
    feature_func = 'packets_per_slot'

    train_name = 'list/Index_train.txt'
    test_name = 'list/Index_test.txt'

    process_dataset(train_name, 'train')
    process_dataset(test_name, 'test')
