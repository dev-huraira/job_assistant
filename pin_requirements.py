import re
from importlib.metadata import version

pinned = []
with open("requirements.txt", encoding="utf-8") as source:
    for line in source:
        requirement = line.strip()
        if not requirement or requirement.startswith("#"):
            continue
        name = re.split(r"[\[<>=!~]", requirement)[0]
        extras = requirement[len(name):].split("==")[0]
        pinned.append(f"{name}{extras}=={version(name)}")

with open("requirements.pinned.txt", "w", encoding="utf-8") as target:
    target.write("\n".join(pinned) + "\n")

print("\n".join(pinned))