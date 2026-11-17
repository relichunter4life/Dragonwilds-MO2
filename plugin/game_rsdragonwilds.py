# Made by Claude Ai & Relic Hunter
from __future__ import annotations

import html
import json
import os
import re
import shutil
import time
import zipfile
import _winapi
from enum import IntEnum, auto
from pathlib import Path

from PyQt6.QtCore import (
    QCoreApplication,
    QDir,
    Q_ARG,
    QFileSystemWatcher,
    QMetaObject,
    QSettings,
    QSize,
    QStandardPaths,
    Qt,
    QTimer,
    QUrl,
    pyqtSignal,
)
from PyQt6.QtGui import QDesktopServices, QDropEvent, QFontDatabase, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

import mobase

from ..basic_features import BasicLocalSavegames
from ..basic_features.basic_save_game_info import BasicGameSaveGame
from ..basic_game import BasicGame

PLUGIN_NAME = "RuneScape Dragonwilds Support"
GAME_FOLDER = "RSDragonwilds"
WIN64 = "Binaries/Win64"
UE4SS_DIR = WIN64 + "/ue4ss"
UE4SS_MODS = UE4SS_DIR + "/Mods"
RS_ROOT = UE4SS_MODS + "/RuneSchema"
RS_MODS = RS_ROOT + "/mods"
PAKS = "Content/Paks"
PAK_MODS = PAKS + "/~mods"
SHIPPING = "RSDragonwilds-Win64-Shipping.exe"
LAUNCHER = "RSDragonwilds.exe"
LOADER = "ue4ss_loader.dll"
BOOT = "rsdragonwilds_ue4ss_boot.dll"
PROXY = "dwmapi.dll"
SWAP_MARK = "ue4ss_loader.mo2swap"
RS_FILE = "runeschema.txt"
UE4SS_FILE = "ue4ss_mods.txt"
DISCORD = "https://discord.gg/BumVNYDUec"
DISCORD_ICON = "rsdragonwilds_discord.png"
NEXUS = "https://www.nexusmods.com/runescapedragonwilds/mods"
PAK_EXT = (".pak", ".utoc", ".ucas", ".sig")
UE4SS_CORE_FILES = ("ue4ss.dll", "ue4ss-settings.ini", "ue4ss.pdb")
RS_STRONG_DIRS = {
    "assets", "blueprints", "buildings", "character-customization", "courses",
    "dialogue", "effects", "enums", "equipment", "events", "journal", "lore",
    "nameplates", "niagara", "npc", "players", "quests", "raw",
    "recipe-discovery", "recipes", "registry", "spawns", "strings", "vendors",
}
RS_WEAK_DIRS = {"paks", "logicmods", "ue4ss", "cache"}
RS_FILES = {"mod.json", "id.txt"}
RS_HEADER = (
    "; RuneSchema mod order - loaded top to bottom.\n"
    "; Use 1 to enable and 0 to disable.\n"
    "; Managed by Mod Organizer 2 (RuneScape: Dragonwilds plugin).\n"
    "; Edit this file or the RuneSchema tab in MO2. Changes apply on the next game start.\n"
)
UE4SS_HEADER = "; UE4SS mod list - managed by Mod Organizer 2 (RuneScape: Dragonwilds plugin).\n"
MASTERS = (
    ("UE4SS", (WIN64 + "/" + LOADER, UE4SS_DIR + "/UE4SS.dll")),
    ("RuneSchema", (RS_ROOT + "/dlls/main.dll",)),
    ("Mod Menu", (UE4SS_MODS + "/ModMenu/Scripts", UE4SS_MODS + "/ModMenu/modmenu.lua")),
)

MASTER_NEXUS = (4, 570, 548)

DIR = mobase.FileTreeEntry.FileTypes.DIRECTORY
MERGE = mobase.IFileTree.InsertPolicy.MERGE
REPLACE = mobase.IFileTree.InsertPolicy.REPLACE


def fold(name: str) -> str:
    return name.casefold()


def is_dir(entry) -> bool:
    return isinstance(entry, mobase.IFileTree)


def master_rank(tree) -> int:
    for rank, (_, paths) in enumerate(MASTERS):
        if any(tree.find(p) is not None for p in paths):
            return rank
    return -1


def parse_order(text: str) -> list[tuple[str, bool]]:
    rows: list[tuple[str, bool]] = []
    seen: dict[str, int] = {}
    if text.startswith("﻿"):
        text = text[1:]
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] in ";#" or ":" not in line:
            continue
        name, value = line.split(":", 1)
        name = name.strip()
        if not name or any(c in name for c in '/\\*?"<>|'):
            continue
        enabled = value.strip() == "1"
        key = fold(name)
        if key in seen:
            index = seen[key]
            rows[index] = (rows[index][0], rows[index][1] and enabled)
            continue
        seen[key] = len(rows)
        rows.append((name, enabled))
    return rows


def walk_tree(root: Path) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    folders: list[Path] = []
    stack = [root]
    while stack:
        folder = stack.pop()
        try:
            entries = list(os.scandir(folder))
        except OSError:
            continue
        for entry in entries:
            path = Path(entry.path)
            try:
                if entry.is_dir(follow_symlinks=False):
                    if not is_link(path):
                        folders.append(path)
                        stack.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files.append(path)
            except OSError:
                pass
    return files, folders


def is_link(path: Path) -> bool:
    try:
        return path.is_junction() or path.is_symlink()
    except OSError:
        return False


NEXUS_CATEGORIES = [
    (9, "Animations"), (10, "Armour"), (8, "Audio"), (6, "Buildings"), (11, "Crafting"), (5, "Gameplay"),
    (12, "Items"), (2, "Miscellaneous"), (3, "Save File"), (13, "Skills"), (4, "Spells"),
    (7, "User Interface"), (16, "Utilities"), (15, "Visuals"), (14, "Weapons"),
]
CAT_OFFSET = 200
MASTER_CAT = (300, "Master Files", CAT_OFFSET + 16)
CAT_IDS = {fold(name): CAT_OFFSET + nexus for nexus, name in NEXUS_CATEGORIES} | {fold(MASTER_CAT[1]): MASTER_CAT[0]}
EMPTY_CATEGORY = {"", "-1", "-1,", "0", "0,"}


def install_categories(base: Path) -> bool:
    cats, nexus_map = base / "categories.dat", base / "nexuscatmap.dat"
    try:
        current = cats.read_text(encoding="utf-8", errors="replace") if cats.is_file() else ""
    except OSError:
        return False
    if current and "|Power Armor|" not in current:
        return False
    rows = sorted(NEXUS_CATEGORIES, key=lambda c: c[1])
    lines = [f"{CAT_OFFSET + nexus}|{name}|0" for nexus, name in rows]
    lines.append(f"{MASTER_CAT[0]}|{MASTER_CAT[1]}|{MASTER_CAT[2]}")
    try:
        if current:
            (base / "categories.dat.mo2default").write_text(current, encoding="utf-8")
        cats.write_text("\n".join(lines) + "\n", encoding="utf-8")
        nexus_map.write_text("".join(f"{CAT_OFFSET + n}|{name}|{n}\n" for n, name in rows), encoding="utf-8")
    except OSError:
        return False
    return True


SEPARATOR = "_separator"
SECTIONS = [
    "Master Files", "Utilities", "User Interface", "Gameplay", "Skills", "Spells", "Items", "Armour",
    "Weapons", "Crafting", "Buildings", "Animations", "Audio", "Visuals", "Miscellaneous", "Save File", "Other Mods",
]
MASTER_SEPARATOR = SECTIONS[0] + SEPARATOR
CAT_SECTION = {CAT_OFFSET + n: name for n, name in NEXUS_CATEGORIES} | {MASTER_CAT[0]: MASTER_CAT[1]}


def mod_category_id(mod: mobase.IModInterface) -> int | None:
    meta = QSettings(str(Path(mod.absolutePath(), "meta.ini")), QSettings.Format.IniFormat)
    for part in str(meta.value("category", "") or "").split(","):
        try:
            value = int(part.strip())
        except ValueError:
            continue
        if value > 0:
            return value
    return None


def section_of(mod: mobase.IModInterface) -> str:
    if master_rank(mod.fileTree()) >= 0:
        return SECTIONS[0]
    return CAT_SECTION.get(mod_category_id(mod) or 0, SECTIONS[-1])


def nexus_category(mod: mobase.IModInterface) -> int | None:
    meta = QSettings(str(Path(mod.absolutePath(), "meta.ini")), QSettings.Format.IniFormat)
    try:
        nexus = int(meta.value("nexusCategory", 0) or 0)
    except (TypeError, ValueError):
        return None
    return CAT_OFFSET + nexus if any(nexus == n for n, _ in NEXUS_CATEGORIES) else None


def write_category(mod: mobase.IModInterface, category_id: int) -> bool:
    meta = QSettings(str(Path(mod.absolutePath(), "meta.ini")), QSettings.Format.IniFormat)
    if str(meta.value("category", "") or "").strip() not in EMPTY_CATEGORY:
        return False
    meta.setValue("category", f"{category_id},")
    meta.sync()
    return True


NOTES_FILE = "rsdragonwilds_notes.json"
NOTES_MARK = "<!--rsdw-notes-->"
GENERIC_FOLDERS = {"runeschema", "shared", "modmenu", "keybinds"}


def load_notes() -> list[dict]:
    try:
        data = json.loads(Path(__file__).with_name(NOTES_FILE).read_text(encoding="utf-8"))
        return [entry for entry in data if isinstance(entry, dict) and entry.get("note")]
    except (OSError, ValueError):
        return []


def note_html(entry: dict) -> str:
    rows = [NOTES_MARK, f"<b>{html.escape(entry.get('name', ''))}</b><br>{html.escape(entry['note'])}"]
    if entry.get("use"):
        rows.append(f"<br><b>How to use:</b> {html.escape(entry['use'])}")
    if entry.get("needs"):
        rows.append(f"<br><b>Needs:</b> {html.escape(', '.join(entry['needs']))}")
    if entry.get("nexus_id"):
        rows.append(f"<br><a href='{NEXUS}/{int(entry['nexus_id'])}'>Nexus page</a>")
    rows.append(f" &middot; <a href='{DISCORD}'>Discord</a>")
    return "".join(rows)


def match_note(mod: mobase.IModInterface, entries: list[dict]) -> dict | None:
    try:
        nexus = int(mod.nexusId())
    except (TypeError, ValueError):
        nexus = 0
    if nexus > 0:
        for entry in entries:
            if entry.get("nexus_id") and int(entry["nexus_id"]) == nexus:
                return entry
    tree = mod.fileTree()
    for entry in entries:
        for folder in entry.get("folders", []):
            if fold(folder) in GENERIC_FOLDERS:
                continue
            if tree.find(f"{UE4SS_MODS}/{folder}") is not None or tree.find(f"{RS_MODS}/{folder}") is not None:
                return entry
    return None


def write_note(mod: mobase.IModInterface, entry: dict) -> bool:
    meta = QSettings(str(Path(mod.absolutePath(), "meta.ini")), QSettings.Format.IniFormat)
    notes = str(meta.value("notes", "") or "")
    comments = str(meta.value("comments", "") or "")
    new_notes = note_html(entry)
    if notes and not notes.startswith(NOTES_MARK):
        return False
    if not notes and comments:
        return False
    if notes == new_notes and comments == entry["note"]:
        return False
    meta.setValue("notes", new_notes)
    meta.setValue("comments", entry["note"])
    meta.sync()
    return True


NEXUS_NAME_NEW = re.compile(r"^(?P<name>.+?) (?P<id>\d+) (?P<ver>\S+) \d{4}-\d{2}-\d{2}T\d{2}-\d{2}Z \w+\.(?:zip|7z|rar)$", re.I)
NEXUS_NAME_OLD = re.compile(r"^(?P<name>.+?)-(?P<id>\d+)-(?P<ver>[\w-]*?)-?\d{9,11}\.(?:zip|7z|rar)$", re.I)
ARCHIVE_EXT = (".zip", ".7z", ".rar")
DW_NAME_MARKERS = ("rsdragonwilds", "dragonwilds", "runeschema")
DW_BYTE_MARKERS = (b"RSDragonwilds", b"/Script/Dominion", b"Dragonwilds", b"dragonwilds")
OTHER_GAME_EXT = (".esp", ".esm", ".esl", ".bsa", ".ba2", ".nif", ".pex", ".psc", ".dds")
SCAN_BUDGET = 64 * 1024 * 1024
SCAN_PER_FILE = 8 * 1024 * 1024


def zip_is_dragonwilds(path: Path) -> bool | None:
    try:
        with zipfile.ZipFile(path) as archive:
            files = [info for info in archive.infolist() if not info.is_dir()]
            names = [info.filename.replace("\\", "/").casefold() for info in files]
            if any(name.endswith(OTHER_GAME_EXT) for name in names):
                return False
            if any(marker in name for name in names for marker in DW_NAME_MARKERS):
                return True
            budget = SCAN_BUDGET
            for info in sorted(files, key=lambda i: i.file_size):
                if budget <= 0:
                    break
                with archive.open(info) as stream:
                    data = stream.read(min(info.file_size, SCAN_PER_FILE))
                budget -= len(data)
                if any(marker in data for marker in DW_BYTE_MARKERS):
                    return True
    except (OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError, ValueError):
        return None
    return False


CURSEFORGE_PAGE = re.compile(r"https://(?:www\.)?curseforge\.com/[^/?#\s]+/[^/?#\s]+/[^/?#\s]+", re.I)
FILE_VERSION = re.compile(r"^(?P<name>.+?)[-_ ]+v?(?P<ver>\d+(?:\.\d+)+)$", re.I)


def download_origin(path: Path) -> tuple[str, str]:
    try:
        with open(f"{path}:Zone.Identifier", encoding="utf-8", errors="ignore") as stream:
            text = stream.read()
    except OSError:
        return "", ""
    low = text.casefold()
    if "curseforge.com" in low or "forgecdn.net" in low:
        page = CURSEFORGE_PAGE.search(text)
        return "curseforge", page.group(0) if page else ""
    if "nexusmods.com" in low or "nexus-cdn.com" in low:
        return "nexus", ""
    return "", ""


def read_order(path: Path) -> list[tuple[str, bool]]:
    try:
        return parse_order(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []


def write_if_changed(path: Path, text: str) -> bool:
    try:
        if path.is_file() and path.read_text(encoding="utf-8", errors="replace") == text:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    except OSError:
        return False


def tier(name: str) -> int:
    key = fold(name)
    if key.startswith("aa_"):
        return 0
    if key.startswith("zz_"):
        return 2
    return 1


def has_child(tree: mobase.IFileTree, names: set[str], want_dir: bool) -> bool:
    for entry in tree:
        if is_dir(entry) == want_dir and fold(entry.name()) in names:
            return True
    return False


def is_ue4ss_mod(tree) -> bool:
    if not is_dir(tree):
        return False
    return bool(
        tree.find("Scripts", DIR)
        or tree.find("dlls/main.dll")
        or tree.find("enabled.txt")
    )


def has_json(tree, depth: int = 0) -> bool:
    for entry in tree:
        if is_dir(entry):
            if depth < 3 and has_json(entry, depth + 1):
                return True
        elif fold(entry.name()).endswith((".json", ".jsonc")):
            return True
    return False


def is_rs_content(tree) -> bool:
    if not is_dir(tree) or is_ue4ss_mod(tree):
        return False
    if tree.find("ue4ss/Mods", DIR) or tree.find("Binaries", DIR):
        return False
    if has_child(tree, RS_FILES, False):
        return has_child(tree, RS_STRONG_DIRS | RS_WEAK_DIRS, True) or tree.find("mod.json") is not None
    for entry in tree:
        if is_dir(entry) and fold(entry.name()) in RS_STRONG_DIRS and has_json(entry):
            return True
    return False


def is_pak_dir(tree) -> bool:
    if not is_dir(tree):
        return False
    found = False
    for entry in tree:
        if is_dir(entry):
            return False
        name = fold(entry.name())
        if name.endswith(PAK_EXT):
            found = True
        elif not name.endswith((".txt", ".md", ".png", ".jpg")):
            return False
    return found


class Act(IntEnum):
    VALID = auto()
    INTO = auto()
    RENAME = auto()
    UNWRAP = auto()
    MODS = auto()
    IGNORE = auto()
    UNKNOWN = auto()


class DragonwildsModDataChecker(mobase.ModDataChecker):
    def __init__(self):
        super().__init__()

    def _classify(self, entry, depth: int = 0) -> tuple[Act, str]:
        name = fold(entry.name())
        if is_dir(entry):
            if name in ("binaries", "content"):
                return Act.VALID, ""
            if name == "rsdragonwilds":
                return Act.UNWRAP, ""
            if name == "ue4ss":
                return Act.INTO, WIN64 + "/"
            if name == "win64":
                return Act.INTO, "Binaries/"
            if name in ("~mods", "logicmods"):
                return Act.INTO, PAKS + "/"
            if name == "paks":
                return Act.INTO, "Content/"
            if name == "mods":
                return Act.MODS, ""
            if name == "runeschema" and (
                entry.find("dlls", DIR) or entry.find("mods", DIR) or entry.find("scripts", DIR)
            ):
                return Act.INTO, UE4SS_MODS + "/"
            if is_ue4ss_mod(entry):
                return Act.INTO, UE4SS_MODS + "/"
            if is_rs_content(entry):
                return Act.INTO, RS_MODS + "/"
            if is_pak_dir(entry):
                return Act.INTO, PAK_MODS + "/"
            if name in ("engine", "__macosx"):
                return Act.IGNORE, ""
            if depth < 3 and self._status(entry, depth + 1, False) != mobase.ModDataChecker.INVALID:
                return Act.UNWRAP, ""
            return Act.UNKNOWN, ""
        if name.endswith(PAK_EXT):
            return Act.INTO, PAK_MODS + "/"
        if name == PROXY:
            return Act.RENAME, WIN64 + "/" + LOADER
        if name in UE4SS_CORE_FILES or name.endswith(".usmap"):
            return Act.INTO, UE4SS_DIR + "/"
        return Act.IGNORE, ""

    def _flat(self, tree: mobase.IFileTree) -> str:
        if tree.parent() is None or not tree.name():
            return ""
        if fold(tree.name()) in ("binaries", "content", "mods", "ue4ss", "rsdragonwilds"):
            return ""
        if is_ue4ss_mod(tree):
            return UE4SS_MODS + "/" + tree.name() + "/"
        if is_rs_content(tree):
            return RS_MODS + "/" + tree.name() + "/"
        if is_pak_dir(tree):
            if fold(tree.name()) == "logicmods":
                return PAKS + "/LogicMods/"
            if fold(tree.name()) in ("~mods", "paks"):
                return PAK_MODS + "/"
            return PAK_MODS + "/" + tree.name() + "/"
        return ""

    def _status(self, tree: mobase.IFileTree, depth: int = 0, allow_flat: bool = True):
        if allow_flat and self._flat(tree):
            return mobase.ModDataChecker.FIXABLE
        status = mobase.ModDataChecker.INVALID
        fixable = False
        for entry in tree:
            act, _ = self._classify(entry, depth)
            if act == Act.VALID:
                status = mobase.ModDataChecker.VALID
            elif act in (Act.INTO, Act.RENAME, Act.UNWRAP, Act.MODS):
                fixable = True
        if fixable:
            return mobase.ModDataChecker.FIXABLE
        if status == mobase.ModDataChecker.VALID and tree.find(WIN64 + "/" + PROXY):
            return mobase.ModDataChecker.FIXABLE
        return status

    def dataLooksValid(self, filetree: mobase.IFileTree) -> mobase.ModDataChecker.CheckReturn:
        return self._status(filetree)

    def fix(self, filetree: mobase.IFileTree) -> mobase.IFileTree:
        flat = self._flat(filetree)
        if flat:
            for entry in list(filetree):
                filetree.move(entry, flat, MERGE)
            return filetree
        for _ in range(8):
            changed = False
            for entry in list(filetree):
                act, dest = self._classify(entry)
                if act == Act.INTO:
                    filetree.move(entry, dest, MERGE)
                    changed = True
                elif act == Act.RENAME:
                    filetree.move(entry, dest, REPLACE)
                    changed = True
                elif act == Act.UNWRAP and is_dir(entry):
                    for child in list(entry):
                        filetree.move(child, "", MERGE)
                    if not entry:
                        entry.detach()
                    changed = True
                elif act == Act.MODS and is_dir(entry):
                    for child in list(entry):
                        target = RS_MODS if is_rs_content(child) else UE4SS_MODS
                        filetree.move(child, target + "/", MERGE)
                    if not entry:
                        entry.detach()
                    changed = True
            if not changed:
                break
        proxy = filetree.find(WIN64 + "/" + PROXY)
        if proxy is not None:
            filetree.move(proxy, WIN64 + "/" + LOADER, REPLACE)
        return filetree


class Content(IntEnum):
    UE4SS_CORE = 0
    LUA = 1
    CPP = 2
    RS_CORE = 3
    RS_CONTENT = 4
    PAK = 5
    LOGIC = 6
    MASTER = 7


class DragonwildsDataContent(mobase.ModDataContent):
    CONTENTS = [
        (Content.UE4SS_CORE, "UE4SS (script loader)", ":/MO/gui/content/skse"),
        (Content.LUA, "UE4SS Lua mod", ":/MO/gui/content/script"),
        (Content.CPP, "UE4SS C++ mod", ":/MO/gui/content/plugin"),
        (Content.RS_CORE, "RuneSchema framework", ":/MO/gui/content/modgroup"),
        (Content.RS_CONTENT, "RuneSchema content", ":/MO/gui/content/menu"),
        (Content.PAK, "Pak mod", ":/MO/gui/content/bsa"),
        (Content.LOGIC, "LogicMods (Blueprint)", ":/MO/gui/content/interface"),
        (Content.MASTER, "Master file (locked at the top)", ":/MO/gui/content/skyproc"),
    ]

    def getAllContents(self) -> list[mobase.ModDataContent.Content]:
        return [mobase.ModDataContent.Content(i, n, icon) for i, n, icon in self.CONTENTS]

    def getContentsFor(self, filetree: mobase.IFileTree) -> list[int]:
        found: set[int] = set()
        if master_rank(filetree) >= 0:
            found.add(Content.MASTER)
        if filetree.find(WIN64 + "/" + LOADER) or filetree.find(UE4SS_DIR + "/UE4SS.dll"):
            found.add(Content.UE4SS_CORE)
        mods = filetree.find(UE4SS_MODS, DIR)
        if is_dir(mods):
            for entry in mods:
                if not is_dir(entry) or fold(entry.name()) == "shared":
                    continue
                if fold(entry.name()) == "runeschema":
                    if entry.find("dlls/main.dll"):
                        found.add(Content.RS_CORE)
                    content = entry.find("mods", DIR)
                    if is_dir(content) and any(is_dir(e) for e in content):
                        found.add(Content.RS_CONTENT)
                elif entry.find("dlls", DIR):
                    found.add(Content.CPP)
                else:
                    found.add(Content.LUA)
        paks = filetree.find(PAKS, DIR)
        if is_dir(paks):
            if paks.find("LogicMods", DIR):
                found.add(Content.LOGIC)
            if paks.find("~mods", DIR):
                found.add(Content.PAK)
        return sorted(found)


class Problem(IntEnum):
    UE4SS_MISSING = auto()
    PROXY_IN_MOD = auto()
    PROXY_IN_GAME = auto()
    RUNESCHEMA_MISSING = auto()
    MODMENU_MISSING = auto()


class LoadOrder:
    def __init__(self, game: "RSDragonwildsGame"):
        self._game = game

    @property
    def _organizer(self) -> mobase.IOrganizer:
        return self._game._organizer

    def profile_file(self) -> Path:
        return Path(self._organizer.profilePath(), RS_FILE)

    def ue4ss_file(self) -> Path:
        return Path(self._organizer.profilePath(), UE4SS_FILE)

    def _active_mods(self):
        modlist = self._organizer.modList()
        for name in modlist.allModsByProfilePriority():
            if not modlist.state(name) & mobase.ModState.ACTIVE:
                continue
            mod = modlist.getMod(name)
            if mod is None or mod.isSeparator():
                continue
            yield name, mod

    def masters(self) -> list[tuple[int, str]]:
        modlist = self._organizer.modList()
        found: dict[int, str] = {}
        for name in modlist.allModsByProfilePriority():
            mod = modlist.getMod(name)
            if mod is None or mod.isSeparator():
                continue
            rank = master_rank(mod.fileTree())
            if rank >= 0 and rank not in found:
                found[rank] = name
        return sorted(found.items())

    def enforce_masters(self) -> bool:
        modlist = self._organizer.modList()
        moved = False
        base = 0
        if modlist.getMod(MASTER_SEPARATOR) is not None:
            if modlist.priority(MASTER_SEPARATOR) != 0:
                modlist.setPriority(MASTER_SEPARATOR, 0)
                moved = True
            base = 1
        for slot, (_, name) in enumerate(self.masters()):
            if modlist.priority(name) != slot + base:
                modlist.setPriority(name, slot + base)
                moved = True
        return moved

    def ensure_separators(self) -> int:
        made = 0
        for section in SECTIONS:
            folder = Path(self._organizer.modsPath(), section + SEPARATOR)
            if folder.exists():
                continue
            try:
                folder.mkdir()
                (folder / "meta.ini").write_text(
                    "[General]\nmodid=0\nversion=\nnewestVersion=\ncategory=\"\"\ninstallationFile=\n",
                    encoding="utf-8",
                )
                made += 1
            except OSError:
                pass
        return made

    def _separator_slots(self) -> list[tuple[int, str]]:
        modlist = self._organizer.modList()
        return sorted(
            (modlist.priority(s + SEPARATOR), s) for s in SECTIONS if modlist.getMod(s + SEPARATOR) is not None
        )

    def organize_all(self):
        modlist = self._organizer.modList()
        groups: dict[str, list[str]] = {s: [] for s in SECTIONS}
        loose: list[str] = []
        for name in modlist.allModsByProfilePriority():
            mod = modlist.getMod(name)
            if mod is None or mod.isOverwrite() or mod.isBackup():
                continue
            if mod.isSeparator():
                if name[: -len(SEPARATOR)] not in groups:
                    loose.append(name)
                continue
            groups[section_of(mod)].append(name)
        order: list[str] = []
        for section in SECTIONS:
            if modlist.getMod(section + SEPARATOR) is not None:
                order.append(section + SEPARATOR)
            order += groups[section]
        order += loose
        for slot, name in enumerate(order):
            if modlist.priority(name) != slot:
                modlist.setPriority(name, slot)

    def place(self, name: str) -> bool:
        modlist = self._organizer.modList()
        mod = modlist.getMod(name)
        if mod is None or mod.isSeparator():
            return True
        section = section_of(mod)
        slots = self._separator_slots()
        here = [p for p, s in slots if s == section]
        if not here:
            return True
        start = here[0]
        after = [p for p, _ in slots if p > start]
        current = modlist.priority(name)
        if after:
            end = after[0]
            if start < current < end:
                return True
            modlist.setPriority(name, end if current > end else end - 1)
        elif current < start:
            modlist.setPriority(name, max(modlist.priority(n) for n in modlist.allModsByProfilePriority()))
        return True

    def real_dirs(self, rel: str) -> list[Path]:
        roots = [Path(self._game.dataDirectory().absolutePath())]
        roots += [Path(mod.absolutePath()) for _, mod in self._active_mods()]
        roots.append(Path(self._organizer.overwritePath()))
        return [root / rel for root in roots if (root / rel).is_dir()]

    def pak_dirs(self) -> list[tuple[str, Path]]:
        found: list[tuple[str, Path]] = []
        seen: set[str] = set()

        def scan(owner: str, root: Path):
            folders = [root] + sorted((c for c in root.iterdir() if c.is_dir()), key=lambda p: fold(p.name))
            for folder in folders:
                stems = {
                    fold(f.stem)
                    for f in folder.iterdir()
                    if f.is_file() and f.suffix.casefold() in (".pak", ".utoc")
                }
                if not stems or stems <= seen:
                    continue
                seen.update(stems)
                label = owner if folder == root else f"{owner}_{folder.name}"
                found.append(("".join(c if c.isalnum() or c in "._-" else "_" for c in label), folder))

        plugin_roots = self.real_dirs(RS_ROOT + "/plugins")
        flags: dict[str, bool] = {}
        for root in plugin_roots:
            flags.update({fold(n): e for n, e in read_order(root / "plugins.txt")})
        for root in plugin_roots:
            for plugin in sorted(root.iterdir(), key=lambda p: fold(p.name)):
                if plugin.is_dir() and flags.get(fold(plugin.name), True) and (plugin / "paks").is_dir():
                    scan("RSPlugin_" + plugin.name, plugin / "paks")
        rows, _ = self.build(self._game.follow_mod_order())
        for name, enabled, _ in rows:
            if enabled:
                for paks in self.real_dirs(f"{RS_MODS}/{name}/paks"):
                    scan("RS_" + name, paks)
        return found

    def core_dir(self) -> Path | None:
        found = None
        for _, mod in self._active_mods():
            if mod.fileTree().find(RS_ROOT + "/dlls/main.dll"):
                found = Path(mod.absolutePath(), RS_ROOT)
        if found is not None:
            return found
        physical = Path(self._game.dataDirectory().absolutePath(), RS_ROOT)
        return physical if (physical / "dlls" / "main.dll").is_file() else None

    def _owner(self, rel: str) -> Path | None:
        found = None
        for _, mod in self._active_mods():
            if mod.fileTree().find(rel) is not None:
                found = Path(mod.absolutePath())
        return found

    def tidy_overwrite(self) -> int:
        over = Path(self._organizer.overwritePath())
        mods_root = Path(self._organizer.modsPath())
        if not over.is_dir():
            return 0
        core = self.core_dir()
        core_mod = core.parents[len(Path(RS_ROOT).parts) - 1] if core is not None and mods_root in core.parents else None
        owners: dict[str, Path | None] = {}

        def owner(key: str) -> Path | None:
            if key not in owners:
                owners[key] = self._owner(key)
            return owners[key]

        skip = {fold(f"{RS_MODS}/{RS_FILE}"), fold(f"{UE4SS_MODS}/mods.txt")}
        rs_mods, rs_root, ue_mods, ue_dir = (fold(p) + "/" for p in (RS_MODS, RS_ROOT, UE4SS_MODS, UE4SS_DIR))
        moved = 0
        files, folders = walk_tree(over)
        for path in sorted(files):
            rel = path.relative_to(over).as_posix()
            low = fold(rel)
            if low in skip or path.name.casefold().startswith(RS_FILE):
                continue
            target = None
            if low.startswith(rs_mods) and low.count("/") > rs_mods.count("/"):
                target = owner(rel[: len(rs_mods)] + rel[len(rs_mods):].split("/")[0])
            elif low.startswith(rs_root):
                target = core_mod
            elif low.startswith(ue_mods) and low.count("/") > ue_mods.count("/"):
                target = owner(rel[: len(ue_mods)] + rel[len(ue_mods):].split("/")[0])
            elif low.startswith(ue_dir) and low.count("/") == ue_dir.count("/"):
                target = owner(UE4SS_DIR + "/UE4SS.dll") or owner(UE4SS_DIR + "/ue4ss.dll")
            if target is None or mods_root not in target.parents:
                continue
            try:
                dest = target / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                path.replace(dest)
                moved += 1
            except OSError:
                pass
        for folder in sorted(folders, key=lambda p: len(p.parts), reverse=True):
            try:
                folder.rmdir()
            except OSError:
                pass
        return moved

    def mirror_manifest(self) -> Path:
        return Path(self._organizer.profilePath(), "helpy_mirror.txt")

    def deploy_mirror(self) -> int:
        core = self.core_dir()
        data = Path(self._game.dataDirectory().absolutePath())
        target = data / RS_ROOT
        if core is None or core == target or Path(self._organizer.modsPath()) not in core.parents:
            return 0
        self.remove_mirror()
        if target.exists() or is_link(target):
            return 0
        made: list[str] = []
        parent = target.parent
        missing = []
        while not parent.exists() and data in parent.parents:
            missing.append(parent)
            parent = parent.parent
        try:
            for folder in reversed(missing):
                folder.mkdir()
                made.append("dir:" + folder.relative_to(data).as_posix())
            _winapi.CreateJunction(str(core), str(target))
            made.append("link:" + RS_ROOT)
        except OSError:
            try:
                if target.is_dir() and not is_link(target) and not any(target.iterdir()):
                    target.rmdir()
            except OSError:
                pass
        if made:
            self.mirror_manifest().write_text("\n".join(made), encoding="utf-8")
        return len(made)

    def _our_link(self, path: Path) -> bool:
        if not is_link(path):
            return False
        try:
            dest = os.readlink(path)
        except OSError:
            return False
        if dest.startswith("\\\\?\\"):
            dest = dest[4:]
        mods = Path(self._organizer.modsPath()).resolve()
        try:
            return mods in Path(dest).resolve().parents
        except OSError:
            return False

    def remove_mirror(self):
        data = Path(self._game.dataDirectory().absolutePath())
        target = data / RS_ROOT
        if self._our_link(target):
            try:
                os.rmdir(target)
            except OSError:
                pass
        manifest = self.mirror_manifest()
        if not manifest.exists():
            return
        try:
            lines = [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
        except OSError:
            lines = []
        for line in reversed(lines):
            if not line.startswith("dir:"):
                continue
            folder = data / line[4:]
            if data not in folder.parents or is_link(folder):
                continue
            try:
                os.rmdir(folder)
            except OSError:
                pass
        try:
            manifest.unlink()
        except OSError:
            pass

    def has_runeschema(self) -> bool:
        if Path(self._game.dataDirectory().absolutePath(), RS_ROOT).is_dir():
            return True
        for _, mod in self._active_mods():
            if mod.fileTree().find(RS_ROOT, DIR):
                return True
        return False

    def has_ue4ss_mods(self) -> bool:
        if Path(self._game.dataDirectory().absolutePath(), UE4SS_MODS).is_dir():
            return True
        for _, mod in self._active_mods():
            if mod.fileTree().find(UE4SS_MODS, DIR):
                return True
        return False

    def discover(self) -> list[tuple[str, str]]:
        found: dict[str, tuple[str, str]] = {}

        def add(name: str, source: str):
            key = fold(name)
            if key in found:
                found.pop(key)
            found[key] = (name, source)

        physical = Path(self._game.dataDirectory().absolutePath(), RS_MODS)
        if physical.is_dir():
            for folder in sorted(physical.iterdir(), key=lambda p: fold(p.name)):
                if folder.is_dir():
                    add(folder.name, "Game folder")
        modlist = self._organizer.modList()
        for name, mod in self._active_mods():
            tree = mod.fileTree().find(RS_MODS, DIR)
            if is_dir(tree):
                for entry in tree:
                    if is_dir(entry):
                        add(entry.name(), modlist.displayName(name))
        overwrite = Path(self._organizer.overwritePath(), RS_MODS)
        if overwrite.is_dir():
            for folder in sorted(overwrite.iterdir(), key=lambda p: fold(p.name)):
                if folder.is_dir():
                    add(folder.name, "Overwrite")
        return list(found.values())

    def build(self, follow: bool):
        discovered = self.discover()
        present = {fold(n): (n, s) for n, s in discovered}
        saved = read_order(self.profile_file())
        flags = {fold(n): e for n, e in saved}
        if follow:
            names = [n for n, _ in sorted(discovered, key=lambda d: tier(d[0]))]
        else:
            names = [present[fold(n)][0] for n, _ in saved if fold(n) in present]
            known = {fold(n) for n in names}
            names += [n for n, _ in discovered if fold(n) not in known]
        rows = [(n, flags.get(fold(n), True), present[fold(n)][1]) for n in names]
        absent = [(n, e) for n, e in saved if fold(n) not in present]
        return rows, absent

    def write(self, rows, absent) -> bool:
        lines = [f"{n} : {1 if e else 0}" for n, e, *_ in rows]
        lines += [f"{n} : {1 if e else 0}" for n, e in absent]
        return write_if_changed(self.profile_file(), RS_HEADER + "\n".join(lines) + ("\n" if lines else ""))

    def sync(self):
        rows, absent = self.build(self._game.follow_mod_order())
        self.write(rows, absent)
        return rows, absent

    def import_runtime_changes(self) -> bool:
        folder = Path(self._organizer.overwritePath(), RS_MODS)
        runtime = folder / RS_FILE
        if not runtime.is_file():
            return False
        rows = read_order(runtime)
        saved = read_order(self.profile_file())
        if self._game.follow_mod_order():
            flags = {fold(n): e for n, e in rows}
            merged = [(n, flags.pop(fold(n), e)) for n, e in saved]
            merged += [(n, e) for n, e in rows if fold(n) in flags]
        else:
            merged = list(rows)
            known = {fold(n) for n, _ in rows}
            merged += [(n, e) for n, e in saved if fold(n) not in known]
        write_if_changed(
            self.profile_file(),
            RS_HEADER + "\n".join(f"{n} : {1 if e else 0}" for n, e in merged) + "\n",
        )
        for leftover in folder.glob(RS_FILE + "*"):
            try:
                leftover.unlink()
            except OSError:
                pass
        return True

    def write_ue4ss_mods(self) -> bool:
        order: dict[str, list] = {}
        defaults: dict[str, bool] = {}

        def add(name: str, enabled: bool | None = None):
            key = fold(name)
            if key == "shared" or key in order or " " in name:
                return
            order[key] = [name, defaults.get(key, True) if enabled is None else enabled]

        def learn(path: Path):
            for n, e in read_order(path):
                defaults.setdefault(fold(n), e)

        physical = Path(self._game.dataDirectory().absolutePath(), UE4SS_MODS)
        if physical.is_dir():
            learn(physical / "mods.txt")
            for n, e in read_order(physical / "mods.txt"):
                if (physical / n).is_dir():
                    add(n, e)
            for folder in sorted(physical.iterdir(), key=lambda p: fold(p.name)):
                if folder.is_dir():
                    add(folder.name)
        for _, mod in self._active_mods():
            tree = mod.fileTree().find(UE4SS_MODS, DIR)
            if not is_dir(tree):
                continue
            txt = Path(mod.absolutePath(), UE4SS_MODS, "mods.txt")
            if txt.is_file():
                learn(txt)
                names = {fold(e.name()) for e in tree if is_dir(e)}
                for n, e in read_order(txt):
                    if fold(n) in names:
                        add(n, e)
            for entry in tree:
                if is_dir(entry):
                    add(entry.name())
        overwrite = Path(self._organizer.overwritePath(), UE4SS_MODS)
        if overwrite.is_dir():
            for folder in sorted(overwrite.iterdir(), key=lambda p: fold(p.name)):
                if folder.is_dir() and folder.name.casefold() != "runeschema":
                    add(folder.name)
        rows = list(order.values())
        rows.sort(key=lambda r: fold(r[0]) == "keybinds")
        text = UE4SS_HEADER + "".join(f"{n} : {1 if e else 0}\n" for n, e in rows)
        return write_if_changed(self.ue4ss_file(), text)


class OrderTree(QTreeWidget):
    dropped = pyqtSignal()

    def dropEvent(self, event: QDropEvent | None):
        super().dropEvent(event)
        self.dropped.emit()


class RuneSchemaTab(QWidget):
    def __init__(self, parent: QWidget | None, game: "RSDragonwildsGame"):
        super().__init__(parent)
        self._game = game
        self._absent: list[tuple[str, bool]] = []
        self._loading = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        top = QHBoxLayout()
        self._follow = QCheckBox("Follow the mod list (left pane) order")
        self._follow.setToolTip(
            "On: RuneSchema mods load in the same order as the mods on the left.\n"
            "Off: drag the rows here to set your own order."
        )
        top.addWidget(self._follow)
        top.addStretch(1)
        self._sort = QPushButton("Sort by mod list")
        self._open = QPushButton("Open runeschema.txt")
        self._refresh = QPushButton("Refresh")
        for button in (self._sort, self._open, self._refresh):
            top.addWidget(button)
        layout.addLayout(top)
        self._tree = OrderTree(self)
        self._tree.setObjectName("runeschemaOrder")
        self._tree.setColumnCount(3)
        self._tree.setHeaderLabels(["#", "RuneSchema mod", "Installed by"])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._tree.setDropIndicatorShown(True)
        header = self._tree.header()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._tree, 1)
        self._info = QLabel(self)
        self._info.setWordWrap(True)
        layout.addWidget(self._info)
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(lambda _p: self._game.sync_later())
        self._follow.toggled.connect(self._on_follow)
        self._sort.clicked.connect(self._on_sort)
        self._open.clicked.connect(self._on_open)
        self._refresh.clicked.connect(lambda: self._game.sync_now())
        self._tree.itemChanged.connect(self._on_item_changed)
        self._tree.dropped.connect(lambda: QTimer.singleShot(0, self._save_view))

    def show_rows(self, rows, absent):
        self._loading = True
        self._absent = list(absent)
        follow = self._game.follow_mod_order()
        self._follow.blockSignals(True)
        self._follow.setChecked(follow)
        self._follow.blockSignals(False)
        self._sort.setEnabled(not follow)
        self._tree.setDragDropMode(
            QAbstractItemView.DragDropMode.NoDragDrop
            if follow
            else QAbstractItemView.DragDropMode.InternalMove
        )
        self._tree.clear()
        base = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
        flags = base if follow else base | Qt.ItemFlag.ItemIsDragEnabled
        for index, (name, enabled, source) in enumerate(rows):
            item = QTreeWidgetItem([str(index + 1), name, source])
            item.setFlags(flags)
            item.setCheckState(1, Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
            item.setTextAlignment(0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._tree.addTopLevelItem(item)
        root = self._tree.invisibleRootItem()
        if root is not None:
            root.setFlags(root.flags() | Qt.ItemFlag.ItemIsDropEnabled)
        path = self._game.order.profile_file()
        on = sum(1 for _, e, _ in rows if e)
        mode = "follows the mod list on the left" if follow else "uses the order you drag here"
        masters = [MASTERS[rank][0] for rank, _ in self._game.order.masters()]
        locked = (
            f"Master files locked at the top: {', '.join(masters)}. "
            if masters and self._game._setting("lock_master_files")
            else ""
        )
        self._info.setText(
            f"{locked}{on} of {len(rows)} RuneSchema mods enabled. The order {mode}. "
            f"Top loads first. Saved to {path} and used by the game on the next start."
        )
        if path.is_file() and str(path) not in self._watcher.files():
            for old in self._watcher.files():
                self._watcher.removePath(old)
            self._watcher.addPath(str(path))
        self._loading = False

    def _rows_from_view(self):
        rows = []
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item is None:
                continue
            rows.append((item.text(1), item.checkState(1) == Qt.CheckState.Checked, item.text(2)))
        return rows

    def _save_view(self):
        if self._loading:
            return
        rows = self._rows_from_view()
        self._game.order.write(rows, self._absent)
        self.show_rows(rows, self._absent)

    def _on_item_changed(self, _item, column: int):
        if not self._loading and column == 1:
            QTimer.singleShot(0, self._save_view)

    def _on_follow(self, checked: bool):
        self._game.set_follow_mod_order(checked)

    def _on_sort(self):
        rows, absent = self._game.order.build(True)
        flags = {fold(n): e for n, e, _ in self._rows_from_view()}
        rows = [(n, flags.get(fold(n), e), s) for n, e, s in rows]
        self._game.order.write(rows, absent)
        self.show_rows(rows, absent)

    def _on_open(self):
        path = self._game.order.profile_file()
        if not path.is_file():
            self._game.sync_now()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


class RSDragonwildsGame(BasicGame, mobase.IPluginFileMapper, mobase.IPluginDiagnose):
    Name = PLUGIN_NAME
    Author = "Relic Hunter"
    Version = "1.0.0"
    Description = (
        "Adds RuneScape: Dragonwilds to Mod Organizer 2: UE4SS Lua mods, RuneSchema mods "
        "and pak mods, with a RuneSchema load order tab that writes runeschema.txt."
    )

    GameName = "RuneScape: Dragonwilds"
    GameShortName = "runescapedragonwilds"
    GameNexusName = "runescapedragonwilds"
    GameValidShortNames = ["rsdragonwilds", "dragonwilds"]
    GameNexusId = 7597
    GameSteamId = 1374490
    GameBinary = LAUNCHER
    GameDataPath = GAME_FOLDER
    GameSaveExtension = "sav"
    _LOCAL = os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local")).replace("\\", "/")
    GameDocumentsDirectory = _LOCAL + "/RSDragonwilds/Saved/Config/Windows"
    GameSavesDirectory = _LOCAL + "/RSDragonwilds/Saved/SaveGames"
    GameIniFiles = ["Engine.ini", "GameUserSettings.ini", "Input.ini"]
    GameSupportURL = "https://www.nexusmods.com/runescapedragonwilds"
    NOT_SAVES = {"enhancedinputusersettings.sav"}

    def listSaves(self, folder: QDir) -> list[mobase.ISaveGame]:
        return [
            BasicGameSaveGame(path)
            for path in Path(folder.absolutePath()).glob(f"**/*.{self.GameSaveExtension}")
            if path.name.casefold() not in self.NOT_SAVES
        ]

    def __init__(self):
        BasicGame.__init__(self)
        mobase.IPluginFileMapper.__init__(self)
        mobase.IPluginDiagnose.__init__(self)
        self.order = LoadOrder(self)
        self._tab: RuneSchemaTab | None = None
        self._timer: QTimer | None = None
        self._has_rs = False
        self._has_ue4ss = False
        self._enforcing = False
        self._pending_place: set[str] = set()
        self._queried: set[str] = set()
        self._reinstall_flags: list[Path] = []
        self._running = False
        self._busy = False
        self._main = None

    def init(self, organizer: mobase.IOrganizer) -> bool:
        super().init(organizer)
        fonts = Path(QCoreApplication.applicationDirPath(), "stylesheets", "Transparent-Style", "Dragonwilds", "fonts")
        if fonts.is_dir():
            for ttf in sorted(fonts.glob("*.ttf")):
                QFontDatabase.addApplicationFont(str(ttf))
        self._register_feature(DragonwildsModDataChecker())
        self._register_feature(DragonwildsDataContent())
        self._register_feature(BasicLocalSavegames(self.savesDirectory()))
        organizer.onUserInterfaceInitialized(self._on_ui)
        organizer.onAboutToRun(self._on_about_to_run)
        organizer.onFinishedRun(self._on_finished_run)
        organizer.onProfileChanged(lambda _a, _b: self.sync_later())
        organizer.onPluginSettingChanged(self._on_setting_changed)
        modlist = organizer.modList()
        modlist.onModMoved(lambda _n, _o, _p: self.sync_later())
        modlist.onModStateChanged(lambda _m: self.sync_later())
        modlist.onModInstalled(self._on_installed)
        organizer.downloadManager().onDownloadComplete(self._on_download_complete)
        modlist.onModRemoved(lambda _n: self.sync_later())
        return True

    def settings(self) -> list[mobase.PluginSetting]:
        return [
            mobase.PluginSetting(
                "lock_master_files",
                "Keep the master files (UE4SS, RuneSchema, Mod Menu) locked at the top of the mod list.",
                True,
            ),
            mobase.PluginSetting(
                "follow_mod_order",
                "RuneSchema mods load in the same order as the mod list on the left.",
                True,
            ),
            mobase.PluginSetting(
                "swap_ue4ss_loader",
                "If UE4SS is installed straight into the game folder, rename its dwmapi.dll "
                "while the game runs from MO2 (so MO2 mods are seen) and put it back afterwards.",
                True,
            ),
            mobase.PluginSetting(
                "map_runeschema_paks",
                "Also show the paks of enabled RuneSchema mods and plugins to the game through Content/Paks/~mods. "
                "Only needed if rsdragonwilds_ue4ss_boot.dll is missing (then it is used automatically).",
                False,
            ),
            mobase.PluginSetting(
                "helpy_mirror",
                "While the game runs, put a folder link to the RuneSchema mod in the game folder so RuneSchema's "
                "Helpy window can find it (Helpy runs outside MO2's virtual folder). Removed when the game closes.",
                True,
            ),
            mobase.PluginSetting(
                "manage_ue4ss_mods_txt",
                "Write UE4SS mods.txt from the mod list so every enabled UE4SS mod loads.",
                True,
            ),
            mobase.PluginSetting(
                "discord_panel",
                "Show the community Discord button at the top right of MO2.",
                True,
            ),
            mobase.PluginSetting(
                "discord_link",
                "Invite link the Discord button opens.",
                DISCORD,
            ),
            mobase.PluginSetting(
                "forward_downloads",
                "While MO2 is open, Dragonwilds mods you download from Nexus with Manual download "
                "are moved from your Downloads folder into MO2's Downloads tab.",
                True,
            ),
            mobase.PluginSetting(
                "downloads_folder",
                "Folder your browser saves downloads to (empty = your Windows Downloads folder).",
                "",
            ),
            mobase.PluginSetting(
                "sort_overwrite",
                "Move files the game writes (logs, mod data, UE4SS.log) out of Overwrite into the mod they belong to.",
                True,
            ),
            mobase.PluginSetting(
                "auto_install",
                "Install every finished Dragonwilds download straight away, switch it on and file it "
                "under its category separator. Off = install by double-clicking in the Downloads tab.",
                False,
            ),
            mobase.PluginSetting(
                "mod_separators",
                "Group the mod list under category separators (Master Files, Gameplay, User Interface ...). "
                "Done once on first start; new mods are filed under their category.",
                True,
            ),
            mobase.PluginSetting(
                "separators_made",
                "The category separators were created (untick to rebuild and regroup the list on next start).",
                False,
            ),
            mobase.PluginSetting(
                "link_nexus_ids",
                "Give known Dragonwilds mods (UE4SS, RuneSchema, Mod Menu and Relic Hunter's mods) their Nexus "
                "mod ID when it is missing, so Nexus Info, Open in Browser and update checks work.",
                True,
            ),
            mobase.PluginSetting(
                "match_nexus_versions",
                "When a Nexus file's own version is higher than its mod page version, show the mod page version "
                "(removes MO2's red 'newer than Nexus' warning triangle).",
                True,
            ),
            mobase.PluginSetting(
                "mod_categories",
                "Use Nexus's Dragonwilds categories in MO2 and file known mods under them (only mods without a category).",
                True,
            ),
            mobase.PluginSetting(
                "mod_notes",
                "Add a short how-to note to known Dragonwilds mods (Notes column). Notes you wrote yourself are never changed.",
                True,
            ),
            mobase.PluginSetting(
                "welcome_shown",
                "The Getting started window was shown (untick to see it again).",
                False,
            ),
        ]

    def _setting(self, key: str, default=True):
        value = self._organizer.pluginSetting(self.name(), key)
        return default if value is None else bool(value)

    def follow_mod_order(self) -> bool:
        return self._setting("follow_mod_order")

    def set_follow_mod_order(self, value: bool):
        self._organizer.setPluginSetting(self.name(), "follow_mod_order", bool(value))
        self.sync_now()

    def _on_setting_changed(self, plugin: str, _key: str, _old, _new):
        if plugin == self.name():
            self.sync_later()

    def executables(self) -> list[mobase.ExecutableInfo]:
        game = self.gameDirectory()
        return [
            mobase.ExecutableInfo(
                "RuneScape Dragonwilds",
                game.absoluteFilePath(f"{GAME_FOLDER}/{WIN64}/{SHIPPING}"),
            ).withSteamAppId(str(self.GameSteamId)),
            mobase.ExecutableInfo(
                "RuneScape Dragonwilds (launcher)",
                game.absoluteFilePath(LAUNCHER),
            ).withSteamAppId(str(self.GameSteamId)),
        ]

    def loader_path(self) -> str:
        return os.path.normpath(self.gameDirectory().absoluteFilePath(f"{GAME_FOLDER}/{WIN64}/{LOADER}"))

    def executableForcedLoads(self) -> list[mobase.ExecutableForcedLoadSetting]:
        loads = [
            mobase.ExecutableForcedLoadSetting(SHIPPING, self.loader_path())
            .withEnabled(True)
            .withForced(True)
        ]
        boot = Path(__file__).with_name(BOOT)
        if boot.is_file():
            loads.append(
                mobase.ExecutableForcedLoadSetting(SHIPPING, str(boot)).withEnabled(True).withForced(True)
            )
        return loads

    def mappings(self) -> list[mobase.Mapping]:
        if not self.isActive():
            return []
        data = self.dataDirectory().absolutePath()
        result: list[mobase.Mapping] = []
        core = self.order.core_dir() if self._has_rs else None
        if core is not None:
            result.append(mobase.Mapping(str(core), f"{data}/{RS_ROOT}", True, True))
        rs = self.order.profile_file()
        if self._has_rs and rs.is_file():
            result.append(mobase.Mapping(str(rs), f"{data}/{RS_MODS}/{RS_FILE}", False, False))
        ue = self.order.ue4ss_file()
        if self._has_ue4ss and ue.is_file() and self._setting("manage_ue4ss_mods_txt"):
            result.append(mobase.Mapping(str(ue), f"{data}/{UE4SS_MODS}/mods.txt", False, False))
        if self._has_rs and (self._setting("map_runeschema_paks", False) or not Path(__file__).with_name(BOOT).is_file()):
            try:
                for _label, folder in self.order.pak_dirs():
                    for file in sorted(folder.iterdir()):
                        if file.is_file() and file.suffix.casefold() in PAK_EXT:
                            result.append(mobase.Mapping(str(file), f"{data}/{PAK_MODS}/{file.name}", False, False))
            except OSError:
                pass
        return result

    def _win64(self) -> Path:
        return Path(self.gameDirectory().absolutePath(), GAME_FOLDER, WIN64)

    def sync_later(self):
        if self._timer is None:
            self._timer = QTimer()
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self.sync_now)
        self._timer.start(200)

    def sync_now(self):
        if not self.isActive():
            return
        if self._enforcing:
            return
        try:
            if self._setting("lock_master_files"):
                self._enforcing = True
                try:
                    self.order.enforce_masters()
                finally:
                    self._enforcing = False
            self._has_rs = self.order.has_runeschema()
            self._has_ue4ss = self.order.has_ue4ss_mods()
            rows, absent = self.order.sync()
            if self._setting("manage_ue4ss_mods_txt"):
                self.order.write_ue4ss_mods()
            if self._tab is not None:
                self._tab.show_rows(rows, absent)
        finally:
            self._invalidate()

    def _on_ui(self, main_window: QMainWindow):
        if not self.isActive():
            return
        self._restore_loader()
        try:
            self.order.remove_mirror()
        except OSError:
            pass
        splash = Path(QCoreApplication.applicationDirPath(), "stylesheets", "Transparent-Style", "Dragonwilds", "splash.png")
        target = Path(self._organizer.basePath(), "splash.png")
        try:
            if splash.is_file() and not target.exists():
                target.write_bytes(splash.read_bytes())
        except OSError:
            pass
        tabs = main_window.findChild(QTabWidget, "tabWidget")
        if tabs is not None:
            self._tab = RuneSchemaTab(main_window, self)
            tabs.insertTab(0, self._tab, "RuneSchema")
            tabs.setCurrentIndex(0)
        if self._setting("mod_categories"):
            install_categories(Path(self._organizer.basePath()))
        if self._setting("discord_panel"):
            self._add_discord(main_window)
        if not self._setting("welcome_shown", False):
            QTimer.singleShot(1200, lambda: self._welcome(main_window))
        self._sort_overwrite_later()
        if self._setting("forward_downloads"):
            self._start_forwarder(main_window)
        self._main = main_window
        QTimer.singleShot(4000, self._query_missing_info)
        self.sync_now()

    def _query_missing_info(self):
        if not self.isActive():
            return
        if not self._setting("forward_downloads"):
            return
        view = self._main.findChild(QWidget, "downloadView") if getattr(self, "_main", None) else None
        model = view.model() if view is not None else None
        source = model.sourceModel() if model is not None and hasattr(model, "sourceModel") else None
        if source is None:
            return
        manager = self._organizer.downloadManager()
        for row in range(source.rowCount()):
            try:
                archive = Path(manager.downloadPath(row))
            except Exception:
                continue
            name = archive.name
            meta_path = Path(f"{archive}.meta")
            if not name or fold(name) in self._queried or not meta_path.is_file():
                continue
            meta = QSettings(str(meta_path), QSettings.Format.IniFormat)
            try:
                mod_id = int(meta.value("modID", 0) or 0)
                file_id = int(meta.value("fileID", 0) or 0)
            except (TypeError, ValueError):
                continue
            if mod_id <= 0 or file_id > 0 or str(meta.value("repository", "")) != "Nexus":
                continue
            if fold(str(meta.value("gameName", ""))) != fold(self.GameShortName):
                continue
            self._queried.add(fold(name))
            if str(meta.value("installed", "false")).casefold() == "true":
                self._reinstall_flags.append(meta_path)
            QMetaObject.invokeMethod(view, "queryInfoMd5", Qt.ConnectionType.QueuedConnection, Q_ARG(int, row))
        if self._reinstall_flags:
            QTimer.singleShot(10000, self._restore_installed_flags)

    def _restore_installed_flags(self):
        paths, self._reinstall_flags = self._reinstall_flags, []
        for meta_path in paths:
            meta = QSettings(str(meta_path), QSettings.Format.IniFormat)
            if str(meta.value("installed", "false")).casefold() != "true":
                meta.setValue("installed", True)
                meta.sync()
        refresh = self._main.findChild(QPushButton, "btnRefreshDownloads")
        if refresh is not None:
            refresh.click()

    def _start_forwarder(self, main_window: QMainWindow):
        folder = self._organizer.pluginSetting(self.name(), "downloads_folder") or QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        if not folder or not Path(folder).is_dir():
            return
        try:
            if Path(folder).resolve() == Path(self._organizer.downloadsPath()).resolve():
                return
        except OSError:
            return
        self._fw_folder = Path(folder)
        self._fw_since = time.time() - 5
        self._fw_seen: set[str] = set()
        self._fw_window = main_window
        self._fw_timer = QTimer()
        self._fw_timer.setSingleShot(True)
        self._fw_timer.timeout.connect(self._scan_downloads)
        self._fw_watch = QFileSystemWatcher([str(self._fw_folder)])
        self._fw_watch.directoryChanged.connect(lambda _p: self._fw_timer.start(2000))

    def _scan_downloads(self):
        if not self.isActive():
            return
        if not self._setting("forward_downloads"):
            return
        try:
            files = sorted(p for p in self._fw_folder.iterdir() if p.is_file() and p.suffix.casefold() in ARCHIVE_EXT)
        except OSError:
            return
        for path in files:
            key = fold(path.name)
            if key in self._fw_seen:
                continue
            try:
                info = path.stat()
            except OSError:
                continue
            if max(info.st_mtime, info.st_ctime) < self._fw_since:
                self._fw_seen.add(key)
                continue
            partial = any(
                Path(f"{path}{ext}").exists() or path.with_suffix(ext).exists()
                for ext in (".crdownload", ".part", ".partial", ".tmp", ".download")
            )
            if info.st_size == 0 or partial or time.time() - info.st_mtime < 1.5:
                self._fw_timer.start(3000)
                continue
            self._fw_seen.add(key)
            origin, page = download_origin(path)
            named = None
            if origin != "curseforge":
                named = NEXUS_NAME_NEW.match(path.name) or NEXUS_NAME_OLD.match(path.name)
                if named:
                    origin = "nexus"
            if not origin:
                continue
            is_zip = path.suffix.casefold() == ".zip"
            verdict = zip_is_dragonwilds(path) if is_zip else None
            if verdict is False or (is_zip and verdict is None):
                continue
            if verdict is None:
                answer = QMessageBox.question(
                    self._fw_window,
                    "CurseForge download" if origin == "curseforge" else "Nexus download",
                    f"Is {path.name} a RuneScape: Dragonwilds mod?\n\n"
                    "Yes moves it from your Downloads folder into MO2's Downloads tab. "
                    "No leaves it where it is.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    continue
            self._forward(path, named, origin, page)

    def _forward(self, path: Path, named, origin: str = "nexus", page: str = ""):
        target_dir = Path(self._organizer.downloadsPath())
        dest = target_dir / path.name
        count = 1
        while dest.exists() or Path(f"{dest}.meta").exists():
            dest = target_dir / f"{path.stem} ({count}){path.suffix}"
            count += 1
        try:
            shutil.move(str(path), str(dest))
        except OSError:
            return
        meta = QSettings(f"{dest}.meta", QSettings.Format.IniFormat)
        meta.setValue("gameName", self.GameShortName)
        for key in ("installed", "uninstalled", "paused", "removed"):
            meta.setValue(key, False)
        if origin == "curseforge":
            parsed = FILE_VERSION.match(path.stem)
            name = (parsed["name"] if parsed else path.stem).replace("_", " ").strip()
            meta.setValue("name", name)
            meta.setValue("modName", name)
            if parsed:
                meta.setValue("version", parsed["ver"])
            meta.setValue("repository", "CurseForge")
            if page:
                meta.setValue("url", page)
        elif named:
            meta.setValue("modID", int(named["id"]))
            meta.setValue("name", named["name"])
            meta.setValue("modName", named["name"])
            meta.setValue("version", named["ver"].replace("-", "."))
            meta.setValue("repository", "Nexus")
        meta.sync()
        QTimer.singleShot(3000, self._query_missing_info)
        QTimer.singleShot(9000, lambda: self._auto_install(dest))
        tabs = self._fw_window.findChild(QTabWidget, "tabWidget")
        if tabs is not None:
            for index in range(tabs.count()):
                if tabs.widget(index).objectName() == "downloadTab" or fold(tabs.tabText(index)).startswith("downloads"):
                    tabs.setCurrentIndex(index)
                    break

    def _welcome(self, main_window: QMainWindow):
        self._organizer.setPluginSetting(self.name(), "welcome_shown", True)
        link = self._organizer.pluginSetting(self.name(), "discord_link") or DISCORD
        box = QMessageBox(main_window)
        box.setWindowTitle("RuneScape: Dragonwilds - Getting started")
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        box.setText(
            "<h3>Welcome to Mod Organizer 2 for Dragonwilds</h3>"
            "<ol>"
            "<li>Open <b>Settings</b> (tools icon) &gt; <b>Nexus</b> &gt; <b>Connect to Nexus</b> and log in.</li>"
            "<li>On Nexus press <b>Mod Manager Download</b> for the three master files:<br>"
            f"<a href='{NEXUS}/4?tab=files'>UE4SS</a> (file \"UE4SS Steam (latest) 3.0.1-gf6d5f942\"), "
            f"<a href='{NEXUS}/570?tab=files'>RuneSchema</a> 0.9.0.0 and "
            f"<a href='{NEXUS}/548?tab=files'>Mod Menu</a>.</li>"
            "<li>No luck with Mod Manager Download, or the mod is on CurseForge? Use <b>Manual download</b> "
            "(Nexus) or <b>Download</b> (CurseForge): while MO2 is open, the file jumps from your Downloads "
            "folder into MO2's <b>Downloads</b> tab.</li>"
            "<li>Double-click each one in the <b>Downloads</b> tab to install it; it lands under its category "
            "in the left list. (Want it automatic? Settings &gt; Plugins &gt; RuneScape Dragonwilds Support &gt; auto_install.)</li>"
            "<li>Get any other mod the same way and press <b>Run</b>.</li>"
            "</ol>"
            "<p>If <b>Mod Manager Download</b> opens another app (like Vortex) or nothing happens, "
            "close your web browser completely and open it again. Browsers remember the old app until restarted.</p>"
            "<p>Always start the game from MO2. Mod order on the left is the RuneSchema load order.</p>"
            f"<p>Need help? <a href='{link}'>Join our Discord</a></p>"
        )
        box.exec()

    def _add_discord(self, main_window: QMainWindow):
        bar = main_window.findChild(QToolBar, "toolBar")
        if bar is None:
            return
        link = self._organizer.pluginSetting(self.name(), "discord_link") or DISCORD
        button = QToolButton(bar)
        button.setObjectName("dragonwildsDiscord")
        button.setText(" Join our Discord")
        button.setToolTip(f"Help, news and mod talk\n{link}")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        icon = Path(__file__).with_name(DISCORD_ICON)
        if icon.is_file():
            button.setIcon(QIcon(str(icon)))
            button.setIconSize(QSize(26, 26))
        button.setStyleSheet(
            "QToolButton#dragonwildsDiscord { background: #5865f2; color: white; border: 1px solid #8b94ff;"
            " border-radius: 8px; padding: 4px 12px 4px 8px; margin: 2px 6px; font: bold 13px 'Segoe UI'; }"
            "QToolButton#dragonwildsDiscord:hover { background: #6d78ff; border-color: #f0b44c; }"
            "QToolButton#dragonwildsDiscord:pressed { background: #4752c4; }"
        )
        button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(link)))
        bar.addWidget(button)

    def _is_game(self, app_path: str) -> bool:
        return fold(os.path.basename(app_path)) in (fold(SHIPPING), fold(LAUNCHER))

    def _on_about_to_run(self, app_path: str, _wd, _args) -> bool:
        if not self.isActive():
            return True
        self._running = True
        self.sync_now()
        try:
            Path(self.dataDirectory().absolutePath(), PAK_MODS).mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        if self._setting("sort_overwrite"):
            try:
                self.order.tidy_overwrite()
            except OSError:
                pass
        if self._is_game(app_path) and self._setting("helpy_mirror"):
            try:
                self.order.deploy_mirror()
            except OSError:
                pass
        if self._is_game(app_path) and self._setting("swap_ue4ss_loader"):
            self._swap_loader()
        return True

    def _on_finished_run(self, app_path: str, _code: int):
        if not self.isActive():
            return
        self._running = False
        self._restore_loader()
        try:
            self.order.remove_mirror()
        except OSError:
            pass
        self.order.import_runtime_changes()
        self._sort_overwrite_later()
        self.sync_later()

    def _sort_overwrite_later(self):
        QTimer.singleShot(1500, self._housekeeping)
        QTimer.singleShot(15000, self._fix_versions)

    def _fix_versions(self) -> int:
        if not self.isActive() or self._running:
            return 0
        if not self._setting("match_nexus_versions"):
            return 0
        modlist = self._organizer.modList()
        fixed = 0
        for name in modlist.allMods():
            mod = modlist.getMod(name)
            if mod is None or mod.isSeparator() or mod.isOverwrite() or mod.isForeign():
                continue
            try:
                if int(mod.nexusId()) <= 0:
                    continue
                newest, current = mod.newestVersion(), mod.version()
                if newest.isValid() and current.isValid() and newest < current:
                    mod.setVersion(newest)
                    fixed += 1
            except Exception:
                pass
        return fixed

    def _housekeeping(self):
        if not self.isActive():
            return
        if self._busy or self._running:
            QTimer.singleShot(5000, self._housekeeping)
            return
        self._busy = True
        try:
            self._housekeeping_now()
        finally:
            self._busy = False

    def _housekeeping_now(self):
        changed = 0
        if self._setting("sort_overwrite"):
            try:
                changed += self.order.tidy_overwrite()
            except Exception:
                pass
        if self._setting("mod_notes") or self._setting("mod_categories"):
            changed += self._apply_notes()
        first_layout = self._setting("mod_separators") and not self._setting("separators_made", False)
        if first_layout and self._has_own_mods() and not self._ask_layout():
            self._organizer.setPluginSetting(self.name(), "separators_made", True)
            first_layout = False
        if first_layout:
            changed += self.order.ensure_separators()
        if changed:
            self._organizer.refresh()
        try:
            if first_layout:
                self.order.organize_all()
                self._organizer.setPluginSetting(self.name(), "separators_made", True)
                self._pending_place.clear()
            elif self._setting("mod_separators"):
                for name in list(self._pending_place):
                    if self.order.place(name):
                        self._pending_place.discard(name)
            self.sync_now()
        except Exception:
            pass
        self._link_nexus_ids()
        self._fix_versions()

    def _link_nexus_ids(self) -> int:
        if not self.isActive() or self._running or not self._setting("link_nexus_ids"):
            return 0
        entries = load_notes()
        modlist = self._organizer.modList()
        linked = 0
        for name in modlist.allMods():
            mod = modlist.getMod(name)
            if mod is None or mod.isSeparator() or mod.isOverwrite() or mod.isForeign() or mod.isBackup():
                continue
            try:
                if int(mod.nexusId()) > 0:
                    continue
                rank = master_rank(mod.fileTree())
                nexus = MASTER_NEXUS[rank] if 0 <= rank < len(MASTER_NEXUS) else None
                if nexus is None:
                    entry = match_note(mod, entries) if entries else None
                    nexus = entry.get("nexus_id") if entry else None
                if nexus:
                    mod.setNexusID(int(nexus))
                    linked += 1
            except Exception:
                pass
        return linked

    def _link_source_page(self, mod: mobase.IModInterface):
        try:
            if mod.url():
                return
            installed = QSettings(str(Path(mod.absolutePath(), "meta.ini")), QSettings.Format.IniFormat)
            archive = str(installed.value("installationFile", "") or "")
            if not archive:
                return
            source = Path(archive) if Path(archive).is_absolute() else Path(self._organizer.downloadsPath(), archive)
            meta = QSettings(f"{source}.meta", QSettings.Format.IniFormat)
            page = str(meta.value("url", "") or "")
            if str(meta.value("repository", "")) == "CurseForge" and CURSEFORGE_PAGE.match(page):
                mod.setUrl(page)
        except Exception:
            pass

    def _has_own_mods(self) -> bool:
        modlist = self._organizer.modList()
        for name in modlist.allMods():
            mod = modlist.getMod(name)
            if mod is None or mod.isSeparator() or mod.isOverwrite() or mod.isBackup() or mod.isForeign():
                continue
            if master_rank(mod.fileTree()) < 0:
                return True
        return False

    def _ask_layout(self) -> bool:
        answer = QMessageBox.question(
            getattr(self, "_main", None),
            "RuneScape: Dragonwilds - Category separators",
            "Group your mod list under category separators (Master Files, Utilities, User Interface, "
            "Gameplay ...)?\n\nThis changes the order of your mod list, and the RuneSchema load order "
            "follows the mod list. You can say No and turn it on later in Settings > Plugins "
            "(untick separators_made).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _on_installed(self, mod: mobase.IModInterface):
        if not self.isActive():
            return
        if mod is not None and not mod.isSeparator():
            self._pending_place.add(mod.name())
            self._link_source_page(mod)
        self.sync_later()
        self._sort_overwrite_later()

    def _on_download_complete(self, download_id: int):
        if not self.isActive() or not self._setting("auto_install", False):
            return
        try:
            path = Path(self._organizer.downloadManager().downloadPath(download_id))
        except Exception:
            return
        if fold(path.name) in self._queried:
            return
        QTimer.singleShot(1500, lambda: self._auto_install(path))

    def _auto_install(self, path: Path):
        if not self.isActive():
            return
        if not self._setting("auto_install", False) or not path.is_file():
            return
        if self._busy or self._running:
            QTimer.singleShot(5000, lambda: self._auto_install(path))
            return
        meta = QSettings(f"{path}.meta", QSettings.Format.IniFormat)
        if fold(str(meta.value("gameName", ""))) != fold(self.GameShortName):
            return
        if str(meta.value("installed", "false")).casefold() == "true":
            return
        silent = self._organizer.pluginSetting("Simple Installer", "silent")
        self._organizer.setPluginSetting("Simple Installer", "silent", True)
        self._busy = True
        try:
            mod = self._organizer.installMod(str(path), str(meta.value("modName", "") or ""))
        except Exception:
            mod = None
        finally:
            self._busy = False
            self._organizer.setPluginSetting("Simple Installer", "silent", bool(silent))
        if mod is None:
            return
        self._organizer.modList().setActive(mod.name(), True)
        self._pending_place.add(mod.name())
        QTimer.singleShot(2000, self._housekeeping)
        QTimer.singleShot(16000, self._housekeeping)

    def _apply_notes(self) -> int:
        entries = load_notes()
        modlist = self._organizer.modList()
        written = 0
        for name in modlist.allMods():
            mod = modlist.getMod(name)
            if mod is None or mod.isSeparator() or mod.isOverwrite() or mod.isForeign():
                continue
            entry = match_note(mod, entries) if entries else None
            try:
                if entry is not None and self._setting("mod_notes") and write_note(mod, entry):
                    written += 1
                if self._setting("mod_categories"):
                    if master_rank(mod.fileTree()) >= 0:
                        category = MASTER_CAT[0]
                    elif entry and entry.get("category"):
                        category = CAT_IDS.get(fold(entry["category"]))
                    else:
                        category = nexus_category(mod)
                    if category and write_category(mod, category):
                        written += 1
            except Exception:
                pass
        return written

    def _swap_loader(self):
        win64 = self._win64()
        proxy, loader, mark = win64 / PROXY, win64 / LOADER, win64 / SWAP_MARK
        if not proxy.is_file() or not (win64 / "ue4ss" / "UE4SS.dll").is_file():
            return
        try:
            if loader.exists():
                if mark.exists():
                    loader.unlink()
                else:
                    proxy.replace(win64 / (PROXY + ".mo2off"))
                    mark.write_text(PROXY + ".mo2off", encoding="utf-8")
                    return
            proxy.rename(loader)
            mark.write_text(LOADER, encoding="utf-8")
        except OSError:
            pass

    def _restore_loader(self):
        win64 = self._win64()
        mark = win64 / SWAP_MARK
        if not mark.is_file():
            return
        try:
            moved = win64 / mark.read_text(encoding="utf-8").strip()
            proxy = win64 / PROXY
            if moved.is_file() and not proxy.exists():
                moved.rename(proxy)
            mark.unlink()
        except OSError:
            pass

    def _virtual_has(self, path: str) -> bool:
        try:
            return self._organizer.virtualFileTree().find(path) is not None
        except Exception:
            return False

    def _mods_with_proxy(self) -> list[mobase.IModInterface]:
        return [mod for _, mod in self.order._active_mods() if mod.fileTree().find(f"{WIN64}/{PROXY}")]

    def activeProblems(self) -> list[int]:
        if not self.isActive():
            return []
        problems: list[int] = []
        win64 = self._win64()
        physical = (win64 / PROXY).is_file() or (win64 / LOADER).is_file()
        if self._mods_with_proxy():
            problems.append(Problem.PROXY_IN_MOD)
        elif not physical and not self._virtual_has(f"{WIN64}/{LOADER}"):
            problems.append(Problem.UE4SS_MISSING)
        if (win64 / PROXY).is_file() and not self._setting("swap_ue4ss_loader"):
            problems.append(Problem.PROXY_IN_GAME)
        if self.order.discover() and not self._virtual_has(f"{RS_ROOT}/dlls/main.dll"):
            problems.append(Problem.RUNESCHEMA_MISSING)
        if self._virtual_has(f"{RS_ROOT}/dlls/main.dll") and not self._virtual_has(f"{UE4SS_MODS}/ModMenu"):
            problems.append(Problem.MODMENU_MISSING)
        return problems

    def shortDescription(self, key: int) -> str:
        return {
            Problem.UE4SS_MISSING: "UE4SS is not installed.",
            Problem.PROXY_IN_MOD: "A UE4SS mod in MO2 still uses dwmapi.dll.",
            Problem.PROXY_IN_GAME: "UE4SS's dwmapi.dll is in the game folder.",
            Problem.RUNESCHEMA_MISSING: "RuneSchema mods are installed but RuneSchema is not.",
            Problem.MODMENU_MISSING: "Mod Menu (master file) is not installed.",
        }.get(key, "")

    def fullDescription(self, key: int) -> str:
        return {
            Problem.UE4SS_MISSING: (
                "Lua and RuneSchema mods need UE4SS. Install 'UE4SS for RSDragonwilds' "
                "(Nexus mod 4, file 'UE4SS Steam (latest) 3.0.1-gf6d5f942') through MO2 like any "
                "other mod. MO2 renames its dwmapi.dll to ue4ss_loader.dll and loads it for you."
            ),
            Problem.PROXY_IN_MOD: (
                "dwmapi.dll is loaded by Windows before MO2's virtual folder is ready, so it never "
                "loads from a mod. The fix renames it to ue4ss_loader.dll, which this plugin loads "
                "into the game at the right moment."
            ),
            Problem.PROXY_IN_GAME: (
                "UE4SS's dwmapi.dll in the game folder starts before MO2's virtual folder, so mods "
                "installed in MO2 may not be seen. Turn on the 'swap_ue4ss_loader' setting, or let "
                "the fix rename it to ue4ss_loader.dll (UE4SS then only runs when started from MO2)."
            ),
            Problem.RUNESCHEMA_MISSING: (
                "Some mods have RuneSchema content, but RuneSchema itself (ue4ss/Mods/RuneSchema "
                "with dlls/main.dll) is not installed. Install RuneSchema from Nexus mod 570 through MO2."
            ),
            Problem.MODMENU_MISSING: (
                "Mod Menu by Maxxfilth is one of the three master files (UE4SS, RuneSchema, Mod Menu). "
                "Many mods put their settings in it. Install it from Nexus mod 548 through MO2; it is locked "
                "at the top of the mod list automatically."
            ),
        }.get(key, "")

    def hasGuidedFix(self, key: int) -> bool:
        return key in (Problem.PROXY_IN_MOD, Problem.PROXY_IN_GAME)

    def startGuidedFix(self, key: int) -> None:
        if key == Problem.PROXY_IN_MOD:
            for mod in self._mods_with_proxy():
                source = Path(mod.absolutePath(), WIN64, PROXY)
                try:
                    source.replace(source.with_name(LOADER))
                    self._organizer.modDataChanged(mod)
                except OSError:
                    pass
        elif key == Problem.PROXY_IN_GAME:
            win64 = self._win64()
            try:
                (win64 / PROXY).replace(win64 / LOADER)
            except OSError:
                pass
        self.sync_later()

