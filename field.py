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

    if r is not None:
        return value, r[1]


class Common(ABC):
    def __init__(self, file_name, files=None):
        self.data = {}
        self.item = {}
        self.file_name = file_name
        self.files = [file_name] if files is None else files

    def attach_data(self, attr=None):
        if attr is None:
            key = self.file_name
            data = self.data
        else:
            key = attr
            data = read_json(attr)

        if getattr(self, key, None) is None:
            setattr(Common, key, data)

    def get_value(self, attr, key):
        return getattr(self, attr, {}).get(key, None)

    def save_file(self):
        save_json(self.file_name, self.data)

    def reset_item(self):
        self.data[self.item["Id"]] = self.item
        self.item = {}

    def parse_item(self, f, line, key):
        r = re.search(r"_(\w+) = \"?(-?\w*)\"?", line)

        if r is None:
            return

        prop, value = r.groups()

        str_props = getattr(self, "str_props")
        int_props = getattr(self, "int_props")

        if prop in str_props:
            self.item[prop] = value
        elif prop in int_props:
            self.item[prop] = int(value)

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

        self.attach_data()


class Label(Common):
    def __init__(self):
        super().__init__("labels", ["en"])

    def parse_item(self, f, line, key):
        pattern = r"Id = \"((?:ABILITY_NAME|SKILL_NAME|ABILITY_DETAIL)_\d+)\""
        r = parse_label(pattern, f, line)

        if r is None:
            return

        uid, value = r
        value = value.replace(" \\n", " ")
        value = value.replace("\\n", " ")
        self.data[uid] = value

    def finalize(self):
        self.attach_data()


class Skill(Common):
    def __init__(self):
        super().__init__("skills")
        self.str_props = ("Id", "Name", "SkillLv1IconName")
        self.int_props = ()
        self.attach_data("labels")

    def modify_item(self):
        if self.item:
            self.item["Name"] = self.get_value("labels", self.item["Name"])
            self.item["Icon"] = self.item.pop("SkillLv1IconName")
            self.reset_item()


if __name__ == "__main__":
    pass
