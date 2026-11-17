# Wabbajack pull request (to github.com/wabbajack-tools/wabbajack, branch main)

## Title
Add RuneScape: Dragonwilds

## Description
Adds RuneScape: Dragonwilds (Steam 1374490, Nexus `runescapedragonwilds` / game id 7597).

MO2 support comes from a basic_games game plugin (`game_rsdragonwilds.py`: GameName "RuneScape: Dragonwilds",
short name `runescapedragonwilds`), which matches `MO2Name` / `MO2ArchiveName` below. Tested on MO2 2.5.2 with a
Stock Game copy: UE4SS, Lua mods, RuneSchema content and pak mods all load through the VFS.

Same two-file change as the Dune: Awakening and Alice additions.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Change 1: Wabbajack.DTOs/Game/Game.cs (add one line at the end of the enum, after DuneAwakening)
```csharp
    [Description("RuneScape: Dragonwilds")] RuneScapeDragonwilds,
```

## Change 2: Wabbajack.DTOs/Game/GameRegistry.cs (add before the ModdingTools entry)
```csharp
        {
            Game.RuneScapeDragonwilds, new GameMetaData
            {
                Game = Game.RuneScapeDragonwilds,
                MO2Name = "RuneScape: Dragonwilds",
                NexusName = "runescapedragonwilds",
                NexusGameId = 7597,
                MO2ArchiveName = "runescapedragonwilds",
                SteamIDs = [1374490],
                RequiredFiles = new []
                {
                    @"RSDragonwilds\Binaries\Win64\RSDragonwilds-Win64-Shipping.exe".ToRelativePath(),
                },
                MainExecutable = @"RSDragonwilds\Binaries\Win64\RSDragonwilds-Win64-Shipping.exe".ToRelativePath(),
            }
        },
```

## After it is merged and Wabbajack releases it
1. Install the mods into the MO2 test instance through MO2's Nexus downloads (so each mod knows its Nexus file).
2. Compile the list with Wabbajack (Stock Game folder included, plugin + theme ride along inside MO2).
3. Share the .wabbajack file, or ask the Wabbajack team for a gallery listing.
