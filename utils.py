import json
import re
import zipfile
from pathlib import Path
from zipfile import ZipFile, is_zipfile

APP_PATH = Path("/home/jl/Documents/dragalia-lost")
DOWNLOAD_PATH = Path("/home/jl/Downloads")
SCRIPT_PATH = Path("/home/jl/Documents/dl-parser")
DECIPHER_PATH = SCRIPT_PATH / "DecipherFiles"
EXPORTS = "Exports"


def update_text_file():
    def extract_file(z, f):
        z.extract(f, DECIPHER_PATH)
        print("Update file: {}/{}".format(DECIPHER_PATH, f.filename))

    # update EN files
    en_zip_name = input("EN Zip Name in Downloads: ")
    en_zip_path = DOWNLOAD_PATH / "{}.zip".format(en_zip_name)

    if not is_zipfile(en_zip_path):
        raise Exception("EN Zip: Wrong path or not exists.")

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

    # Make sure MonoBehaviour folder in zip files
    pattern = r"MonoBehaviour/({}).txt".format("|".join(files.keys()))
    with ZipFile(en_zip_path) as z:
        for f in z.infolist():
            if r := re.search(pattern, f.filename):
                f.filename = "{}.txt".format(files[r[1]])
                extract_file(z, f)

    # update ZH TextLabel
    zh_zip_path = DOWNLOAD_PATH / "qq-files" / "2236526965" / "file_recv" / "master.zip"

    if not is_zipfile(zh_zip_path):
        raise Exception("ZH Zip: Wrong path or not exists.")

    with ZipFile(zh_zip_path) as z:
        for f in z.infolist():
            if f.filename == "master/TextLabel.txt":
                f.filename = "zh.txt"
                extract_file(z, f)
                break


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
    update_text_file()
    pass
