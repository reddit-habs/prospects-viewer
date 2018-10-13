import importlib
import json
from enum import Enum
from json import JSONEncoder
from pathlib import Path

import attr


def _ser_filter_attrs(attr, val):
    return attr.init


def _get_class_path(o):
    return "{}.{}".format(o.__module__, o.__class__.__qualname__)


def _parse_class_path(path: str):
    last_dot = path.rfind(".")
    return path[:last_dot], path[last_dot:][1:]


def _load_class(path):
    mod, klass = _parse_class_path(path)
    m = importlib.import_module(mod)
    return getattr(m, klass)


class _DtoJsonEncoder(JSONEncoder):
    def default(self, obj):
        if attr.has(obj):
            d = attr.asdict(obj, recurse=False, filter=_ser_filter_attrs)
            d["__class__"] = _get_class_path(obj)
            return d
        elif isinstance(obj, Enum):
            return {"__enum__": _get_class_path(obj), "name": obj.name, "value": obj.value}
        else:
            return super().default(obj)


def dumps(obj, indent=None):
    return _DtoJsonEncoder(indent=indent).encode(obj)


def dumpf(path, obj, indent=None):
    Path(path).write_text(dumps(obj, indent=indent))


def _walk_de(obj):
    if isinstance(obj, list):
        return [_walk_de(item) for item in obj]
    elif isinstance(obj, dict):
        d = {key: _walk_de(val) for key, val in obj.items()}
        klass_path = d.get("__class__")
        if klass_path is not None:
            klass = _load_class(klass_path)
            del d["__class__"]
            return klass(**d)
        enum_path = d.get("__enum__")
        if enum_path is not None:
            enum = _load_class(enum_path)
            return enum(d.get("value"))
        return d
    else:
        return obj


def loads(text):
    d = json.loads(text)
    return _walk_de(d)


def loadf(path):
    return loads(Path(path).read_text())


__all__ = ["loads", "loadf", "dumps", "dumpf"]
