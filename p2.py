import re

from p1 import P1
from utils import ELEMENT_TYPE, read_json


class P2(P1):
    def __init__(self, key, columns):
        pattern = r"_(\w+) = \"?(-?\w*)\"?"
        super().__init__(key, pattern)
        self.columns = columns
        self.item = {}
        self.attach_data("labels")

    def parse(self, line, f):
        if r := self.pattern.search(line):
            if r[1] in self.columns:
                self.item[r[1]] = r[2]

    def register(self):
        if self.eligible():
            self.modify()
            self.data[self.item["Id"]] = self.item

        self.item = {}

    def modify(self):
        self.set_prop()
        self.set_name()
        self.set_image()

    def eligible(self):
        return self.item

    def set_prop(self):
        pass

    def set_name(self):
        pass

    def set_image(self):
        pass

    def attach_data(self, key):
        if not getattr(P1, key, None):
            data = read_json(key)
            setattr(P1, key, data)

    def get_value(self, attr, key):
        return getattr(self, attr, {}).get(key, None)


class Ability(P2):
    def __init__(self):
        columns = (
            "Id",
            "Name",
            "Details",
            "AbilityIconName",
            "PartyPowerWeight",
            "ElementalType",
            "ConditionType",
            "ConditionValue",
            "AbilityType1",
            "AbilityType2",
            "AbilityType3",
            "VariousId1a",
            "VariousId2a",
            "VariousId3a",
            "AbilityType1UpValue",
            "AbilityType2UpValue",
            "AbilityType3UpValue",
        )

        super().__init__("abilities", columns)
        self.attach_data("ability_val")
        self.__enemy_dict = {
            "3": "hms",
            "5": "hmc",
            "7": "hbh",
            "9": "hjp",
            "11": "hzd",
        }

    def eligible(self):
        item = self.item

        if item:
            item["Name"] = self.get_value("labels", item["Name"])
            item["Details"] = self.get_value("labels", item["Details"])

        return item and item["Name"] and item["Details"]

    def modify(self):
        super().modify()
        self.set_type()

    def set_prop(self):
        item = self.item
        item["Might"] = int(item.pop("PartyPowerWeight"))
        item["Element"] = ELEMENT_TYPE[int(item.pop("ElementalType"))]

    def set_name(self):
        item = self.item
        uid = item["Id"]
        cond = item.pop("ConditionValue")
        temp = self.get_value("ability_val", uid)

        for k in ("Name", "Details"):
            text = item[k]

            if item["AbilityType1UpValue"] == "0" and "{ability_val0}" in text:
                if temp:
                    item["AbilityType1UpValue"] = temp
                else:
                    print("{}: ability_val0 loss".format(uid))

            element = None
            if not item["Element"]:
                if r := re.search(r"\((Flame|Water|Wind|Light|Shadow)\)", text):
                    element = r[1]
                elif "{element_owner}" in text and not (element := temp):
                    print("{}: element_owner loss".format(uid))

                item["Element"] = element

            item[k] = text.format(
                ability_shift0="",
                ability_val0=item["AbilityType1UpValue"],
                element_owner=item["Element"],
                ability_cond0=cond,
            )

    def set_image(self):
        image = self.item.pop("AbilityIconName")
        self.item["Image"] = image.replace("Icon_Ability_", "")

    def set_type(self):
        item = self.item
        cond = int(item.pop("ConditionType"))
        type_list = []
        for i in range(1, 4):
            key1 = item.pop("AbilityType{}".format(i))
            key2 = item.pop("VariousId{}a".format(i))
            value = int(item.pop("AbilityType{}UpValue".format(i)))

            if cond < 2:
                ability_type = "{}_{}".format(key1, key2)
                type_item = None
                if ability_type == "1_1":
                    type_item = {"Key": "IncHP"}
                elif ability_type == "1_2":
                    type_item = {"Key": "IncSTR"}
                elif ability_type == "1_3":
                    type_item = {"Key": "IncDEF"}
                elif key1 == "28":
                    type_item = {"Key": "IncRES", "ResEle": ELEMENT_TYPE[int(key2)]}
                elif key1 == "29" and (enemy := self.__enemy_dict.get(key2, None)):
                    type_item = {"Key": "IncDIS", "Enemy": enemy}

                if type_item:
                    type_item["Value"] = value
                    type_list.append(type_item)

        if type_list:
            item["Type"] = type_list


class Skill(P2):
    def __init__(self):
        columns = (
            "Id",
            "Name",
            "SkillLv2IconName",
        )

        super().__init__("skills", columns)

    def set_name(self):
        self.item["Name"] = self.get_value("labels", self.item["Name"])

    def set_image(self):
        self.item["Image"] = self.item.pop("SkillLv2IconName")
