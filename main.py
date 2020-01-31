import re

from content import Ability, Adventurer, Dragon, Skill, Weapon, Wyrmprint
from label import Label, Name
from utils import get_text_path, save_json


def parse(obj):
    for file_name in obj.files:
        if obj.key == "names":
            obj.lang = file_name

        path = get_text_path(file_name)

        with path.open(encoding="utf-8") as f:
            start = False
            for line in f:
                if "Element data" in line:
                    start = True
                    obj.register()
                elif start:
                    if "_Id = 0" in line or '_Id = ""' in line:
                        break

                    obj.parse(line, f)

    obj.finalize()


if __name__ == "__main__":

    queue = (
        Label(),
        Name(),
        Ability(),
        Skill(),
        Adventurer(),
        Weapon(),
        Dragon(),
        Wyrmprint(),
    )

    for obj in queue:
        parse(obj)
