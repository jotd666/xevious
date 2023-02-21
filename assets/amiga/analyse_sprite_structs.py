# decodes memory dump of 8-bytes each sprite structure (8*64)
# and prints x,y,sprite type...

import struct

with open("sprites","rb") as f:
    contents = f.read()

for i in range(64):
    block = contents[i*8:i*8+8]
    if (block[0]):
        sprite_code = block[2]
        sprite_color = block[3]
        sprite_attributes = block[1]
        y,x = struct.unpack_from(">HH",block,4)
        print(x,y,sprite_code,sprite_color,sprite_attributes)
