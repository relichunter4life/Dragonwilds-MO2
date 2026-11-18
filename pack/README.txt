Made by Claude Ai & Relic Hunter

RuneScape: Dragonwilds - Mod Organizer 2 Support 1.0.1
=======================================================

Mod Organizer 2 (MO2) keeps every mod in its own folder instead of copying it into the game.
This pack teaches MO2 how Dragonwilds works: UE4SS mods, RuneSchema mods and pak mods.
(Want MO2 already set up? Get the Stand-alone download instead.)

WHAT YOU GET
- Dragonwilds in MO2's game list (Steam is found automatically).
- Drop-in installs: any mod zip lands in the right game folder by itself.
- Master files: UE4SS, RuneSchema and Mod Menu stay locked at the top of your mod list.
- RuneSchema tab: the RuneSchema load order follows the left list; tick a box to switch a
  RuneSchema mod off. UE4SS mods.txt is written for you from the mod list.
- Manual downloads from Nexus and CurseForge work too: while MO2 is open, a Dragonwilds mod
  you save to your Windows Downloads folder is MOVED into MO2's Downloads tab. Nexus files get
  their Nexus info filled in; CurseForge mods are linked to their CurseForge page (right-click
  the mod > Visit web page). Only files that contain Dragonwilds content are taken; for .7z and
  .rar files MO2 asks first. MO2 can't check CurseForge mods for updates.
- Installs are manual: double-click a download in the Downloads tab.
- Nexus's Dragonwilds categories with matching separators in the mod list. On the first start
  MO2 asks before it regroups an existing mod list. The categories show from the second start.
- Short how-to notes on Relic Hunter's mods (hover the note icon in the mod list).
- Files the game writes (logs, mod data) go back into the mod they belong to, not Overwrite.
- Profile-specific saves and game INI files (Engine.ini, GameUserSettings.ini, Input.ini).
- Built-in fixes: UE4SS starts before the game engine (so RuneSchema sees every mod) and
  RuneSchema's Helpy window (F2) works.
- A Dragonwilds theme, splash screen and a Discord button at the top right.

INSTALL
1. Install Mod Organizer 2 version 2.5.2
   (github.com/ModOrganizer2/modorganizer/releases/tag/v2.5.2).
2. Unzip this pack into the MO2 folder (the one with ModOrganizer.exe). Say Yes to merge folders.
3. Start MO2 and create a new instance. Pick "RuneScape: Dragonwilds" from the game list.
4. Settings (the tools icon) > General > Style: pick "Transparent-Style-Dragonwilds".
   The Dragonwilds splash screen shows from the next start on its own.
5. In MO2, open Settings > Nexus and connect your account, then use "Mod Manager Download"
   (or Manual download) on Nexus for:
   - UE4SS for RSDragonwilds (mod 4, file "UE4SS Steam (latest) 3.0.1-gf6d5f942")
   - RuneSchema 0.9.0.0 (mod 570)
   - Mod Menu (mod 548)
   - then any other mods you want
6. Double-click each download to install it, tick every mod in the left list and press Run.

If "Mod Manager Download" opens Vortex or nothing happens, close your web browser completely
(every window) and open it again. Browsers remember the old download app until restarted.

ALWAYS START THE GAME FROM MO2
Starting from Steam skips MO2, so no mods load.

RUNESCHEMA LOAD ORDER
With "Follow the mod list" ticked in the RuneSchema tab (the default), drag mods in the left
list to change the order. To set the order by hand in runeschema.txt, untick "Follow the mod
list" first, or your order is replaced by the mod list order.

WHAT MO2 CHANGES IN YOUR GAME FOLDER
- Creates the empty folder RSDragonwilds\Content\Paks\~mods if it is missing.
- While the game runs from MO2: a folder link RSDragonwilds\Binaries\Win64\ue4ss\Mods\RuneSchema
  that points at the RuneSchema mod in MO2 (so Helpy can find it). It is removed when the game
  closes, or the next time MO2 starts. It is only made if that folder doesn't already exist.
- Only if you installed UE4SS by hand: its dwmapi.dll is renamed ue4ss_loader.dll while the
  game runs from MO2 and put back afterwards.

IF YOU ALREADY MODDED BY HAND
Mods copied straight into the game folder still load and will show up twice next to the MO2
copies. For a clean start: delete RSDragonwilds\Binaries\Win64\ue4ss and dwmapi.dll from the
game folder, then use Steam > Verify integrity of game files.

TURNING FEATURES OFF
Settings > Plugins > RuneScape Dragonwilds Support: auto_install (off by default),
forward_downloads, mod_separators / separators_made, mod_categories, mod_notes,
sort_overwrite, match_nexus_versions, lock_master_files, follow_mod_order, discord_panel,
helpy_mirror.

PROBLEMS
- The warning triangle in MO2's toolbar lists anything missing (UE4SS, RuneSchema, Mod Menu).
- UE4SS log: right-click UE4SS in the mod list > Open in Explorer >
  Binaries\Win64\ue4ss\UE4SS.log
- Antivirus: rsdragonwilds_ue4ss_boot.dll (in plugins\basic_games\games) is a 1.5 KB helper
  that makes UE4SS start before the game engine. Its full source is in
  "Dragonwilds - Source\build_bootstrap_dll.py". If your antivirus blocks it, allow it.
- Discord: discord.gg/BumVNYDUec

UNINSTALL
Delete from the MO2 folder: plugins\basic_games\games\game_rsdragonwilds.py and the three
rsdragonwilds_* files next to it, stylesheets\Transparent-Style-Dragonwilds.qss,
stylesheets\Transparent-Style\Dragonwilds, "Dragonwilds - Source" and the Dragonwilds text files.
