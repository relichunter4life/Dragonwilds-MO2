<!-- Made by Claude Ai & Relic Hunter -->

# Dragonwilds MO2

**Mod Organizer 2 support for RuneScape: Dragonwilds.** It manages UE4SS Lua mods, RuneSchema mods and pak mods, and keeps the RuneSchema load order in step with your mod list. It also comes with a Dragonwilds theme.

![Dragonwilds MO2 theme](theme/preview-mo2-theme.jpg)

## Downloads

Get them from the [Releases](../../releases) page:

| File | What it is |
|---|---|
| `Dragonwilds-MO2-Standalone-1.0.2.zip` | A complete, ready-to-go MO2 2.5.2 for Dragonwilds. Unzip it and start it. |
| `Dragonwilds-MO2-Support-1.0.2.zip` | An add-on for an MO2 2.5.2 you already have. |

## Supported files from Nexus

Install these in MO2 first. Dragonwilds MO2 locks them at the top of your mod list as **Master Files**. Click **Mod Manager Download** on each page and MO2 picks them up.

| Mod | File to get | Why |
|---|---|---|
| [UE4SS for RSDragonwilds](https://www.nexusmods.com/runescapedragonwilds/mods/4?tab=files&file_id=2111) | **UE4SS Steam (latest)** 3.0.1-gf6d5f942 | Runs every Lua mod |
| [RuneSchema](https://www.nexusmods.com/runescapedragonwilds/mods/570?tab=files&file_id=3921) | **RuneSchema** 0.9.0.0 (latest) | Loads RuneSchema item, recipe and building mods |
| [Mod Menu](https://www.nexusmods.com/runescapedragonwilds/mods/548?tab=files&file_id=3683) | **Mod Menu** 2.0.3 | In-game settings for your mods |

## Features

- **Installs in the right place:** UE4SS mods go to `ue4ss/Mods`, RuneSchema core and content to `ue4ss/Mods/RuneSchema/mods`, and pak mods to `Content/Paks/~mods`. A mod that ships both a mod folder and a RuneSchema folder stays one entry.
- **Master files:** UE4SS, RuneSchema and Mod Menu are locked at the top of the list, under a *Master Files* separator.
- **RuneSchema tab:** `runeschema.txt` follows the left list, and you can switch mods on and off. UE4SS `mods.txt` is written for you.
- **UE4SS start fix:** a 1.5 KB boot DLL makes UE4SS start before the game engine, so RuneSchema sees every pak and DataTable. The source is in [`tools/build_bootstrap_dll.py`](tools/build_bootstrap_dll.py).
- **Helpy works:** RuneSchema's Helpy window finds RuneSchema through a temporary folder link that MO2 removes when the game closes.
- **Downloads:**
  - Nexus "Mod Manager Download" sends mods to MO2.
  - Manual downloads from **Nexus** and **CurseForge** are moved into MO2's Downloads tab, but only files that really contain Dragonwilds content.
  - MO2 looks up the Nexus info for each file.
  - Auto-install is optional and off by default.
- **Categories and separators:** Nexus's Dragonwilds categories, with matching separators in the mod list. Short how-to notes are added to Relic Hunter's mods.
- **Tidy Overwrite:** logs and data the game writes go back into the mod that owns them.
- **Same game settings as Steam:** the game always reads its normal settings files, so graphics and keys match a Steam start. Profile-specific saves and save game listing work like other MO2 games.
- **Updates itself:** once a day the plugin checks this repository's latest release and offers *Update now*. It replaces only the Dragonwilds plugin and theme files (setting `check_updates`).
- **Theme:** a Dragonwilds theme and splash, plus a Discord button.

## Install

**Stand-alone:** unzip the `Dragonwilds MO2` folder outside Program Files and start `ModOrganizer.exe`. A *Getting started* window walks you through the rest.

**Add-on:** install [MO2 2.5.2](https://github.com/ModOrganizer2/modorganizer/releases/tag/v2.5.2), unzip the add-on into the MO2 folder, then create a new instance for *RuneScape: Dragonwilds*.

Both READMEs (`pack/`) explain:
- what MO2 changes in the game folder
- how to turn each feature off
- where the logs are
- how to uninstall

## Repository layout

| Folder | Contents |
|---|---|
| `plugin/` | The game plugin (`game_rsdragonwilds.py`), the boot DLL, mod notes and the Discord icon |
| `theme/` | The QSS theme and art; `make_theme_art.py` rebuilds the art |
| `pack/` | The player READMEs and the third-party notice |
| `tools/` | `build_pack.py` and `build_standalone.py` make the zips; `build_bootstrap_dll.py` rebuilds the boot DLL |
| `tests/` | Offline tests: archive layouts and download detection (`python tests/test_checker.py`) |
| `wabbajack/` | The Wabbajack game-registry entry for RuneScape: Dragonwilds |

**Dev tools:**
- They expect an MO2 2.5.2 folder at `D:\Modding\MO2-Dragonwilds`. Pass another path as the first argument to `build_standalone.py`.
- The tests need MO2's Python 3.12 libraries.

## Links

- Discord: [discord.gg/BumVNYDUec](https://discord.gg/BumVNYDUec)
- Nexus: [Dragonwilds MO2](https://www.nexusmods.com/runescapedragonwilds/mods/916)

## License

[GPL v3](LICENSE), the same license as Mod Organizer 2. See [`pack/THIRD-PARTY.txt`](pack/THIRD-PARTY.txt) for MO2's sources and the font and art credits. This is a fan project; it is not made or endorsed by Jagex Ltd.
