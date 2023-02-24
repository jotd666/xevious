# decodes memory dump of 8-bytes each sprite structure (8*64)
# and prints x,y,sprite type...

import struct,os
from PIL import Image

this_dir = os.path.dirname(__file__)

dump_dir = os.path.join(this_dir,"dumps","sprite","raw")
prefix = "andor_genesis"
# reading memory dump from running game
with open("sprites","rb") as f:
    contents = f.read()

def is_andor_genesis(code):
    return (88 <= code <= 95) or (128 <= code <= 159)


ag_blocks = []

for i in range(64):
    block = contents[i*8:i*8+8]
    if block[0]:
        sprite_code = block[2]
        if is_andor_genesis(sprite_code):
            sprite_color = block[3]
            sprite_attributes = block[1]
            y,x = struct.unpack_from(">HH",block,4)
            ag_blocks.append([x,y,sprite_code,sprite_color,sprite_attributes])

min_x = min(b[0] for b in ag_blocks)
min_y = min(b[1] for b in ag_blocks)

img = Image.new("RGB",(96,96))
for x,y,sprite_code,sprite_color,sprite_attributes in ag_blocks:
    x -= min_x
    y -= min_y
    offsets = [(1,0),(1,1),(0,0),(0,1)] if sprite_attributes == 3 else [(0,0)]
    for i,(xo,yo) in enumerate(offsets):
        source = os.path.join(dump_dir,"{}_{}_{}.png".format(prefix,sprite_code+i,sprite_color))
        src = Image.open(source)
        x_offset = 16*xo
        y_offset = 16*yo
        img.paste(src,(x+x_offset,y+y_offset))

img.save(os.path.join(dump_dir,"..","andor_genesis.png")
