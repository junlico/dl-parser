import re
from abc import ABC, abstractclassmethod

from utils import save_json


class Base(ABC):
    def __init__(self, key, files=None):
        self.key = key
        self.files = files if files else [key]
        self.data = {}

    def parse(self, line, f):
        pattern = self.get_pattern()

        if k := re.search(pattern, line):
            # parse next line for value
            if v := re.search(r"\"(.+)\"", f.readline()):
                self.modify(k[1], v[1])

    def modify(self, key, value):
        pass

    def register(self):
        pass

    def finalize(self):
        setattr(Base, self.key, self.data)
        save_json(self.key, self.data)

    @abstractclassmethod
    def get_pattern(self):
        pass


class Label(Base):
    def __init__(self):
        super().__init__("labels", ["en"])

    def modify(self, key, value):
        self.data[key] = re.sub(r" ?\\n", " ", value)

    def get_pattern(self):
        return r"Id = \"((?:ABILITY_NAME|SKILL_NAME|ABILITY_DETAIL)_\d+)\""


class Name(Base):
    def __init__(self):
        super().__init__("names", ["en", "ja", "zh"])
        self.lang = "en"

    def modify(self, key, value):
        item = self.data.get(key, {"en": "", "ja": "", "zh": ""})
        item[self.lang] = value
        self.data[key] = item

    def finalize(self):
        self.data["CHARA_NAME_10150403"] = self.data["CHARA_NAME_10140101"]
        super().finalize()

    def get_pattern(self):
        return r"Id = \"((?:CHARA|WEAPON|DRAGON|AMULET|FORT_PLANT)_NAME_\d+)\""
