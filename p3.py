import re

from p2 import P2
from utils import ELEMENT_TYPE, WEAPON_TYPE, save_json, save_content


class P3(P2):
    def __init__(self, key, columns):
        super().__init__(key, columns)
        self.attach_data("names")
        self.attach_data("abilities")

    def modify(self):
        super().modify()
        self.set_stat()
        self.set_ability()
        self.set_might()

    def set_name(self):
        name = self.get_value("names", self.item["Name"])
        self.item["Name"] = name
        self.item["Abbr"] = "".join([c[0] for c in name["en"].split()]).upper()

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

                if uid == "210001706":
                    print(item["Id"])

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

    def set_stat(self):
        pass

    def set_type(self, key, ability):
        pass

    def set_might(self):
        pass

    def finalize(self):
        save_json(self.key, self.data)
        save_content(self.key, self.data)


class Adventurer(P3):
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
        item = self.item

        if item:
            if item.pop("IsPlayable") == "1":
                return True
            elif item["Id"] in ("10130103", "10140401"):
                return True

        return False

    def modify(self):
        super().modify()
        self.set_mc()

    def set_prop(self):
        item = self.item
        item["DefCoef"] = int(item["DefCoef"])
        item["Element"] = ELEMENT_TYPE[int(item.pop("ElementalType"))]
        item["Weapon"] = WEAPON_TYPE[int(item.pop("WeaponType"))]
        item["LimitBreak"] = item.pop("MaxLimitBreakCount")

    def set_image(self):
        item = self.item
        base_id = item.pop("BaseId")
        variation = int(item.pop("VariationId"))
        item["Image"] = "{}_{:02d}".format(base_id, variation)

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

        # MC70: +200
        might[6] += 200

        item["Might"] = might

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


class Weapon(P3):
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
        self.attach_data("skills")

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

    def set_stat(self):
        item = self.item
        item["Max"] = [int(item.pop("MaxHp")), int(item.pop("MaxAtk"))]
        item["Min"] = [int(item.pop("MinHp")), int(item.pop("MinAtk"))]

    def set_type(self, key, ability):
        for t in ability.get("Type", []):
            self.item[t["Key"]] = t["Value"]

    def set_might(self):
        # weapon has only 1 level of ability
        might = self.item.pop("Might")

        if m := (might[1][1] + might[2][1]):
            self.item["Might"] = m

    def set_skill(self):
        item = self.item
        if skill := self.get_value("skills", item["Skill"]):
            del skill["Id"]
            item["Skill"] = skill
        else:
            del item["Skill"]


class Dragon(P3):
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

    def set_prop(self):
        item = self.item
        item["Element"] = ELEMENT_TYPE[int(item.pop("ElementalType"))]

    def set_image(self):
        item = self.item
        base_id = item.pop("BaseId")
        variation = int(item.pop("VariationId"))
        item["Image"] = "{}_{:02d}".format(base_id, variation)

    def set_stat(self):
        item = self.item
        item["Max"] = [int(item.pop("MaxHp")), int(item.pop("MaxAtk"))]
        item["Min"] = [int(item.pop("MinHp")), int(item.pop("MinAtk"))]

    def set_type(self, key, ability):
        item = self.item

        for t in ability.get("Type", []):
            if (ability_key := t["Key"]) not in item:
                item[ability_key] = []

            temp = t.copy()
            del temp["Key"]

            if ability_key != "IncRES":
                temp["Element"] = ability["Element"]

            item[ability_key].append(temp)

    def set_might(self):
        might = self.item["Might"]
        v1 = 0
        v2 = 0

        for i in range(1, 3):
            v1 += might[i][1]
            v2 += might[i][2]

        self.item["Might"] = [v1, v2]


class Wyrmprint(P3):
    def __init__(self):
        columns = (
            "Id",
            "Name",
            "Rarity",
            "BaseId",
            "MinHp",
            "MaxHp",
            "MinAtk",
            "MaxAtk",
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

        super().__init__("wyrmprint", columns)

    def eligible(self):
        item = self.item
        return item and item.pop("IsPlayable") == "1" and int(item["Rarity"]) >= 3

    def set_image(self):
        self.item["Image"] = self.item.pop("BaseId")

    def set_stat(self):
        item = self.item
        item["Max"] = [int(item.pop("MaxHp")), int(item.pop("MaxAtk"))]
        item["Min"] = [int(item.pop("MinHp")), int(item.pop("MinAtk"))]

    def set_type(self, key, ability):
        item = self.item

        for t in ability.get("Type", []):
            if (ability_key := t["Key"]) not in item:
                item[ability_key] = []

            if ability_key == "IncRES":
                item["ResEle"] = t["ResEle"]
            elif ability_key == "IncDIS":
                item["Enemy"] = t["Enemy"]

            item[ability_key].append(t["Value"])

    def set_might(self):
        might = self.item["Might"]
        v1 = 0
        v2 = 0
        v3 = 0

        for i in range(1, 4):
            v1 += might[i][1]
            v2 += might[i][2]
            v3 += might[i][3]

        self.item["Might"] = [v1, v2, v3]

