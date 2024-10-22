import hashlib
import pickle
from moirae.serialize import serialize


def stable_hash(*args, **kwargs):
    hash_obj = hashlib.blake2b(serialize(args))
    return hash_obj.hexdigest()
