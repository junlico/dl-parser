import re
from abc import ABC, abstractclassmethod

from utils import save_json


class P1(ABC):
    def __init__(self, key, pattern, files=None):
        self.key = key
        self.pattern = re.compile(pattern)
        self.files = files if files else [key]
        self.data = {}

    def parse(self, line, f):
        if k := self.pattern.search(line):
            # parse next line for value
            if v := re.search(r"\"(.+)\"", f.readline()):
                self.modify(k[1], v[1])

    def modify(self, key, value):
        pass

    def register(self):
        pass

    def finalize(self):
        setattr(P1, self.key, self.data)
        save_json(self.key, self.data)


class Label(P1):
    def __init__(self):
        pattern = r"Id = \"((?:ABILITY_NAME|SKILL_NAME|ABILITY_DETAIL)_\d+)\""
        super().__init__("labels", pattern, ["en"])

    def modify(self, key, value):
        self.data[key] = re.sub(r" ?\\n", " ", value)


class Name(P1):
    def __init__(self):
        pattern = r"Id = \"((?:CHARA|WEAPON|DRAGON|AMULET|FORT_PLANT)_NAME_\d+)\""
        super().__init__("names", pattern, ["en", "ja", "zh"])
        self.lang = "en"

    def modify(self, key, value):
        item = self.data.get(key, {"en": "", "ja": "", "zh": ""})
        item[self.lang] = value
        self.data[key] = item

    def finalize(self):
        self.data["CHARA_NAME_10150403"] = self.data["CHARA_NAME_10140101"]
        super().finalize()

