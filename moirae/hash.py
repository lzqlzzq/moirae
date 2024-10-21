import hashlib
import pickle
from moirae.serialize import serialize


def recursively_sort(obj):
    if isinstance(obj, dict):
        return tuple((k, recursively_sort(v)) for k, v in sorted(obj.items(), key=lambda x: str(x[0])))
    elif isinstance(obj, (list, tuple, set)):
        return tuple(recursively_sort(item) for item in sorted(obj, key=lambda x: str(x)))
    else:
        return obj


def stable_hash(*args, **kwargs):
    sorted_data = recursively_sort(args)
    hash_obj = hashlib.blake2b(serialize(sorted_data))
    return hash_obj.hexdigest()
