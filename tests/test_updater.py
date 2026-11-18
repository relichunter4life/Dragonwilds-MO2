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
import io
from pathlib import Path

SUPPORT = Path(HERE).parent / "release"
results = []


def check(name, ok):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name)


def zip_bytes(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


check("version order", plugin.version_tuple("v1.0.10") > plugin.version_tuple("1.0.9") > plugin.version_tuple("1.0"))
base = plugin.GITHUB_DOWNLOAD + "v1.0.2/"
release = {"tag_name": "v1.0.2", "draft": False, "prerelease": False, "assets": [
    {"name": "Dragonwilds-MO2-Standalone-1.0.2.zip", "browser_download_url": base + "Dragonwilds-MO2-Standalone-1.0.2.zip", "size": 200000000},
    {"name": "Dragonwilds-MO2-Support-1.0.2.zip", "browser_download_url": base + "Dragonwilds-MO2-Support-1.0.2.zip", "size": 2000000},
]}
check("picks the Support zip", plugin.update_asset(release) == ("1.0.2", base + "Dragonwilds-MO2-Support-1.0.2.zip", 2000000))
check("ignores drafts", plugin.update_asset(dict(release, draft=True)) is None)
check("ignores prereleases", plugin.update_asset(dict(release, prerelease=True)) is None)
bad_host = dict(release, assets=[dict(release["assets"][1], browser_download_url="https://evil.example/Dragonwilds-MO2-Support-1.0.2.zip")])
check("refuses other hosts", plugin.update_asset(bad_host) is None)
wrong_ver = dict(release, assets=[dict(release["assets"][1], name="Dragonwilds-MO2-Support-1.0.1.zip")])
check("refuses version mismatch", plugin.update_asset(wrong_ver) is None)

good = {plugin.UPDATE_PLUGIN: b"new plugin", "stylesheets/x.qss": b"qss", "Dragonwilds MO2 Support - README.txt": b"r"}
for label, extra in [("path traversal", {"plugins/basic_games/games/../../../evil.py": b"x"}),
                     ("absolute path", {"/evil.py": b"x"}),
                     ("drive path", {"C:/evil.py": b"x"}),
                     ("unknown folder", {"mods/evil.txt": b"x"}),
                     ("exe in root", {"ModOrganizer.exe": b"x"})]:
    files = dict(good, **extra)
    with zipfile.ZipFile(io.BytesIO(zip_bytes(files))) as z:
        check("rejects " + label, plugin.update_members(z) is None)
with zipfile.ZipFile(io.BytesIO(zip_bytes({"stylesheets/x.qss": b"q"}))) as z:
    check("rejects zip without the plugin", plugin.update_members(z) is None)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    target = root / plugin.UPDATE_PLUGIN
    target.parent.mkdir(parents=True)
    target.write_bytes(b"old plugin")
    (root / "stylesheets").mkdir()
    (root / "stylesheets/x.qss").write_bytes(b"qss")
    changed, pending = plugin.apply_update(zip_bytes(good), root)
    check("applies a good update, skips unchanged files", (changed, pending) == (2, 0) and target.read_bytes() == b"new plugin")
    check("leaves no temp files", not list(root.rglob("*" + plugin.PENDING)))
    try:
        plugin.apply_update(zip_bytes(dict(good, **{"mods/evil.txt": b"x"})), root)
        check("bad update raises", False)
    except ValueError:
        check("bad update raises", target.read_bytes() == b"new plugin")
    locked = root / "stylesheets/x.qss"
    newer = dict(good, **{plugin.UPDATE_PLUGIN: b"newest plugin", "stylesheets/x.qss": b"qss 2"})
    with open(locked, "rb"):
        changed, pending = plugin.apply_update(zip_bytes(newer), root)
    check("file in use is left pending, the rest updates", (changed, pending) == (1, 1) and target.read_bytes() == b"newest plugin" and locked.read_bytes() == b"qss")
    check("next start finishes the pending file", plugin.finish_pending_update(root) == 1 and locked.read_bytes() == b"qss 2" and not list(root.rglob("*" + plugin.PENDING)))

real = sorted(SUPPORT.glob("Dragonwilds-MO2-Support-*.zip"))
if real:
    with zipfile.ZipFile(real[-1]) as z:
        check("real Support zip passes (%s)" % real[-1].name, plugin.update_members(z) is not None)
    with tempfile.TemporaryDirectory() as tmp:
        n, waiting = plugin.apply_update(real[-1].read_bytes(), Path(tmp))
        check("real Support zip installs %d files" % n, waiting == 0 and (Path(tmp) / plugin.UPDATE_PLUGIN).is_file())
check("no profile INI copies", list(plugin.RSDragonwildsGame.GameIniFiles) == [])
print("updater: %d/%d passed" % (sum(results), len(results)))
