Xevious (68K)

This is a transcode from the original arcade game (multiple Z80s) to 68K assembly.

The original GAME and SUB CPU ROMs were disassembled and reverse-engineered. Then the code was transcoded line-by-line to 68K assembly. The 'core' code is platform-agnostic and calls out to an operating system dependent (OSD) layer written for each target platform.

The original target is the Neo Geo (AES/MVS/CD). It runs in 'tate' mode.

Subsequent targets include the Amiga (requirements TBD).

In theory the core can be ported easily to any 68K target that can support the resolution, number of sprites (performance) and palette.

PROGRESS:

The core transcode is 100% complete. One "last" gameplay bug to be confirmed.

The Neo Geo target is playable with sound on an emulator and also on real hardware (tested on an AES with NeoSD cartridge and NGCD).

The Amiga target is playable.

FEATURES:

- game play is identical to the original arcade game, including the pseudo-random
  number generation
- original dipswitch options supported (except cocktail cabinet mode)
- all original graphics and colours reproduced perfectly on Neo Geo target
- 1 or 2 players supported
- high score load/save

CREDITS:

- Mark McDougall (aka tcdev): reverse-engineering, core and Neo Geo code and assets
- Jean-Francois Fabre (aka jotd): Amiga code and assets
- Namco: original game :)

REBUILDING FROM SOURCES:

NEO GEO:

Prerequesites:

- Windows
- NeoDev kit (Fabrice Martinez, Jeff Kurtz, et al)  
  https://wiki.neogeodev.org/index.php?title=Development_tools
- puzzledp ROM files

Build process:

- install NeoDev and set path accordingly
- clone repository
- unzip original puzzledp roms in 'roms/puzzledp' subdirectory
- set PLATFORM=neogeo in makefile
- make

AMIGA:

Prerequesites:

- Bebbo's amiga gcc compiler
- Windows
- python
- sox
- "bitplanelib.py" (asset conversion tool needs it) at https://github.com/jotd666/amiga68ktools.git

Build process:

- install above tools & adjust python paths
- make -f makefile.am

When changing asset-related data (since dependencies aren't good):

- To update the "graphics.68k" & "palette*.68k" files from "assets/amiga" subdir, 
  just run the "convert_sprites.py" python script, 
- To update sounds, use "convert_sounds.py"
  python script (audio) to create sound*.68k files.

