import os
import numpy as np
import datetime

def np_time_convert(dt64, func=datetime.datetime.utcfromtimestamp):
    unix_epoch = np.datetime64(0, 's')
    one_second = np.timedelta64(1, 's')
    seconds_since_epoch = (dt64 - unix_epoch) / one_second

    return func(seconds_since_epoch)

def np_time_convert_offset(init, step):
    return np_time_convert(init) + np_time_convert(step, func=lambda x: datetime.timedelta(seconds=x))

def np_time_list_convert_offset(init, steps):
    return list(map(lambda x: np_time_convert_offset(init, x), steps))

def create_output_dir(path, clear=False):
    if not os.path.exists(path):
        os.makedirs(path)
    elif clear:
        raise Exception('clear not implemented')

