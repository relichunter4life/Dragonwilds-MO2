# Made by Claude Ai & Relic Hunter
import glob
import importlib
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(os.path.dirname(HERE))
PLUGIN = os.path.join(os.path.dirname(HERE), "plugin", "game_rsdragonwilds.py")
MO2 = r"D:\Modding\MO2-Dragonwilds"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(MO2, "plugins", "plugin_python", "libs"))
os.add_dll_directory(os.path.join(MO2, "dlls"))
os.add_dll_directory(MO2)

import fake_mobase

mobase = fake_mobase.install()
pkg = tempfile.mkdtemp()
os.makedirs(os.path.join(pkg, "fakebg", "games"))
open(os.path.join(pkg, "fakebg", "__init__.py"), "w").close()
open(os.path.join(pkg, "fakebg", "games", "__init__.py"), "w").close()
with open(os.path.join(pkg, "fakebg", "basic_game.py"), "w") as f:
    f.write("class BasicGame:\n    def __init__(self, *a, **k):\n        pass\n")
os.makedirs(os.path.join(pkg, "fakebg", "basic_features"))
with open(os.path.join(pkg, "fakebg", "basic_features", "__init__.py"), "w") as f:
    f.write("class BasicLocalSavegames:\n    def __init__(self, *a, **k):\n        pass\n")
with open(os.path.join(pkg, "fakebg", "basic_features", "basic_save_game_info.py"), "w") as f:
    f.write("class BasicGameSaveGame:\n    def __init__(self, *a, **k):\n        pass\n")
shutil.copy(PLUGIN, os.path.join(pkg, "fakebg", "games", "game_rsdragonwilds.py"))
sys.path.insert(0, pkg)
plugin = importlib.import_module("fakebg.games.game_rsdragonwilds")
checker = plugin.DragonwildsModDataChecker()
content = plugin.DragonwildsDataContent()

UE = "Binaries/Win64/ue4ss/Mods/"
RS = UE + "RuneSchema/mods/"


def install(paths):
    root = fake_mobase.tree_from(paths)
    tree = root
    status = checker.dataLooksValid(tree)
    while status == "INVALID" and len(tree) == 1 and isinstance(list(tree)[0], fake_mobase.IFileTree):
        tree = list(tree)[0]
        status = checker.dataLooksValid(tree)
    if status == "FIXABLE":
        tree = checker.fix(tree)
        status = checker.dataLooksValid(tree)
    return status, tree


def sub_install(paths):
    root = fake_mobase.tree_from(paths)
    if len(root) == 1 and isinstance(list(root)[0], fake_mobase.IFileTree):
        tree = list(root)[0]
        if checker.dataLooksValid(tree) == "FIXABLE":
            checker.fix(tree)
            return checker.dataLooksValid(tree), tree
    return None, None


CASES = {
    "UE4SS core (Nexus)": (
        ["dwmapi.dll", "ue4ss/UE4SS.dll", "ue4ss/UE4SS-settings.ini", "ue4ss/Mods/mods.txt",
         "ue4ss/Mods/BPModLoaderMod/Scripts/main.lua", "ue4ss/Mods/shared/UEHelpers/UEHelpers.lua"],
        ["Binaries/Win64/ue4ss_loader.dll", "Binaries/Win64/ue4ss/UE4SS.dll", UE + "mods.txt",
         UE + "BPModLoaderMod/Scripts/main.lua"],
    ),
    "UE4SS core full game path": (
        ["RSDragonwilds/Binaries/Win64/dwmapi.dll", "RSDragonwilds/Binaries/Win64/ue4ss/UE4SS.dll"],
        ["Binaries/Win64/ue4ss_loader.dll", "Binaries/Win64/ue4ss/UE4SS.dll"],
    ),
    "RuneSchema framework (RuneSchema/)": (
        ["RuneSchema/dlls/main.dll", "RuneSchema/scripts/main.lua", "RuneSchema/enabled.txt",
         "RuneSchema/mods/AA_Example/assets/a.jsonc"],
        [UE + "RuneSchema/dlls/main.dll", RS + "AA_Example/assets/a.jsonc"],
    ),
    "RuneSchema framework (ue4ss/Mods/)": (
        ["ue4ss/Mods/RuneSchema/dlls/main.dll", "ue4ss/Mods/RuneSchema/settings/settings.ini"],
        [UE + "RuneSchema/dlls/main.dll"],
    ),
    "RuneSchema content recommended layout": (
        ["RuneSchema/mods/MyMod/mod.json", "RuneSchema/mods/MyMod/equipment/x.jsonc",
         "RuneSchema/mods/MyMod/paks/MyMod/MyMod.pak"],
        [RS + "MyMod/mod.json", RS + "MyMod/paks/MyMod/MyMod.pak"],
    ),
    "RuneSchema content folder at root": (
        ["MyMod/ID.txt", "MyMod/buildings/b.jsonc", "MyMod/paks/MyMod.pak"],
        [RS + "MyMod/ID.txt", RS + "MyMod/buildings/b.jsonc"],
    ),
    "Lua mod folder": (
        ["CapeEffects/README.txt", "CapeEffects/Scripts/main.lua", "CapeEffects/enabled.txt"],
        [UE + "CapeEffects/Scripts/main.lua", UE + "CapeEffects/enabled.txt"],
    ),
    "Lua mod in Mods/": (
        ["Mods/FastEatSleep/Scripts/main.lua"],
        [UE + "FastEatSleep/Scripts/main.lua"],
    ),
    "Lua mod in wrapper folder": (
        ["Lockpicking-5.11/ue4ss/Mods/Lockpicking/Scripts/main.lua",
         "Lockpicking-5.11/ue4ss/Mods/RuneSchema/mods/Lockpicking/npc/n.jsonc", "Lockpicking-5.11/README.txt"],
        [UE + "Lockpicking/Scripts/main.lua", RS + "Lockpicking/npc/n.jsonc"],
    ),
    "Pak files at root": (
        ["Better_Icons_P.pak", "Better_Icons_P.utoc", "Better_Icons_P.ucas", "readme.txt"],
        ["Content/Paks/~mods/Better_Icons_P.pak", "Content/Paks/~mods/Better_Icons_P.ucas"],
    ),
    "Pak folder": (
        ["MaxCape/MaxCape_P.pak", "MaxCape/MaxCape_P.utoc", "MaxCape/MaxCape_P.ucas"],
        ["Content/Paks/~mods/MaxCape/MaxCape_P.pak"],
    ),
    "ModMenu style full path": (
        ["RSDragonwilds/Content/Paks/~mods/ModMenu/ModMenu_P.pak",
         "RSDragonwilds/Binaries/Win64/ue4ss/Mods/ModMenu/Scripts/main.lua"],
        ["Content/Paks/~mods/ModMenu/ModMenu_P.pak", UE + "ModMenu/Scripts/main.lua"],
    ),
    "LogicMods at root": (
        ["LogicMods/MyBp.pak"],
        ["Content/Paks/LogicMods/MyBp.pak"],
    ),
    "Already correct": (
        ["Binaries/Win64/ue4ss/Mods/X/Scripts/main.lua", "Content/Paks/~mods/x.pak"],
        [UE + "X/Scripts/main.lua", "Content/Paks/~mods/x.pak"],
    ),
    "Correct but raw proxy": (
        ["Binaries/Win64/dwmapi.dll", "Binaries/Win64/ue4ss/UE4SS.dll"],
        ["Binaries/Win64/ue4ss_loader.dll", "Binaries/Win64/ue4ss/UE4SS.dll"],
    ),
}


def check(name, paths, expect, runner):
    status, tree = runner(paths)
    if tree is None:
        return None
    files = [f.replace("\\", "/") for f in tree.files()]
    missing = [e for e in expect if e not in files]
    ok = status == "VALID" and not missing and not any(f.lower().endswith("dwmapi.dll") for f in files)
    print(("PASS " if ok else "FAIL ") + name + f"  [{status}]")
    if not ok:
        for f in files:
            print("      have", f)
        for m in missing:
            print("      MISSING", m)
    return ok


results = []
for name, (paths, expect) in CASES.items():
    results.append(check(name, paths, expect, install))
    sub = check(name + " (installer gives the inner folder)", paths, expect, sub_install)
    if sub is not None:
        results.append(sub)

zips = []
for pattern in ("*.zip", "*/*.zip", "*/*/*.zip"):
    zips += glob.glob(os.path.join(WORK, pattern))
seen = set()
real_ok = real = 0
for z in sorted(zips, key=os.path.getmtime, reverse=True):
    base = os.path.basename(z).split("-")[0].lower()
    if base in seen:
        continue
    seen.add(base)
    try:
        names = [n for n in zipfile.ZipFile(z).namelist()]
    except Exception:
        continue
    status, tree = install(names)
    files = [f.replace("\\", "/") for f in tree.files()]
    good = status == "VALID" and all(
        f.startswith(("Binaries/Win64/ue4ss/", "Binaries/Win64/ue4ss_loader.dll", "Content/Paks/"))
        or "/" not in f
        for f in files
    )
    real += 1
    real_ok += good
    tops = sorted({"/".join(f.split("/")[:6]) for f in files if "/" in f})[:4]
    print(("ZIP OK   " if good else "ZIP BAD  ") + os.path.relpath(z, WORK) + f" [{status}] " + " | ".join(tops))

print()
print(f"layout cases: {sum(1 for r in results if r)}/{len(results)} passed; real zips: {real_ok}/{real} installed cleanly")
tree = fake_mobase.tree_from([UE + "RuneSchema/dlls/main.dll", RS + "A/assets/x.jsonc", UE + "Lua/Scripts/main.lua",
                              "Binaries/Win64/ue4ss_loader.dll", "Content/Paks/~mods/a.pak", "Content/Paks/LogicMods/b.pak"])
print("content ids:", content.getContentsFor(tree))

from pathlib import Path

detect_ok = 0
detect_total = 0
for z in glob.glob(os.path.join(MO2, "downloads", "*.zip")):
    detect_total += 1
    detect_ok += plugin.zip_is_dragonwilds(Path(z)) is True
foreign = os.path.join(pkg, "OtherGame-123-1-0-1700000000.zip")
with zipfile.ZipFile(foreign, "w") as zf:
    zf.writestr("SomeMod/enabled.txt", "")
    zf.writestr("SomeMod/Scripts/main.lua", "RegisterKeyBind(Key.F5, function() print('palworld') end)")
    zf.writestr("~mods/Other_P.pak", b"../../../Pal/Content/" + bytes(200))
detect_total += 1
detect_ok += plugin.zip_is_dragonwilds(Path(foreign)) is False
for referrer, expected in (
    ("https://www.curseforge.com/runescape-dragonwilds/mods/elemental-totems/files/1", "curseforge"),
    ("https://www.nexusmods.com/", "nexus"),
    ("https://quaternius.itch.io/x", ""),
):
    probe = os.path.join(pkg, "probe.zip")
    open(probe, "wb").close()
    with open(probe + ":Zone.Identifier", "w") as zone:
        zone.write("[ZoneTransfer]\nZoneId=3\nReferrerUrl=" + referrer + "\n")
    origin, page = plugin.download_origin(Path(probe))
    detect_total += 1
    detect_ok += origin == expected and (expected != "curseforge" or page.endswith("/mods/elemental-totems"))
print(f"download detection: {detect_ok}/{detect_total} correct")
shutil.rmtree(pkg, ignore_errors=True)
