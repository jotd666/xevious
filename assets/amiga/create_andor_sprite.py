# decodes memory dump of 8-bytes each sprite structure (8*64)
# and prints x,y,sprite type...

import struct,os
from PIL import Image
import bitplanelib

this_dir = os.path.dirname(__file__)

andor_table = [False]*320
for start,stop in ((88,96),(128,159)):
    andor_table[start:stop+1] = [True]*(stop-start+1)


def doit():
    dump_dir = os.path.join(this_dir,"dumps","sprite","raw")
    prefix = "andor_genesis"
    # reading memory dump from running game
    with open("sprites","rb") as f:
        contents = f.read()

    def is_andor_genesis(code):
        return andor_table[code]

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

    img.save(os.path.join(dump_dir,"..","andor_genesis.png"))
    # remove a color so there are 6 colors +1 for transparency, allowing
    # to use 4 sprites total for the boss
    # (we're losing some shadow in upper left corner,
    # color quantization did more or less the same, so doing it manually makes
    # sure that other palette values don't change)
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            p = img.getpixel((x,y))
            if p == (174,174,143):
                p = (210,210,174)
                img.putpixel((x,y),p)
    img.save(os.path.join(dump_dir,"..","andor_genesis_recolor.png"))
    palette = bitplanelib.palette_extract(img)
    # magenta (transparent) is first
    transparent = palette.pop()
    if len(palette) != 6:
        raise Exception("6 colors are expected exactly for andor genesis")
    # find the red color
    red_color_index = next(i for i,p in enumerate(palette) if p[0]!=0 and p[1]==p[2]==0)
    # and move it in the first position
    r = palette.pop(red_color_index)
    palette.insert(1,r)

    # separate 2 images according to palette
    first_half = palette[:3]
    second_half = palette[3:]
    img1 = Image.new("RGB",img.size,color=transparent)
    img2 = Image.new("RGB",img.size,color=transparent)
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            p = img.getpixel((x,y))
            dest = None
            if p in first_half:
                dest = img1
            elif p in second_half:
                dest = img2
            if dest:
                dest.putpixel((x,y),p)
    # now create 4 sprites out of those 2 images
    # 2 (64x96) sprites, 2 (32x96 sprites)
    first_half.insert(0,transparent)
    second_half.insert(0,transparent)
    srcout = os.path.join(this_dir,"../../src/amiga/andor_genesis.68k")

    sprites = []
    for pal,img in [(first_half,img1),(second_half,img2)]:
        img11 = img.crop((0,0,64,96))
        img12 = img.crop((64,0,96,96))
        sprite_left = bitplanelib.palette_image2sprite(img11,None,pal,sprite_fmode=3)
        sprite_right = bitplanelib.palette_image2sprite(img12,None,pal,sprite_fmode=3)
        sprites.append([sprite_left,sprite_right])

    with open(srcout,"w") as f:
        f.write("is_andor_genesis_table:")
        bitplanelib.dump_asm_bytes(andor_table,f,mit_format=True)
        f.write("* andor sprites\n")
        for d in ("left","right"):
            f.write("""andor_genesis_{}:
    .word    BT_SPRITE
* 2 sprite(s)
    .word    0   | sprite number
* palette
""".format(d))
            bitplanelib.palette_dump(first_half,f,bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
            f.write("""
* bitmap
    .long    andor_genesis_00_{}
    .word    1   | sprite number
* palette
""".format(d))
            bitplanelib.palette_dump(second_half,f,bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
            f.write("""
* bitmap
    .long    andor_genesis_01_{}
    .word    -1   | end of sprite(s)
""".format(d))
        f.write("\t.datachip\n")
        for j,d in enumerate(("left","right")):
            for i in range(2):
                sp = sprites[i][j]
                f.write("andor_genesis_{:02d}_{}:\n".format(i,d))
                f.write("\t.word\t0,0,0,0,0,0,0,0")
                bitplanelib.dump_asm_bytes(sp,f,mit_format=True)
                f.write("\t.long\t0,0,0,0\n")
if __name__ == "__main__":
    doit()
