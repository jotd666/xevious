import bitplanelib

with open("andor_sprites_dump_1","rb") as f:
    contents = f.read()

with open("../../src/amiga/ag_test.68k","w") as f:
    f.write("ag_sprites:")
    bitplanelib.dump_asm_bytes(contents,f,mit_format=True)