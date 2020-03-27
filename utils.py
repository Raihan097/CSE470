import os
from uuid import uuid4


def generate_uuid() -> str:
    return uuid4().hex


def clear_dir(path: str):
    try:
        for file in os.listdir(path):
            os.remove(os.path.join(path, file))
    except:
        return
