class DiffChange:
    REMOVED = 0
    ADDED = 1
    MODIFIED = 2


def diff_dict(a, b) -> dict:
    """ get the difference between 2 dicts. if the dicts are the same it will return an empty dict. if the dicts are
    different it will return a dict with the differnce between the 2 dicts. it will recursively check the dict for
    diffences. it will return a 2 if a value is different, 1 if it is only in b(added) to b and 0 if it is only in a(removed).
    for arrays it will give the new values in the array. it will not check for order.

    :param a: dict. the dict to compare to. this is the original dict.
    :param b: dict. the dict to compare. this is the new dict.
    :return: dict. the difference between the 2 dicts. if the dicts are the same it will return an empty dict.

    example:
    a = {'a': 1, 'b': 2, 'c': 3}
    b = {'a': 1, 'b': 3, 'd': 4}
    diff_dict(a, b) == {'b': (2, 3), 'c': (0, 3), 'd': (1, 4)}

    a = {'a': 1, 'b': [1, 2, 3], 'c': 3}
    b = {'a': 1, 'b': [1, 3, 4], 'd': 4}
    diff_dict(a, b) == {'b': ((0, [2]), (1, [4])), 'c': (0, 3), 'd': (1, 4)}

    a = {'a': 1, 'b': {'a': 1, 'b': 2}, 'c': 3}
    b = {'a': 1, 'b': {'a': 1, 'b': 3}, 'd': 4}
    diff_dict(a, b) == {'b': {'b': (2, 3)}, 'c': (0, 3), 'd': (1, 4)}
    """

    keys = set(a.keys()).union(b.keys())
    diff = {}

    for key in keys:
        if key not in a:
            diff[key] = (DiffChange.ADDED, b[key])
        elif key not in b:
            diff[key] = (DiffChange.REMOVED, a[key])

        elif a[key] != b[key]:
            # check if it is an array
            if isinstance(a[key], list) and isinstance(b[key], list):
                # check if they are the same
                if a[key] == b[key]:
                    continue

                # check if the array is the same but the order is different.
                if set(a[key]) == set(b[key]):
                    continue

                # check if the array is different. 2 is in a but not in b 1 is in b but not in a
                added = [i for i in b[key] if i not in a[key]]
                removed = [i for i in a[key] if i not in b[key]]

                diff[key] = (
                    (DiffChange.REMOVED, removed),
                    (DiffChange.ADDED, added),
                )
            # check if it is a dict
            elif isinstance(a[key], dict) and isinstance(b[key], dict):
                # check if they are the same
                # recursive diff
                d = diff_dict(a[key], b[key])
                if d:
                    diff[key] = d

                continue
            else:
                diff[key] = (DiffChange.MODIFIED, b[key])

    return diff


def apply_diff(a: dict, diff: dict, apply=False) -> dict:
    """ apply a diff to a dict. this will return a new dict. it will not change the original dict unless apply is set
        to true. if apply is set to true it will still return a dict. this function will recursively apply the diff to
        dict a.

        :param a: dict. the dict to apply the diff to. this is the original dict.
        :param diff: dict. the diff to apply to the dict.
        :param apply: bool. if true it will change the original dict. if false it will return a new dict.
        :return: dict. the new dict with the diff applied.
    """
    if not apply:
        b = a.copy()
    else:
        b = a

    for key, value in diff.items():

        if isinstance(value, tuple):
            if isinstance(value[0], tuple):
                for i in value:
                    if i[0] == DiffChange.REMOVED:
                        for j in i[1]:
                            b[key].remove(j)

                    elif i[0] == DiffChange.ADDED:
                        b[key] += i[1]
            elif value[0] == DiffChange.REMOVED:
                del b[key]
            else:
                # throws strange error when using __dict__ of NodeConfigData, TypeError without message.
                b[key] = value[1] 

        elif isinstance(value, list):
            if value[0] == DiffChange.REMOVED:
                b[key] = [i for i in b[key] if i not in value[1]]

            elif value[0] == DiffChange.ADDED:
                b[key] += value[1]

        elif isinstance(value, dict):
            b[key] = apply_diff(b[key], value)

    return b


import libs.external.umsgpack as umsgpack
def serialize_dict(d): 
    """ serialize a dict to bytes """
    return umsgpack.dumps(d)

def deserialize_dict(d):
    """ deserialize a dict from bytes """
    return umsgpack.loads(d)
