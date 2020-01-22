import re
from abc import ABC

from utils import read_json, save_json

ELEMENT_TYPE = [None, "Flame", "Water", "Wind", "Light", "Shadow"]


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

    def set_value(self, attr, key, value):
        data = getattr(self, attr, {})
        data[key] = value

    def save_file(self):
        save_json(self.file_name, self.data)

    def register_item(self):
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
            self.register_item()


class Ability(Common):
    def __init__(self):
        super().__init__("abilities")
        self.str_props = (
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
        self.int_props = (
            "PartyPowerWeight",
            "ElementalType",
            "ConditionType",
            "ConditionValue",
            "AbilityType1UpValue",
            "AbilityType2UpValue",
            "AbilityType3UpValue",
        )
        self.__enemy = {
            "3": "hms",
            "5": "hmc",
            "7": "hbh",
            "9": "hjp",
            "11": "hzd",
        }

        self.attach_data("labels")
        self.attach_data("ability_val")
        self.save_ability_val = False

    def modify_item(self):
        item = self.item

        if not item:
            return

        if not self.get_value("labels", item["Name"]):
            self.item = {}
            return

        for k in ["Name", "Details"]:
            text = self.get_value("labels", item[k])

            if text is None:
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
        self.register_item()

    def finalize(self):
        if self.save_ability_val:
            save_json("ability_val", getattr(self, "ability_val"))

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
                r = re.search(r"(Flame|Water|Wind|Light|Shadow)", item["Name"])
                if r is not None:
                    element = r[1]
                elif not (element := self.get_value("ability_val", uid)):
                    print("{}: element_owner loss".format(uid))
                    self.set_value("ability_val", uid, "")
                    self.save_ability_val = True

                item["ElementalType"] = ELEMENT_TYPE.index(element)
            else:
                element = ELEMENT_TYPE[item["ElementalType"]]

        return element


if __name__ == "__main__":
    pass
