Xevious (68K)

This is a transcode from the original arcade game (multiple Z80s) to 68K assembly.

The original GAME and SUB CPU ROMs were disassembled and reverse-engineered. Then the code was transcoded line-by-line to 68K assembly. The 'core' code is platform-agnostic and calls out to an operating system dependent (OSD) layer written for each target platform.

The original target is the Neo Geo (AES/MVS/CD). It runs in 'tate' mode.

Subsequent targets include the Amiga (requirements TBD).

In theory the core can be ported easily to any 68K target that can support the resolution, number of sprites (performance) and palette.

PROGRESS:

The core transcode is complete, except for a few minor bugs. There is also currently no provision for sound in the core (TBD).

The Neo Geo target is essentially playable on an emulator. It runs but requires some optimisations in the Neo Geo OSD layer before it will run at 100% on real hardware.

The Amiga target is early WIP.

FEATURES:

- game play is identical to the original arcade game, including the pseudo-random
  number generation
- original dipswitch options supported (except cocktail cabinet mode)
- all original graphics and colours reproduced perfectly on Neo Geo target
- 1 or 2 players supported

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

Build process:

- install NeoDev and set path accordingly
- make

AMIGA:

(TBA)
