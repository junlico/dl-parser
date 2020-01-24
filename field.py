import re
from abc import ABC, abstractclassmethod

from utils import save_json


class Base1(ABC):
    def __init__(self, file_name, files=None):
        self.data = {}
        self.file_name = file_name
        self.files = [file_name] if files is None else files

    def attach_data(self):
        setattr(Base1, self.file_name, self.data)

    def parse_item(self, f, line):
        pattern = self.get_pattern()

        if not (k := re.search(pattern, line)):
            return

        # read next line to get value
        if v := re.search(r"\"(.+)\"", f.readline()):
            self.modify_item(k[1], v[1])

    def finalize(self):
        self.attach_data()
        save_json(self.file_name, self.data)

    def register_item(self):
        pass

    def modify_item(self, key, value):
        pass

    @abstractclassmethod
    def get_pattern(self):
        pass


class Name(Base1):
    def __init__(self):
        super().__init__("names", ["en", "ja", "zh"])
        self.lang = "en"

    def modify_item(self, key, value):
        item = self.data.get(key, {"en": "", "ja": "", "zh": ""})
        item[self.lang] = value
        self.data[key] = item

    def finalize(self):
        self.data["CHARA_NAME_10150403"] = self.data["CHARA_NAME_10140101"]
        super().finalize()

    def get_pattern(self):
        return r"Id = \"((?:CHARA|WEAPON|DRAGON|AMULET|FORT_PLANT)_NAME_\d+)\""


class Label(Base1):
    def __init__(self):
        super().__init__("labels", ["en"])

    def modify_item(self, key, value):
        value = value.replace(" \\n", " ")
        value = value.replace("\\n", " ")
        self.data[key] = value

    def get_pattern(self):
        return r"Id = \"((?:ABILITY_NAME|SKILL_NAME|ABILITY_DETAIL)_\d+)\""


class Base2(Base1):
    def __init__(self, file_name):
        super().__init__(file_name)
        self.item = {}

    def parse_item(self):
        print("Base2 parse_item")

    def finalize(self):
        save_json(self.finalize, self.data)

    def get_pattern(self):
        return r"_(\w+) = \"?(-?\w*)\"?"


class Adventurer(Base2):
    def __init__(self):
        super().__init__("adventurer")


class Weapon(Base2):
    def __init__(self):
        super().__init__("weapon")


class Dragon(Base2):
    def __init__(self):
        super().__init__("dragon")


class Wyrmprint(Base2):
    def __init__(self):
        super().__init__("wyrmprint")


if __name__ == "__main__":
    pass
