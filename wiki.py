import requests

from utils import read_json, save_json

MAX = 500
WIKI = "https://dragalialost.gamepedia.com"
API = "{}/api.php?format=json&action".format(WIKI)


def get_data(table, fields, group):
    offset = 0
    data = []
    while offset % MAX == 0:
        print("Retrieve data: {}, {}".format(table, offset))
        query = "tables={}&fields={}&group_by={}&offset={}".format(
            table, fields, group, offset
        )
        url = "{}=cargoquery&limit={}&{}".format(API, MAX, query)
        r = requests.get(url).json()

        try:
            new_trieve = r["cargoquery"]
            data += new_trieve
            offset += len(new_trieve)
        except:
            print(r)
            raise Exception

    print("Retrieve data {} done.".format(table))
    return data


def get_abilities():
    ability_val = read_json("ability_val")
    ability_details = {}

    table = "Abilities"
    fields = "Id,Name,Details,AbilityIconName,PartyPowerWeight,AbilityLimitedGroupId1"
    group = "Id"

    raw_data = get_data(table, fields, group)

    for i in raw_data:
        item = i["title"]
        uid = item["Id"]

        if uid in ability_val:
            ability_details[uid] = item["Details"]

    save_json("ability_val_details", ability_details)


if __name__ == "__main__":
    get_abilities()
