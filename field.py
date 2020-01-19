import re
from abc import ABC

from utils import read_json, save_json


def parse_label(pattern, f, line):
    r = re.search(pattern, line)

    if r is None:
        return

    value = r[1]

    line = f.readline()
    r = re.search(r"\"(.+)\"", line)

    return value, r[1]


class Common(ABC):
    def __init__(self, file_name, files=None):
        self.data = {}
        self.item = {}
        self.file_name = file_name
        self.files = [file_name] if files is None else files

    def save_file(self):
        save_json(self.file_name, self.data)

    def reset_item(self):
        self.data[self.item["Id"]] = self.item
        self.reset_item()

    def modify_item(self):
        pass

    def finalize(self):
        pass


class Name(Common):
    def __init__(self):
        super().__init__("names", ["en", "ja", "zh"])

    def parse_item(self, f, line, key):
        pattern = r"Id = \"((?:CHARA|WEAPON|DRAGON|AMULET|FORT_PLANT)_NAME_\d+)\""

        r = parse_label(pattern, f, line)

        if r is None:
            return

        uid, value = r
        item = self.data.get(uid, {"en": "", "ja": "", "zh": ""})
        item[key] = value
        self.data[uid] = item

    def finalize(self):
        self.data["CHARA_NAME_10150403"] = {
            "en": "Euden",
            "ja": "ユーディル",
            "zh": "尤蒂尔",
        }

        setattr(Common, self.file_name, self.data)


if __name__ == "__main__":
    pass
