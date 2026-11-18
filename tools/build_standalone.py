# Made by Claude Ai & Relic Hunter
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "1.0.2"
MO2 = sys.argv[1] if len(sys.argv) > 1 else r"D:\Modding\MO2-Dragonwilds"
TOP = "Dragonwilds MO2"
OUT = os.path.join(ROOT, "release", f"Dragonwilds-MO2-Standalone-{VERSION}.zip")
SKIP_DIRS = {"crashdumps", "downloads", "logs", "mods", "overwrite", "profiles", "stock game", "webcache", "__pycache__"}
SKIP_FILES = {
    "modorganizer.ini", "splash.png", "dragonwilds mo2 support - readme.txt", "portable.txt",
    "categories.dat", "categories.dat.mo2default", "nexuscatmap.dat",
}
GAMES = "plugins/basic_games/games/"
LEFT_OUT = ("plugins/installer_omod/", "plugins/installer_fomod_csharp.dll")
OWNED = (
    "stylesheets/transparent-style/dragonwilds/",
    "stylesheets/transparent-style-dragonwilds.qss",
    "plugins/basic_games/games/game_rsdragonwilds",
    "plugins/basic_games/games/rsdragonwilds_",
)
MO2_RELEASED = 1735689600

INI = """[General]
gameName=RuneScape: Dragonwilds
selected_profile=@ByteArray(Default)
first_start=false
version=2.5.2

[Settings]
style=Transparent-Style-Dragonwilds.qss
log_level=1
profile_local_inis=false
"""


NEXUS_CATEGORIES = [
    (9, "Animations"), (10, "Armour"), (8, "Audio"), (6, "Buildings"), (11, "Crafting"), (5, "Gameplay"),
    (12, "Items"), (2, "Miscellaneous"), (3, "Save File"), (13, "Skills"), (4, "Spells"),
    (7, "User Interface"), (16, "Utilities"), (15, "Visuals"), (14, "Weapons"),
]


def category_files():
    rows = sorted(NEXUS_CATEGORIES, key=lambda c: c[1])
    cats = "".join(f"{200 + n}|{name}|0\n" for n, name in rows) + "300|Master Files|216\n"
    nexus_map = "".join(f"{200 + n}|{name}|{n}\n" for n, name in rows)
    return cats, nexus_map


def program_files():
    for base, dirs, names in os.walk(MO2):
        rel = os.path.relpath(base, MO2)
        dirs[:] = [d for d in dirs if d.casefold() not in SKIP_DIRS]
        for name in names:
            if rel == "." and name.casefold() in SKIP_FILES:
                continue
            if name.endswith(".pyc"):
                continue
            arc = os.path.normpath(os.path.join(rel, name)).replace("\\", "/")
            if arc.casefold().startswith(OWNED) or arc.casefold().startswith(LEFT_OUT):
                continue
            path = os.path.join(base, name)
            if os.path.getmtime(path) > MO2_RELEASED:
                print("skipped (not part of MO2 2.5.2):", arc)
                continue
            yield path, arc


def our_files():
    plugin = os.path.join(ROOT, "plugin")
    for name in ("game_rsdragonwilds.py", "rsdragonwilds_ue4ss_boot.dll", "rsdragonwilds_discord.png", "rsdragonwilds_notes.json"):
        yield os.path.join(plugin, name), GAMES + name
    sheets = os.path.join(ROOT, "theme", "stylesheets")
    for base, _, names in os.walk(sheets):
        for name in names:
            path = os.path.join(base, name)
            yield path, "stylesheets/" + os.path.relpath(path, sheets).replace("\\", "/")
    splash = os.path.join(ROOT, "theme", "splash.png")
    yield splash, "stylesheets/Transparent-Style/Dragonwilds/splash.png"
    yield splash, "splash.png"
    yield os.path.join(ROOT, "pack", "README-standalone.txt"), "README - Dragonwilds MO2.txt"
    yield os.path.join(ROOT, "pack", "THIRD-PARTY.txt"), "Dragonwilds - THIRD-PARTY.txt"
    yield os.path.join(ROOT, "tools", "build_bootstrap_dll.py"), "Dragonwilds - Source/build_bootstrap_dll.py"


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    ours = list(our_files())
    taken = {arc.casefold() for _, arc in ours}
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for src, arc in program_files():
            if arc.casefold() in taken:
                continue
            z.write(src, f"{TOP}/{arc}")
            count += 1
        for src, arc in ours:
            z.write(src, f"{TOP}/{arc}")
            count += 1
        z.writestr(f"{TOP}/ModOrganizer.ini", INI)
        z.writestr(f"{TOP}/portable.txt", "\n")
        cats, nexus_map = category_files()
        z.writestr(f"{TOP}/categories.dat", cats)
        z.writestr(f"{TOP}/nexuscatmap.dat", nexus_map)
        count += 4
    print(f"{OUT} ({count} files, {os.path.getsize(OUT) / 1048576:.1f} MB)")


if __name__ == "__main__":
    main()
