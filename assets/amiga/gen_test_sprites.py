import bitplanelib,struct

with open("andor_sprites_dump_1","rb") as f:
    contents = f.read()

new_data = []
for i in range(0,len(contents),8):
    (tile,state,x,y) = struct.unpack_from(">BBHH",contents,i+2)
    if state == 3:
        print(hex(tile),x,y)
    new_data.append(contents[i:i+8]+bytes(4))

with open("../../src/amiga/ag_test.68k","w") as f:
    f.write("ag_sprites:")
    bitplanelib.dump_asm_bytes(b"".join(new_data),f,mit_format=True)