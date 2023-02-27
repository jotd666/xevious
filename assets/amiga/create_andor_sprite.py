# this script handles the special case of andor genesis boss
#
# the game code can handle sprites already but here we have to rebuild
# the massive sprite image from a game dump, so tiles are properly assembled
#
# besides, there are several CLUTs for the same graphics, and that is not currently
# supported by the "convert_graphics.py" main code which would have copied the sprite data
#
# instead, here we generate the boss structure in a format that respects the game engine
# hardware sprite structure, but we hardcode many things. For example we re-use the sprite bitmap
# across CLUT configs (which could be done generically but would mean feed the generic asset
# conversion with all CLUT configs and assembled andor genesis. Hardcoding it allows to make it
# less complex.
#
# Also, the generated code provides a truth table that tells the engine which tiles are andor genesis
# tiles. One tile (the upper left one) in particular triggers the display of the first sprite part
# and the second tile (upper left + 64X) triggers the display of the second sprite part

import struct,os
from PIL import Image
import bitplanelib

this_dir = os.path.dirname(__file__)


AS_NONE = 0
AS_TILE = 1
AS_FIRST = 2
AS_SECOND = 3
AS_OTHER = 4


# dictionary of sprites which aren't bobs but sprites
# since game sprites can have more than 3 colors, we have to combine 2 sprites
real_sprites = {80:[0,1]   # solvalou
}
# bragza: "soul" of the andor genesis
# only 1 sprite needed but uses a lot of unique colors
# unseen in other enemies, so it's good that it has its own palette in sprites
for i in range(184,188):
    real_sprites[i] = [2,3]

# shining object for Xevious title
for i in range(304,320):
    real_sprites[i] = [1]


def doit():
    andor_table = [AS_NONE]*320
    for start,stop in ((88,96),(128,159)):
        andor_table[start:stop+1] = [AS_TILE]*(stop-start+1)

    dump_dir = os.path.join(this_dir,"dumps","sprite","raw")
    prefix = "andor_genesis"
    # reading memory dump from running game (old structure, 8 bytes per sprite)
    with open("andor_genesis_sprite_dump.bin","rb") as f:
        contents = f.read()


    def is_andor_genesis(code):
        return bool(andor_table[code])

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
        if x==0 and y==0:
            andor_table[sprite_code] = AS_FIRST
        if x==64 and y==0:
            andor_table[sprite_code] = AS_SECOND

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
        f.write("* table:\n")
        f.write("* 0: no andor tile\n")
        f.write("* 1: andor tile, do not display\n")
        f.write("* 2: origin andor tile (first sprite)\n")
        f.write("* 3: second origin andor tile (second sprite)\n\n")
        f.write("\t.global\t{0}\n\n{0}:".format("is_hw_sprite_table"))
        bitplanelib.dump_asm_bytes(andor_table,f,mit_format=True)
        f.write("* andor sprites\n")
        for d in ("left","right"):
            f.write("""andor_genesis_{}:
    .word    BT_SPRITE
* 2 sprite(s)
    .word    6   | sprite number
* palette
""".format(d))
            bitplanelib.palette_dump(first_half,f,bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
            f.write("""
* bitmap
    .long    andor_genesis_00_{0}
    *.long    andor_genesis_00_{0}_databack
    .word    7   | sprite number
* palette
""".format(d))
            bitplanelib.palette_dump(second_half,f,bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
            f.write("""
* bitmap
    .long    andor_genesis_01_{0}
    *.long    andor_genesis_01_{0}_databack
    .word    -1   | end of sprite(s)
""".format(d))
        f.write("\t.datachip\n")
        f.write("\t.align\t8\n")
        for j,d in enumerate(("left","right")):
            for i in range(2):
                sp = sprites[i][j]
                f.write("andor_genesis_{:02d}_{}:\n".format(i,d))
                f.write("\t.word\t0,0,0,0,0,0,0,0")
                bitplanelib.dump_asm_bytes(sp,f,mit_format=True)
                f.write("\t.long\t0,0,0,0\n")
        f.write("\t.align\t8\n")
if __name__ == "__main__":
    doit()
