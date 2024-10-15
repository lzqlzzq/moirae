import hashlib
import pickle


def recursively_sort(obj):
    if isinstance(obj, dict):
        return tuple((k, recursively_sort(v)) for k, v in sorted(obj.items(), key=lambda x: str(x[0])))
    elif isinstance(obj, (list, tuple, set)):
        return tuple(recursively_sort(item) for item in sorted(obj, key=lambda x: str(x)))
    else:
        return obj


def stable_hash(*args, **kwargs):
	return hashlib.sha256(pickle.dumps(recursively_sort(args)))
