# coding=utf-8
# Copyleft 2019 project LXRT.

import sys
import csv
import base64
import time

import numpy as np

csv.field_size_limit(sys.maxsize)
FIELDNAMES = [
    "img_id",
    "img_h",
    "img_w",
    "objects_id",
    "objects_conf",
    "attrs_id",
    "attrs_conf",
    "num_boxes",
    "boxes",
    "features",
]


def load_obj_tsv(fname, topk=None, fp16=False):
    """Load object features from tsv file.

    :param fname: The path to the tsv file.
    :param topk: Only load features for top K images (lines) in the tsv file.
        Will load all the features if topk is either -1 or None.
    :return: A list of image object features where each feature is a dict.
        See FILENAMES above for the keys in the feature dict.
    """
    data = []
    start_time = time.time()
    print("Start to load Faster-RCNN detected objects from %s" % fname)
    with open(fname) as f:
        reader = csv.DictReader(f, FIELDNAMES, delimiter="\t")
        for i, item in enumerate(reader):

            for key in ["img_h", "img_w", "num_boxes"]:
                item[key] = int(item[key])

            boxes = item["num_boxes"]
            decode_config = [
                ("objects_id", (boxes,), np.int64),
                ("objects_conf", (boxes,), np.float32),
                ("attrs_id", (boxes,), np.int64),
                ("attrs_conf", (boxes,), np.float32),
                ("boxes", (boxes, 4), np.float32),
                ("features", (boxes, -1), np.float32),
            ]
            for key, shape, dtype in decode_config:
                item[key] = np.frombuffer(base64.b64decode(item[key]), dtype=dtype)

                if fp16 and item[key].dtype == np.float32:
                    item[key] = item[key].astype(
                        np.float16
                    )  # Save features as half-precision in memory.
                item[key] = item[key].reshape(shape)
                item[key].setflags(write=False)

            data.append(item)
            if topk is not None and len(data) == topk:
                break
    elapsed_time = time.time() - start_time
    print(
        "Loaded %d images in file %s in %d seconds." % (len(data), fname, elapsed_time)
    )
    return data
