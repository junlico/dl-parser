import json
import re
import urllib.request
from pathlib import Path

import requests

from utils import read_json, save_json, APP_PATH

MAX = 500
WIKI = "https://dragalialost.gamepedia.com"
API = "{}/api.php?format=json&action".format(WIKI)

IMAGE_PATH = APP_PATH / "public" / "images"


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


def get_image(queue):
    for key in queue:
        path = IMAGE_PATH / key
        files = [f.name for f in path.rglob("*.png")]
        items = read_json(key)
        image_list = []
        for item in items.values():
            if item["Image"] and format_image_name(item, key) not in files:
                image_list.append(item["Image"])

    if image_list:
        download_images(key, image_list)


def format_image_name(item, key):
    image = item["Image"]
    if key == "adventurer":
        image = "{}_r0{}".format(image, item["Rarity"])
    elif key == "wyrmprint":
        image = "{}_01".format(image)
    elif key == "abilities":
        image = "Icon_Ability_{}".format(image)

    return "{}.png".format(image)


def download_images(key, image_list=[]):
    pattern = {
        "adventurer": r"\d{6}_\d{2,3}_r0[345].png",
        "dragon": r"\d{6}_01.png",
        "weapon": r"\d{6}_01_\d{5}.png",
        "wyrmprint": r"\d{6}_0[12].png",
        "material": r"\d{9}.png",
        "facility": r"TW02_(\d{6})_IMG_0(\d)",
        "abilities": r"^Icon_Ability_\d+.png",
        "skills": r"^Icon_Skill_\d+.png",
    }

    start = {
        "abilities": "4_Unbind.png",
        "adventurer": "0_Unbind.png",
        "dragon": "1_Unbind.png",
        "facility": "TW02_100101_IMG_01.png",
        "material": "0_Unbind.png",
        "skills": "4_Unbind.png",
        "weapon": "2_Unbind.png",
        "wyrmprint": "3_Unbind.png",
    }

    stop = {
        "abilities": "U",
        "adventurer": "2",
        "dragon": "3",
        "facility": "U",
        "material": "4",
        "skills": "U",
        "weapon": "4",
        "wyrmprint": "A",
    }

    flag = True
    download = {}
    aifrom = start[key]

    while flag:
        url = "{}=query&list=allimages&aifrom={}&ailimit=max".format(API, aifrom)
        response = requests.get(url).json()
        try:
            data = response["query"]["allimages"]

            for i in data:
                name = i["name"]
                if name[0] == stop[key]:
                    flag = False
                    break

                r = re.search(pattern[key], name)
                if r and any(ele in name for ele in image_list):
                    download[name] = i["url"]

            con = response.get("continue", None)
            if con and con.get("aicontinue", None):
                aifrom = con["aicontinue"]
            else:
                flag = False
                break

        except:
            raise Exception

    print("Start downloading images...")
    for k, v in download.items():
        path = IMAGE_PATH / key / k
        urllib.request.urlretrieve(v, path)
        print("download image: {}".format(path))


if __name__ == "__main__":
    get_image(["abilities", "skills", "adventurer", "weapon", "dragon", "wyrmprint"])
    pass
