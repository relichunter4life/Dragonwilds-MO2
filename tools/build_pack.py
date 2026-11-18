# Made by Claude Ai & Relic Hunter
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "1.0.1"
OUT = os.path.join(ROOT, "release", f"Dragonwilds-MO2-Support-{VERSION}.zip")


def files():
    yield os.path.join(ROOT, "plugin", "game_rsdragonwilds.py"), "plugins/basic_games/games/game_rsdragonwilds.py"
    yield os.path.join(ROOT, "plugin", "rsdragonwilds_ue4ss_boot.dll"), "plugins/basic_games/games/rsdragonwilds_ue4ss_boot.dll"
    yield os.path.join(ROOT, "plugin", "rsdragonwilds_discord.png"), "plugins/basic_games/games/rsdragonwilds_discord.png"
    yield os.path.join(ROOT, "plugin", "rsdragonwilds_notes.json"), "plugins/basic_games/games/rsdragonwilds_notes.json"
    sheets = os.path.join(ROOT, "theme", "stylesheets")
    for base, _, names in os.walk(sheets):
        for name in names:
            path = os.path.join(base, name)
            yield path, "stylesheets/" + os.path.relpath(path, sheets).replace("\\", "/")
    yield os.path.join(ROOT, "theme", "splash.png"), "stylesheets/Transparent-Style/Dragonwilds/splash.png"
    yield os.path.join(ROOT, "pack", "README.txt"), "Dragonwilds MO2 Support - README.txt"
    yield os.path.join(ROOT, "pack", "THIRD-PARTY.txt"), "Dragonwilds - THIRD-PARTY.txt"
    yield os.path.join(ROOT, "tools", "build_bootstrap_dll.py"), "Dragonwilds - Source/build_bootstrap_dll.py"


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in files():
            z.write(src, arc)
            count += 1
    print(f"{OUT} ({count} files, {os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    main()
