def run(data, vars):
    ret = data[0]
    for var in vars:
        ret[var['name']] = ret[var['field']].diff(var['by'])

    return ret
