import re

from label import Base
from utils import read_json


ELEMENT_TYPE = [None, "Flame", "Water", "Wind", "Light", "Shadow"]
WEAPON_TYPE = [None, "Sword", "Blade", "Dagger", "Axe", "Lance", "Bow", "Wand", "Staff"]


class Common(Base):
    def __init__(self, key, columns):
        super().__init__(key)
        self.columns = columns
        self.item = {}

    def parse(self, line, f):
        pattern = self.get_pattern()

        if r := re.search(pattern, line):
            if r[1] in self.columns:
                self.item[r[1]] = r[2]

    def register(self):
        if self.eligible():
            self.modify()
            self.data[self.item["Id"]] = self.item

        self.item = {}

    def eligible(self):
        return self.item

    def modify(self):
        pass

    def get_pattern(self):
        return r"_(\w+) = \"?(-?\w*)\"?"

    def attach_data(self, key):
        if not getattr(self, key, None):
            data = read_json(key)
            setattr(Common, key, data)

    def get_value(self, attr, key):
        return getattr(Common, attr, {}).get(key, None)


class Ability(Common):
    def __init__(self):
        columns = (
            "Id",
            "Name",
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

        self.__enemy_dict = {
            "3": "hms",
            "5": "hmc",
            "7": "hbh",
            "9": "hjp",
            "11": "hzd",
        }

        self.attach_data("labels")
        self.attach_data("ability_val")

    def eligible(self):
        return super().eligible() and self.get_value("labels", self.item["Name"])

    def modify(self):
        self.set_prop()
        self.set_name()
        self.set_image()
        self.set_ability()

    def set_prop(self):
        item = self.item
        item["Might"] = int(item.pop("PartyPowerWeight"))
        item["Element"] = int(item.pop("ElementalType"))

    def set_name(self):
        item = self.item
        uid = item["Id"]
        temp = self.get_value("ability_val", uid)

        text = self.get_value("labels", item["Name"])
        if item["AbilityType1UpValue"] == "0" and "{ability_val0}" in text:
            if temp:
                item["AbilityType1UpValue"] = temp
            else:
                print("{}: ability_val0 loss".format(uid))

        element = None
        if "{element_owner}" in text:
            if item["Element"] == "0":
                element_pattern = r"(Flame|Water|Wind|Light|Shadow)"

                if r := re.search(element_pattern, item["Name"]):
                    element = r[1]
                elif not (element := temp):
                    print("{}: element_owner loss".format(uid))

                item["ElementalType"] = ELEMENT_TYPE.index(element)
            else:
                element = ELEMENT_TYPE[int(item["Element"])]

        item["Name"] = text.format(
            ability_shift0="",
            ability_val0=item["AbilityType1UpValue"],
            element_owner=element,
            ability_cond0=item.pop("ConditionValue"),
        )

    def set_image(self):
        image = self.item.pop("AbilityIconName")
        self.item["Image"] = image.replace("Icon_Ability_", "")

    def set_ability(self):
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
