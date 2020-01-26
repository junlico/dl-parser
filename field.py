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
        if getattr(Base2, key, None):
            return

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

    def eligible(self):
        return self.item

    def register_item(self):
        if not self.eligible():
            self.item = {}
            return

        self.modify_item()
        self.data[self.item["Id"]] = self.item
        self.item = {}

    def modify_item(self):
        self.set_image()
        self.__set_ability()

    def finalize(self):
        save_json(self.file_name, self.data)

    def get_pattern(self):
        return r"_(\w+) = \"?(-?\w*)\"?"

    def set_image(self):
        pass

    def __set_ability(self):
        item = self.item
        item["icon"] = []
        might = [[0] * 4 for _ in range(4)]

        for i in [1, 2, 3]:
            icon = None
            for j in [3, 2, 1]:
                if (key := "Abilities{}{}".format(i, j)) not in item:
                    continue

                uid = item.pop(key)

                if ability := self.get_value("abilities", uid):
                    might[i][j] = ability["PartyPowerWeight"]

                    if not icon:
                        icon = {
                            "title": ability["Name"],
                            "image": ability["Image"],
                        }

            if icon:
                item["icon"].append(icon)


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

        self.__enemy_dict = {
            "3": "hms",
            "5": "hmc",
            "7": "hbh",
            "9": "hjp",
            "11": "hzd",
        }

        self.save_ability_val = False
        self.attach_data("labels")
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
        self.__set_icon()
        self.__set_type()

    def finalize(self):
        if self.save_ability_val:
            save_json("ability_val", getattr(self, "ability_val"))

        setattr(Base2, "abilities", self.data)
        super().finalize()

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

    def __set_icon(self):
        image = self.item.pop("AbilityIconName")
        self.item["Image"] = image.replace("Icon_Ability_", "")

    def __set_type(self):
        item = self.item
        type_list = []

        for i in range(1, 4):
            if (key1 := item["AbilityType{}".format(i)]) == "0":
                continue

            key2 = item["VariousId{}a".format(i)]
            value = item["AbilityType{}UpValue".format(i)]

            ability_type = "{}_{}".format(key1, key2)
            type_item = None
            if ability_type == "1_1":
                type_item = {"key": "incHP"}
            elif ability_type == "1_2":
                type_item = {"key": "incSTR"}
            elif ability_type == "1_3":
                type_item = {"key": "incDEF"}
            elif key1 == "28":
                type_item = {"key": "incRES", "resEle": ELEMENT_TYPE[int(key2)]}
            elif key1 == "29" and (enemy := self.__enemy_dict.get(key2, None)):
                type_item = {"key": "incDIS", "enemy": enemy}

            if type_item:
                type_item["value"] = value
                type_list.append(type_item)

        if type_list:
            item["Type"] = type_list


class Adventurer(Base2):
    def __init__(self):
        str_props = (
            "Id",
            "Name",
            "BaseId",
            "Rarity",
            "Abilities11",
            "Abilities12",
            "Abilities13",
            "Abilities21",
            "Abilities22",
            "Abilities23",
            "Abilities31",
            "Abilities32",
            "Abilities33",
            "IsPlayable",
        )
        int_props = (
            "WeaponType",
            "ElementalType",
            "MaxLimitBreakCount",
            "VariationId",
            "MinHp3",
            "MinHp4",
            "MinHp5",
            "MaxHp",
            "AddMaxHp1",
            "PlusHp0",
            "PlusHp1",
            "PlusHp2",
            "PlusHp3",
            "PlusHp4",
            "PlusHp5",
            "McFullBonusHp5",
            "MinAtk3",
            "MinAtk4",
            "MinAtk5",
            "MaxAtk",
            "AddMaxAtk1",
            "PlusAtk0",
            "PlusAtk1",
            "PlusAtk2",
            "PlusAtk3",
            "PlusAtk4",
            "PlusAtk5",
            "McFullBonusAtk5",
            "DefCoef",
        )
        super().__init__("adventurer", str_props, int_props)
        self.attach_data("abilities")

    def eligible(self):
        return self.item and self.item.pop("IsPlayable") == "1"

    def modify_item(self):
        super().modify_item()

    def set_image(self):
        item = self.item
        base_id = item.pop("BaseId")
        variation = item.pop("VariationId")
        item["image"] = "{}_{:02d}".format(base_id, variation)


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
