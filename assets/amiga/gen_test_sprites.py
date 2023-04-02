import bitplanelib,struct

with open("sprite_log_bridge_jet","rb") as f:
    contents = f.read()

new_data = []
for i in range(0,len(contents),12):
    (state,_,tile,color,x,y) = struct.unpack_from(">BBBBHH",contents,i)
    if state == 3:
        print(hex(tile),x,y)
    new_data.append(contents[i:i+12])

with open("../../src/amiga/ag_test.68k","w") as f:
    f.write("ag_sprites:")
    bitplanelib.dump_asm_bytes(b"".join(new_data),f,mit_format=True)