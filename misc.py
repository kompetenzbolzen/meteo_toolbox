import numpy as np
import datetime

def np_time_convert(dt64):
    unix_epoch = np.datetime64(0, 's')
    one_second = np.timedelta64(1, 's')
    seconds_since_epoch = (dt64 - unix_epoch) / one_second

    return datetime.datetime.utcfromtimestamp(seconds_since_epoch)
