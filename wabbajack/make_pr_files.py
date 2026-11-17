# Made by Claude Ai & Relic Hunter
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "pr", "Wabbajack.DTOs", "Game")
RAW = "https://raw.githubusercontent.com/wabbajack-tools/wabbajack/main/Wabbajack.DTOs/Game/{}"


def fetch(name):
    with urllib.request.urlopen(RAW.format(name)) as r:
        return r.read()


def main():
    os.makedirs(OUT, exist_ok=True)
    game = fetch("Game.cs")
    nl = b"\r\n" if b"\r\n" in game else b"\n"
    anchor = b'    [Description("Dune: Awakening")] DuneAwakening,' + nl
    assert game.count(anchor) == 1, "Game.cs anchor not found"
    game = game.replace(anchor, anchor + b'    [Description("RuneScape: Dragonwilds")] RuneScapeDragonwilds,' + nl)

    reg = fetch("GameRegistry.cs")
    rnl = b"\r\n" if b"\r\n" in reg else b"\n"
    anchor = b"        {" + rnl + b"            Game.ModdingTools, new GameMetaData"
    assert reg.count(anchor) == 1, "GameRegistry.cs anchor not found"
    entry = rnl.join([
        b"        {",
        b"            Game.RuneScapeDragonwilds, new GameMetaData",
        b"            {",
        b"                Game = Game.RuneScapeDragonwilds,",
        b'                MO2Name = "RuneScape: Dragonwilds",',
        b'                NexusName = "runescapedragonwilds",',
        b"                NexusGameId = 7597,",
        b'                MO2ArchiveName = "runescapedragonwilds",',
        b"                SteamIDs = [1374490],",
        b"                RequiredFiles = new []",
        b"                {",
        b'                    @"RSDragonwilds\\Binaries\\Win64\\RSDragonwilds-Win64-Shipping.exe".ToRelativePath(),',
        b"                },",
        b'                MainExecutable = @"RSDragonwilds\\Binaries\\Win64\\RSDragonwilds-Win64-Shipping.exe".ToRelativePath(),',
        b"            }",
        b"        },",
    ]) + rnl
    reg = reg.replace(anchor, entry + anchor)
    for name, data in (("Game.cs", game), ("GameRegistry.cs", reg)):
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(data)
        print(name, len(data), "bytes", "CRLF" if b"\r\n" in data else "LF")


if __name__ == "__main__":
    main()
