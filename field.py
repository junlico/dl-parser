import re
from abc import ABC, abstractclassmethod

from utils import read_json, save_json

ELEMENT_TYPE = [None, "Flame", "Water", "Wind", "Light", "Shadow"]


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
    def __init__(self, file_name, str_props, int_props):
        super().__init__(file_name)
        self.item = {}
        self.str_props = str_props
        self.int_props = int_props

    def get_value(self, attr, key):
        return getattr(Base2, attr, {}).get(key, None)

    def set_value(self, attr, key, value):
        data = getattr(Base2, attr, {})
        data[key] = value

    def attach_data(self, key):
        data = read_json(key)
        setattr(Base2, key, data)

    def parse_item(self, f, line):
        pattern = self.get_pattern()
        if not (r := re.search(pattern, line)):
            return

        key, value = r.groups()

        if key in self.str_props:
            self.item[key] = value
        elif key in self.int_props:
            self.item[key] = int(value)

    def register_item(self):
        if not self.eligible():
            self.item = {}
            return

        self.modify_item()
        self.data[self.item["Id"]] = self.item
        self.item = {}

    def finalize(self):
        save_json(self.file_name, self.data)

    def get_pattern(self):
        return r"_(\w+) = \"?(-?\w*)\"?"

    def eligible(self):
        return self.item

    @abstractclassmethod
    def modify_item(self):
        pass


class Ability(Base2):
    def __init__(self):
        str_props = (
            "Id",
            "Name",
            "Details",
            "AbilityIconName",
            "AbilityType1",
            "AbilityType2",
            "AbilityType3",
            "VariousId1a",
            "VariousId2a",
            "VariousId3a",
        )
        int_props = (
            "PartyPowerWeight",
            "ElementalType",
            "ConditionType",
            "ConditionValue",
            "AbilityType1UpValue",
            "AbilityType2UpValue",
            "AbilityType3UpValue",
        )
        super().__init__("abilities", str_props, int_props)
        self.save_ability_val = False
        self.attach_data("ability_val")

    def eligible(self):
        return self.item and self.get_value("labels", self.item["Name"])

    def modify_item(self):
        item = self.item

        for k in ["Name", "Details"]:
            if (text := self.get_value("labels", item[k])) is None:
                continue

            val = self.__get_val(text)
            element = self.__get_element(text)

            text = text.format(
                ability_shift0="",
                ability_val0=val,
                element_owner=element,
                ability_cond0=item["ConditionValue"],
            )

            item[k] = text

        del item["ConditionValue"]

    def __get_val(self, text):
        item = self.item
        if item["AbilityType1UpValue"] == 0 and "{ability_val0}" in text:
            uid = item["Id"]
            if not (val := self.get_value("ability_val", uid)):
                print("{}: ability_val0 loss".format(uid))
                self.set_value("ability_val", uid, "")
                self.save_ability_val = True
            else:
                item["AbilityType1UpValue"] = val

        return item["AbilityType1UpValue"]

    def __get_element(self, text):
        item = self.item
        element = None
        if "{element_owner}" in text:
            if item["ElementalType"] == 0:
                uid = item["Id"]
                element_pattern = r"(Flame|Water|Wind|Light|Shadow)"

                if r := re.search(element_pattern, item["Name"]):
                    element = r[1]
                elif not (element := self.get_value("ability_val", uid)):
                    print("{}: element_owner loss".format(uid))
                    self.set_value("ability_val", uid, "")
                    self.save_ability_val = True

                item["ElementalType"] = ELEMENT_TYPE.index(element)
            else:
                element = ELEMENT_TYPE[item["ElementalType"]]

        return element


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
