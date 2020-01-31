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
        self.attach_data("names")
        self.attach_data("abilities")

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
        self.set_prop()
        self.set_name()
        self.set_image()
        self.set_stat()
        self.set_ability()
        self.set_might()

    def set_name(self):
        name = self.get_value("names", self.item["Name"])
        self.item["Name"] = name
        self.item["Abbr"] = "".join([c[0] for c in name["en"].split()])

    def set_ability(self):
        item = self.item
        item["Might"] = [[0 for i in range(4)] for j in range(4)]
        icon_list = []

        for i in range(1, 4):
            icon = None
            for j in range(1, 4):
                if (key := "Abilities{}{}".format(i, j)) not in item:
                    continue

                uid = item.pop(key)
                if ability := self.get_value("abilities", uid):
                    item["Might"][i][j] = ability["Might"]

                    icon = {
                        "Name": ability["Name"],
                        "Image": ability["Image"],
                    }

                    self.set_type(key, ability)

            if icon:
                icon_list.append(icon)

        if icon_list:
            item["Icon"] = icon_list

    def set_image(self):
        pass

    def set_might(self):
        pass

    def set_prop(self):
        pass

    def set_stat(self):
        pass

    def set_type(self, key, ability):
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
        item = self.item

        if item:
            item["Name"] = self.get_value("labels", item["Name"])
            item["Details"] = self.get_value("labels", item["Details"])

        return item and item["Name"] and item["Details"]

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


class Skill(Common):
    def __init__(self):
        columns = (
            "Id",
            "Name",
            "SkillLv2IconName",
        )

        super().__init__("skills", columns)
        self.attach_data("labels")

    def set_name(self):
        self.item["Name"] = self.get_value("labels", self.item["Name"])

    def set_image(self):
        self.item["Image"] = self.item.pop("SkillLv2IconName")

    def set_ability(self):
        pass


class Adventurer(Common):
    def __init__(self):
        columns = (
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

        super().__init__("adventurer", columns)
        self.attach_data("abilities")
        self.__mc_require = {
            "5": {
                "Abilities11": 10,
                "Abilities21": 10,
                "Abilities31": 20,
                "Abilities12": 30,
                "Abilities22": 40,
                "Abilities32": 45,
                "Abilities13": 70,
                "Abilities23": 70,
                "Abilities33": 70,
            },
            "rest": {
                "Abilities11": 10,
                "Abilities21": 10,
                "Abilities12": 30,
                "Abilities22": 40,
                "Abilities31": 45,
                "Abilities13": 70,
                "Abilities23": 70,
                "Abilities32": 70,
            },
        }

    def eligible(self):
        return super().eligible() and self.item.pop("IsPlayable") == "1"

    def modify(self):
        super().modify()
        self.set_mc()
        self.item["DefCoef"] = int(self.item["DefCoef"])

    def set_prop(self):
        item = self.item
        item["Element"] = ELEMENT_TYPE[int(item.pop("ElementalType"))]
        item["Weapon"] = WEAPON_TYPE[int(item.pop("WeaponType"))]
        item["LimitBreak"] = item.pop("MaxLimitBreakCount")

    def set_image(self):
        item = self.item
        base_id = item.pop("BaseId")
        variation = int(item.pop("VariationId"))
        item["Image"] = "{}_{:02d}".format(base_id, variation)

    def set_mc(self):
        item = self.item

        # MC50: McFullBonusHp5,  MC70: PlusHp5
        for k in ("Hp", "Atk"):
            mc5 = "Plus{}5".format(k)
            item["Plus{}6".format(k)] = item[mc5]
            item[mc5] = item.pop("McFullBonus{}5".format(k))

        # sum mc bonus
        item["McBonus"] = []
        total = {"Hp": 0, "Atk": 0}
        for i in range(7):
            for k in ("Hp", "Atk"):
                total[k] += int(item.pop("Plus{}{}".format(k, i)))

            item["McBonus"].append([total["Hp"], total["Atk"]])

    def set_might(self):
        item = self.item

        if item["Rarity"] == "5" or item["Id"] == "10140101":
            rarity = "5"
        else:
            rarity = "rest"

        might = []
        for mc in (10, 20, 30, 40, 45, 50, 70):
            v = 0
            for i in range(1, 4):
                for j in reversed(range(1, 4)):
                    if item["Might"][i][j] == 0:
                        continue

                    if mc >= self.__mc_require[rarity]["Abilities{}{}".format(i, j)]:
                        v += item["Might"][i][j]
                        break

            might.append(v)

        item["Might"] = might

    def set_stat(self):
        item = self.item

        item["Max"] = [int(item.pop("MaxHp")), int(item.pop("MaxAtk"))]
        item["AddMax1"] = [int(item.pop("AddMaxHp1")), int(item.pop("AddMaxAtk1"))]

        item["Min"] = []
        for i in range(3, 6):
            temp = []
            for k in ("Hp", "Atk"):
                key = "Min{}{}".format(k, i)
                temp.append(int(item.pop(key)))
            item["Min"].append(temp)

    def set_type(self, key, ability):
        item = self.item
        for t in ability.get("Type", []):
            rarity = "5" if item["Rarity"] == "5" else "rest"
            mc = self.__mc_require[rarity][key]

            ability_key = t["Key"]
            if ability_key not in item:
                item[ability_key] = []

            item[ability_key].append({"MC": mc, "Value": t["Value"]})


class Weapon(Common):
    def __init__(self):
        columns = (
            "Id",
            "Name",
            "Type",
            "Rarity",
            "ElementalType",
            "MinHp",
            "MaxHp",
            "MinAtk",
            "MaxAtk",
            "BaseId",
            "VariationId",
            "FormId",
            "Skill",
            "Abilities11",
            "Abilities21",
            "IsPlayable",
        )

        super().__init__("weapon", columns)

    def eligible(self):
        item = self.item
        return item and item.pop("IsPlayable") == "1" and int(item["Rarity"]) >= 3

    def modify(self):
        super().modify()
        self.set_skill()

    def set_prop(self):
        item = self.item
        if (element := int(item.pop("ElementalType"))) == 99:
            element = 0

        item["Element"] = ELEMENT_TYPE[element]
        item["Weapon"] = WEAPON_TYPE[int(item.pop("Type"))]

    def set_image(self):
        item = self.item
        base_id = item.pop("BaseId")
        variation = int(item.pop("VariationId"))
        form_id = item.pop("FormId")
        item["Image"] = "{}_{:02d}_{}".format(base_id, variation, form_id)

    def set_might(self):
        # weapon has only 1 level of ability
        might = self.item.pop("Might")

        if m := (might[1][1] + might[2][1]):
            self.item["Might"] = m

    def set_stat(self):
        item = self.item
        item["Max"] = [int(item.pop("MaxHp")), int(item.pop("MaxAtk"))]
        item["Min"] = [int(item.pop("MinHp")), int(item.pop("MinAtk"))]

    def set_skill(self):
        item = self.item
        if skill := self.get_value("skills", item["Skill"]):
            del skill["Id"]
            item["Skill"] = skill
        else:
            del item["Skill"]

    def set_type(self, key, ability):
        for t in ability.get("Type", []):
            self.item[t["Key"]] = t["Value"]


class Dragon(Common):
    def __init__(self):
        columns = (
            "Id",
            "Name",
            "Rarity",
            "ElementalType",
            "BaseId",
            "VariationId",
            "MinHp",
            "MaxHp",
            "MinAtk",
            "MaxAtk",
            "Abilities11",
            "Abilities12",
            "Abilities21",
            "Abilities22",
            "IsPlayable",
        )

        super().__init__("dragon", columns)

    def eligible(self):
        item = self.item
        return item and item.pop("IsPlayable") == "1" and item["Id"] != "20050507"

    def set_image(self):
        item = self.item
        base_id = item.pop("BaseId")
        variation = int(item.pop("VariationId"))
        item["Image"] = "{}_{:02d}".format(base_id, variation)

    def set_type(self, key, ability):
        pass


if __name__ == "__main__":
    pass
