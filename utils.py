import json
from pathlib import Path


ROOT_PATH = Path("/home/jl/Documents/dragalia-lost")
SCRIPT_PATH = Path("/home/jl/Documents/script")
EXPORTS = "z_files"


def mono_file(file_name):
    files = {
        "en": "TextLabel",
        "ja": "TextLabelJP",
        "zh": "TextLabelZH",
        "abilities": "AbilityData",
        "skills": "SkillData",
        "adventurer": "CharaData",
        "weapon": "WeaponData",
        "dragon": "DragonData",
        "wyrmprint": "AmuletData",
        "facility": "FortPlantDetail",
    }

    return SCRIPT_PATH / "MonoBehaviour" / "{}.txt".format(files[file_name])


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
    print("save file: {}".format(path))


if __name__ == "__main__":
    pass
