Made by Claude Ai & Relic Hunter

RuneScape: Dragonwilds - Mod Organizer 2 (Stand-alone) 1.0.0
=============================================================

A ready-to-go Mod Organizer 2 (MO2) for Dragonwilds. Unzip it, start it, download mods
from Nexus. MO2 keeps every mod in its own folder instead of copying it into the game, so
a broken mod can't damage your game install.

WHAT YOU GET
- MO2 2.5.2 already set up for RuneScape: Dragonwilds (your Steam game is found by itself).
- "Mod Manager Download" on Nexus sends mods straight into MO2's Downloads tab.
- Manual downloads from Nexus and CurseForge work too: while MO2 is open, a Dragonwilds mod
  you save to your Windows Downloads folder is MOVED into MO2's Downloads tab. Nexus files get
  their Nexus info filled in; CurseForge mods are linked to their CurseForge page (right-click
  the mod > Visit web page). Only files that contain Dragonwilds content are taken; for .7z and
  .rar files MO2 asks first. MO2 can't check CurseForge mods for updates.
- Drop-in installs: every mod lands in the right game folder by itself (UE4SS mods, RuneSchema
  mods, pak mods).
- Installs are manual: double-click a download in the Downloads tab.
- Master files: UE4SS, RuneSchema and Mod Menu stay locked at the top of your mod list.
- Nexus's Dragonwilds categories (Gameplay, Armour, Spells, User Interface ...) with matching
  separators in the mod list. New mods are filed under their category.
- RuneSchema tab: the RuneSchema load order follows the left list.
- Short how-to notes on Relic Hunter's mods (hover the note icon in the mod list).
- Files the game writes (logs, mod data) go back into the mod they belong to, not Overwrite.
- Profile-specific saves and game INI files (Engine.ini, GameUserSettings.ini, Input.ini)
  work like in other MO2 games (Profiles window).
- Built-in fixes: UE4SS starts before the game engine (so RuneSchema sees every mod),
  RuneSchema's Helpy window (F2) works, and MO2's "newer than Nexus" and "info missing"
  warnings are cleared.
- Dragonwilds theme, splash screen and a Discord button at the top right.

INSTALL
1. Unzip the "Dragonwilds MO2" folder somewhere outside Program Files and outside the game
   folder, for example C:\Modding\Dragonwilds MO2.
2. Start ModOrganizer.exe. A "Getting started" window shows the next steps.
3. Settings (tools icon) > Nexus > Connect to Nexus, and log in.
4. On Nexus press "Mod Manager Download" (or Manual download) for the three master files first:
   - UE4SS for RSDragonwilds (mod 4, file "UE4SS Steam (latest) 3.0.1-gf6d5f942")
   - RuneSchema 0.9.0.0 (mod 570)
   - Mod Menu (mod 548)
5. Double-click each download in the Downloads tab to install it, tick it in the left list.
6. Add any other mods the same way and press Run.

If Windows asks which app should open Nexus links, pick Mod Organizer.
If "Mod Manager Download" opens Vortex or nothing happens, close your web browser completely
(every window) and open it again. Browsers remember the old download app until restarted.
If MO2 can't find the game, point it at the folder that has RSDragonwilds.exe in it.

ALWAYS START THE GAME FROM MO2
Starting from Steam skips MO2, so no mods load.

RUNESCHEMA LOAD ORDER
With "Follow the mod list" ticked in the RuneSchema tab (the default), drag mods in the left
list to change the order. The on/off ticks in the tab always work. To set the order by hand
in runeschema.txt, untick "Follow the mod list" first, or your order is replaced by the
mod list order.

WHAT MO2 CHANGES IN YOUR GAME FOLDER
- Creates the empty folder RSDragonwilds\Content\Paks\~mods if it is missing.
- While the game runs from MO2: a folder link RSDragonwilds\Binaries\Win64\ue4ss\Mods\RuneSchema
  that points at the RuneSchema mod in MO2 (so Helpy can find it). It is removed when the game
  closes, or the next time MO2 starts. It is only made if that folder doesn't already exist.
- Only if you installed UE4SS by hand: its dwmapi.dll is renamed ue4ss_loader.dll while the
  game runs from MO2 and put back afterwards.
Nothing else in the game folder is changed.

IF YOU ALREADY MODDED BY HAND
Mods copied straight into the game folder still load and will show up twice next to the MO2
copies. For a clean start: delete RSDragonwilds\Binaries\Win64\ue4ss and dwmapi.dll from the
game folder, then use Steam > Verify integrity of game files.

TURNING FEATURES OFF
Settings > Plugins > RuneScape Dragonwilds Support:
- auto_install (off by default) - install and switch on every finished download
- forward_downloads - manual downloads moved into MO2
- mod_separators / separators_made - category separators (untick separators_made to regroup)
- mod_categories, mod_notes, sort_overwrite, match_nexus_versions
- lock_master_files, follow_mod_order, discord_panel, helpy_mirror

PROBLEMS
- The warning triangle in MO2's toolbar lists anything missing (UE4SS, RuneSchema, Mod Menu).
- UE4SS log: right-click UE4SS in the mod list > Open in Explorer >
  Binaries\Win64\ue4ss\UE4SS.log
- RuneSchema log: the same inside the RuneSchema mod > Binaries\Win64\ue4ss\Mods\RuneSchema\
  RuneSchema.log
- Antivirus: rsdragonwilds_ue4ss_boot.dll (in plugins\basic_games\games) is a 1.5 KB helper
  that makes UE4SS start before the game engine. Its full source is in
  "Dragonwilds - Source\build_bootstrap_dll.py". If your antivirus blocks it, allow it.
- Discord: discord.gg/BumVNYDUec (or the Discord button in MO2)

UNINSTALL
Delete the "Dragonwilds MO2" folder. Your game folder needs nothing removed (see above).

Mod Organizer 2 is free software (GPLv3) by the Mod Organizer 2 team. This is the official
2.5.2 release with our Dragonwilds game plugin and theme added. Licenses are in the licenses
folder; sources and credits are listed in "Dragonwilds - THIRD-PARTY.txt".
