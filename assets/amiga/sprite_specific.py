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
src_dir = os.path.join(this_dir,"../../src/amiga")

hw_dict = dict(HW_NONE = 0,
HW_OTHER = 4,
HW_MASKED_TILE = 12,  # tile not displayed (bridge, andor, jet): do not change value
# special big size sprites from "HW_BRIDGE"
HW_SPECIAL_SPRITES = 14,  # not real just to delimit special sprites
HW_BRIDGE = 16,
HW_FLYING_JET_1 = 18,
HW_FLYING_JET_2 = 19,
HW_ANDOR_FIRST = 20,   # do not change value, present in bin dump to create big andor sprite
HW_ANDOR_SECOND = 24)  # ""

globals().update(hw_dict)

# dictionary of sprites which aren't bobs but sprites
# since game sprites can have more than 3 colors, we have to combine 2 sprites
real_sprites = {80:{"sprites":[0,1]},   # solvalou
240:{"sprites":[2,3],"mirror":True},   # helicopter
241:{"sprites":[2,3],"mirror":True},   # helicopter
243:{"sprites":[2,3],"mirror":True},   # taking off jet
230:{"sprites":[2,3],"mirror":True},   # flying jet 1
234:{"sprites":[2,3],"mirror":True},   # flying jet 2
248:{"sprites":[2,3],"mirror":True},   # tank
254:{"sprites":[4,5]},   # bridge start
}
# bragza: "soul" of the andor genesis
# only 1 sprite needed but uses a lot of unique colors
# unseen in other enemies, so it's good that it has its own palette in sprites
for i in range(184,188):
    real_sprites[i] = {"sprites":[2,3]}
# bridge: not useful, addressed through double height+width 254 sprite
##for i in range(252,253,255):
##    real_sprites[i] = {"sprites":[2,3]}

# shining object for Xevious title
for i in range(304,320):
    real_sprites[i] = {"sprites":[1]}

# table gathering ALL sprites, the ones handled by the engine, and
# special ones (andor genesis)
sprite_table = [HW_NONE]*320
for start,stop in ((88,91),(128,159)):  # 92-96 are glowing hulls, we need to display them
    sprite_table[start:stop+1] = [HW_MASKED_TILE]*(stop-start+1)
for r in real_sprites:
    sprite_table[r] = HW_OTHER

# sets bridge tiles. top left tile is 254 but since sprite has double width/double height
# tile 252 is the key and controls HW sprite other tiles shouldn't be displayed or dumped
# as BOBs
sprite_table[252:256] = [HW_BRIDGE,HW_MASKED_TILE,HW_MASKED_TILE,HW_MASKED_TILE]
sprite_table[228:231] = [HW_FLYING_JET_1,HW_MASKED_TILE,HW_MASKED_TILE,HW_MASKED_TILE]
sprite_table[232:236] = [HW_FLYING_JET_2,HW_MASKED_TILE,HW_MASKED_TILE,HW_MASKED_TILE]


def split_sprite(palette,img):

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
    first_half.insert(0,transparent)
    second_half.insert(0,transparent)
    return (first_half,img1),(second_half,img2)

def doit():
    global transparent

    dump_dir = os.path.join(this_dir,"dumps","sprite","raw")
    prefix = "andor_genesis"
    # reading memory dump from running game (old structure, 8 bytes per sprite
    # new structure has 12 bytes per sprite, includes height and sprite HW yes/no)
    with open(os.path.join(this_dir,"andor_genesis_sprite_dump.bin"),"rb") as f:
        contents = f.read()


    def is_andor_genesis(code):
        return bool(sprite_table[code] in [HW_MASKED_TILE,HW_ANDOR_FIRST,HW_ANDOR_SECOND])

    ag_blocks = []

    # reading in-game dump of sprite array when andor is present
    # so we can assemble the tiles easily
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
            sprite_table[sprite_code] = HW_ANDOR_FIRST   # sprite code = 132
            print(sprite_code)
        if x==64 and y==0:
            sprite_table[sprite_code] = HW_ANDOR_SECOND # sprite code = 88


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

    (first_half,fimg),(second_half,simg) = split_sprite(palette,img)

    srcout = os.path.join(src_dir,"hw_sprite_specific.68k")
    hdrout = os.path.join(src_dir,"hw_sprite_types.68k")

    # now create 4 sprites out of those 2 images
    # 2 (64x96) sprites, 2 (32x96 sprites)

    sprites = []
    for pal,img in [(first_half,fimg),(second_half,simg)]:
        img11 = img.crop((0,0,64,96))
        img12 = img.crop((64,0,96,96))
        sprite_left = bitplanelib.palette_image2sprite(img11,None,pal,sprite_fmode=3)
        sprite_right = bitplanelib.palette_image2sprite(img12,None,pal,sprite_fmode=3)
        sprites.append([sprite_left,sprite_right])

    with open(hdrout,"w") as f:
        for k,v in hw_dict.items():
            f.write("{} = {}\n".format(k,v))

    dict_32x32 = {}

    for name,tiles in [("bridge",((254,0,0),(252,1,0),(255,0,1),(253,1,1))),
    ("flying_jet_1",((230,0,0),(228,1,0),(231,0,1),(229,1,1))),
    ("flying_jet_2",((234,0,0),(232,1,0),(235,0,1),(233,1,1)))
    ]:
        # brige: much simpler: just assemble 4 parts for 32x32 sprite
        big_32x32 = Image.new("RGB",(32,32),color=transparent)
        for n,xo,yo in tiles:
            source = os.path.join(dump_dir,"{}_{}_2.png".format(name,n))
            src = Image.open(source)
            x_offset = 16*xo
            y_offset = 16*yo
            big_32x32.paste(src,(x_offset,y_offset))
        big_32x32.save(os.path.join(dump_dir,"..","{}.png".format(name)))

        (first_half,fimg),(second_half,simg) = split_sprite(bitplanelib.palette_extract(big_32x32),big_32x32)

        # now create 2 overlayed sprites
        # (32x32)

        xx_sprites = []
        for pal,img in [(first_half,fimg),(second_half,simg)]:
            sprite = bitplanelib.palette_image2sprite(img,None,pal,sprite_fmode=3)
            xx_sprites.append(sprite)

        dict_32x32[name] = {"sprites":xx_sprites,"first_half":first_half,
        "second_half":second_half}

    with open(srcout,"w") as f:
        f.write("* table:\n")
        f.write("* refer to HW_xxx enums for meaning\n")
        for d in ("left","right"):
            f.write("\t.global\tandor_genesis_{}\n".format(d))
        for extra_32x32 in dict_32x32:
            f.write("\t.global\t{}\n".format(extra_32x32))

        f.write("\n\t.global\t{0}\n\n{0}:\n".format("red_color_table"))
        for i,r in enumerate([0,0,255,174,143,88,0]):
            f.write("\t.byte\t0x{:x},0x{:x}  | config #{}\n".format((r>>4),r&0xF,i))
        f.write("\n\t.global\t{0}\n\n{0}:".format("is_hw_sprite_table"))

        bitplanelib.dump_asm_bytes(sprite_table,f,mit_format=True)
        f.write("* andor sprites\n")
        for i,d in enumerate(("left","right")):
            f.write("""andor_genesis_{0}:
    .word    BT_SPRITE
* 2 sprite(s)
    .word    {1}   | sprite number
* palette
""".format(d,i*2+4))
            bitplanelib.palette_dump(first_half,f,bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
            f.write("""
* bitmap
    .long    andor_genesis_00_{0}
    .word    {1}   | sprite number
* palette
""".format(d,i*2+5))
            bitplanelib.palette_dump(second_half,f,bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
            f.write("""
* bitmap
    .long    andor_genesis_01_{0}
    .word    -1   | end of sprite(s)
""".format(d))

        for k,v in dict_32x32.items():
            f.write("* {} sprite\n".format(k))
            f.write("""{}:
    .word    BT_SPRITE
* 2 sprite(s)
    .word    {}   | sprite number
* palette
""".format(k,4))
            bitplanelib.palette_dump(v["first_half"],f,bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
            f.write("""
* bitmap
    .long    {}_00
    .word    {}   | sprite number
* palette
""".format(k,5))
            bitplanelib.palette_dump(v["second_half"],f,bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
            f.write("""
* bitmap
    .long    {}_01
    .word    -1   | end of sprite(s)
""".format(k))


        f.write("\t.datachip\n")
        f.write("\t.align\t8\n")
        for j,d in enumerate(("left","right")):
            for i in range(2):
                sp = sprites[i][j]
                f.write("andor_genesis_{:02d}_{}:\n".format(i,d))
                f.write("\t.word\t0,0,0,0,0,0,0,0")
                bitplanelib.dump_asm_bytes(sp,f,mit_format=True)
                f.write("* add 96 blank rows so the clipping works\n")
                f.write("\t.rept\t96*2\n")
                f.write("\t.byte    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00\n")
                f.write("\t.endr\n")
                f.write("\t.long\t0,0,0,0\n")

        for k,v in dict_32x32.items():
            sprites = v["sprites"]
            for i in range(2):
                sp = sprites[i]
                f.write("{}_{:02d}:\n".format(k,i))
                f.write("\t.word\t0,0,0,0,0,0,0,0")
                bitplanelib.dump_asm_bytes(sp,f,mit_format=True)
                f.write("* add 32 blank rows so the clipping works\n")
                f.write("\t.rept\t32*2\n")
                f.write("\t.byte    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00\n")
                f.write("\t.endr\n")
                f.write("\t.long\t0,0,0,0\n")
        f.write("\t.align\t8\n")
if __name__ == "__main__":
    doit()
