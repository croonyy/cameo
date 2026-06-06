from pprint import pprint
from types import MethodType, FunctionType


def get_structure(obj, cnt=3):
    """
    Returns the structure of an object as a dictionary
    """
    doc = {}
    for i in dir(obj):
        attr = getattr(obj, i)
        if isinstance(attr, (str, int, float)):
            doc[i] = attr
        elif isinstance(attr, dict):
            tmp = {
                k: v if isinstance(v, (str, int, float)) else type(v)
                for k, v in list(attr.items())[: min(len(attr), cnt)]
            }
            if len(attr) > cnt:
                tmp["..."] = "..."
            doc[i] = tmp
        elif isinstance(attr, list):
            tmp = [
                v if isinstance(v, (str, int, float)) else type(v)
                for v in attr[: min(len(attr), cnt)]
            ]
            if len(attr) > cnt:
                tmp.append("...")
            doc[i] = tmp
        elif isinstance(attr, tuple):
            tmp = tuple(
                [
                    v if isinstance(v, (str, int, float)) else type(v)
                    for v in attr[: min(len(attr), cnt)]
                ]
            )
            if len(attr) > cnt:
                tmp += ("...",)
            doc[i] = tmp
        elif isinstance(attr, set):
            tmp = {
                v if isinstance(v, (str, int, float)) else type(v)
                for v in list(attr)[: min(len(attr), cnt)]
            }
            if len(attr) > cnt:
                tmp.add("...")
            doc[i] = tmp
        elif isinstance(attr, (MethodType, FunctionType)):
            doc[i] = (type(attr), attr.__annotations__)
        else:
            doc[i] = type(attr)
    pprint(doc)
    return doc


if __name__ == "__main__":
    print(get_structure({"a": "a", "b": {"b": "b", "c": "c"}}))
