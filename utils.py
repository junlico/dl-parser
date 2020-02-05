import json
import re
import shutil
import time
from pathlib import Path
from zipfile import ZipFile, ZipInfo

from rarfile import RarFile, RarInfo

from secret import (
    APP_PATH,
    DECIPHER_PATH,
    DOWNLOAD_PATH,
    EXPORTS,
    IMAGE_PATH,
    QQ_RECV,
    SCRIPT_PATH,
)

ELEMENT_TYPE = [None, "Flame", "Water", "Wind", "Light", "Shadow"]
WEAPON_TYPE = [None, "Sword", "Blade", "Dagger", "Axe", "Lance", "Bow", "Wand", "Staff"]


ST_CTIME = lambda p: p.stat().st_ctime


def extract_file(lib, f, path):
    """ Extract File from compressed folder """

    try:
        if isinstance(f, ZipInfo):
            lib.extract(f, path)
            path = path / f.filename
        elif isinstance(f, RarInfo):
            lib.extract(f)
            path.parent.mkdir(parents=True, exist_ok=True)
            Path(SCRIPT_PATH / f.filename).rename(path)
    except:
        code = "Failed"
    else:
        code = "Succeed"

    print("{}: {}".format(code, path))


def get_images():
    """ Extract Image from .rar """

    files = {
        "chara": "adventurer",
        "weapon": "weapon",
        "dragon": "dragon",
        "amulet": "wyrmprint",
        "skill": "skills",
        "ability": "abilities",
    }

    path = max(QQ_RECV.glob("*.rar"), key=ST_CTIME)

    p = re.compile(r"icon/({})/l/.*/(\w+)_rgba8.png".format("|".join(files.keys())))

    try:
        shutil.rmtree("./images")
        Path("./images").mkdir()
        with RarFile(path) as rf:
            for f in rf.infolist():
                if m := p.search(f.filename):
                    save_path = IMAGE_PATH / files[m[1]] / "{}.png".format(m[2])
                    extract_file(rf, f, save_path)
    except FileNotFoundError:
        print("File Not Found.")

    else:
        shutil.rmtree("./resources")


def get_files():

    files = {
        "AbilityData": "abilities",
        "AmuletData": "wyrmprint",
        "CharaData": "adventurer",
        "DragonData": "dragon",
        "FortPlantDetail": "facility",
        "SkillData": "skills",
        "TextLabel": "en",
        "TextLabelJP": "ja",
        "WeaponData": "weapon",
    }

    # update EN files
    en_path = max(DOWNLOAD_PATH.glob("*_Dump.zip"), key=ST_CTIME)
    p = re.compile(r"MonoBehaviour/({}).txt".format("|".join(files.keys())))

    try:
        # Make sure MonoBehaviour folder in zip files
        with ZipFile(en_path) as zf:
            for f in zf.infolist():
                if r := p.search(f.filename):
                    f.filename = "{}.txt".format(files[r[1]])
                    extract_file(zf, f, DECIPHER_PATH)
    except FileNotFoundError:
        raise Exception("EN Zip: Wrong path or not exists.")

    # update ZH TextLabel
    zh_path = max(QQ_RECV.glob("*.zip"), key=ST_CTIME)

    try:
        with ZipFile(zh_path) as zf:
            for f in zf.infolist():
                if "TextLabel.txt" in f.filename:
                    f.filename = "zh.txt"
                    extract_file(zf, f, DECIPHER_PATH)
                    break
    except FileNotFoundError:
        raise Exception("ZH Zip: Wrong path or not exists.")


def get_text_path(file_name):
    return DECIPHER_PATH / "{}.txt".format(file_name)


def get_json_path(folder, file_name):
    return SCRIPT_PATH / folder / "{}.json".format(file_name)


def read_json(file_name, folder=EXPORTS):
    path = get_json_path(folder, file_name)

    if path.is_file():
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    return {}


def save_json(file_name, data, folder=EXPORTS):
    path = get_json_path(folder, file_name)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("Save file: {}".format(path))


def save_content(file_name, data):
    path = APP_PATH / "src" / "data" / "content" / "{}.js".format(file_name)

    with path.open("w", encoding="utf-8") as f:
        f.write("const {} =\n".format(file_name))
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write(";\n\nexport default {};\n".format(file_name))

    print("save file: {}".format(path))


if __name__ == "__main__":
    get_files()
    get_images()
    pass
