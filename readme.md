Xevious (68K)

This is a transcode from the original arcade game (multiple Z80s) to 68K assembly.

The original GAME and SUB CPU ROMs were disassembled and reverse-engineered. Then the code was transcoded line-by-line to 68K assembly. The 'core' code is platform-agnostic and calls out to an operating system dependent (OSD) layer written for each target platform.

The original target is the Neo Geo (AES/MVS/CD). It runs in 'tate' mode.

Subsequent targets include the AGA Amiga.

In theory the core can be ported easily to any 68K target that can support the resolution, number of sprites (performance) and palette.

PROGRESS:

The core transcode is 100% complete. One "last" gameplay bug to be confirmed.

The Neo Geo target is playable with sound on an emulator and also on real hardware (tested on an AES with NeoSD cartridge and NGCD). Beta1 has been released (https://tcdev.itch.io/xevious).

The Amiga target is playable. A1200 with fast memory is recommended.

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
- Andrzej Dobrowolski (aka no9): Amiga music
- DanyPPC: Amiga icon
- phx: ptplayer sound/music replay Amiga code
- Namco: original game :)

CONTROLS (Amiga: 2-button joystick recommended):

- red/fire: fire/start game (from menu)
- blue/2nd button/space/left shift: bomb/insert coin (from menu)
- green/5 key: insert coin
- yellow/1 key: start game
- 2 key: start game (2P game)
- play/P key: pause

REBUILDING FROM SOURCES:

NEO GEO:

Prerequesites:

- Windows
- NeoDev kit (Fabrice Martinez, Jeff Kurtz, et al)  
  https://wiki.neogeodev.org/index.php?title=Development_tools

Build process:

- install NeoDev and set path accordingly
- clone repository
- make -f makefile.ng OUTPUT={cart|cd}
  - (OUTPUT defaults to cart)
  
Install process (MAME):

- make -f makefile.ng OUTPUT={cart|cd} MAMEDIR={mamedir} install
  - (mamedir defaults to '.')
- paste xevious.xml into MAME's hash/neogeo.xml file

To run in MAME:

- cart : 'mame neogeo xevious'
- cd : 'mame neocdz -cdrom roms/neocdz/xevious.iso'
  
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
  just run the "convert_graphics.py" python script, 
- To update sounds, use "convert_sounds.py"
  python script (audio) to create sound*.68k files.

