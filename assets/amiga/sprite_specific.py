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
HW_BRIDGE_TILE = 8,
HW_ANDOR_TILE = 12,
# special big size sprites from "HW_BRIDGE"
HW_BRIDGE = 16,
HW_ANDOR_FIRST = 20,
HW_ANDOR_SECOND = 24)

globals().update(hw_dict)

# dictionary of sprites which aren't bobs but sprites
# since game sprites can have more than 3 colors, we have to combine 2 sprites
real_sprites = {80:{"sprites":[0,1]},   # solvalou
240:{"sprites":[2,3],"mirror":True},   # helicopter
241:{"sprites":[2,3],"mirror":True},   # helicopter
243:{"sprites":[2,3],"mirror":True},   # flying jet
248:{"sprites":[2,3],"mirror":True},   # tank
249:{"sprites":[2,3],"mirror":True},   # tank
252:{"sprites":[4,5]},   # bridge start
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
    sprite_table[start:stop+1] = [HW_ANDOR_TILE]*(stop-start+1)
for r in real_sprites:
    sprite_table[r] = HW_OTHER


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
        return bool(sprite_table[code] in [HW_ANDOR_TILE,HW_ANDOR_FIRST,HW_ANDOR_SECOND])

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


    # brige: much simpler: just assemble 4 parts for 32x32 sprite
    bridge = Image.new("RGB",(64,32),color=transparent)
    for n,xo,yo in ((254,0,0),(252,1,0),(255,0,1),(253,1,1)):
        source = os.path.join(dump_dir,"bridge_{}_2.png".format(n))
        src = Image.open(source)
        x_offset = 16*xo
        y_offset = 16*yo
        bridge.paste(src,(x_offset,y_offset))
    bridge.save(os.path.join(dump_dir,"..","bridge.png"))

    (first_half_bridge,fimg),(second_half_bridge,simg) = split_sprite(bitplanelib.palette_extract(bridge),bridge)

    # now create 2 overlayed sprites
    # (32x32)

    bridge_sprites = []
    for pal,img in [(first_half_bridge,fimg),(second_half_bridge,simg)]:
        sprite = bitplanelib.palette_image2sprite(img,None,pal,sprite_fmode=3)
        bridge_sprites.append(sprite)

    with open(srcout,"w") as f:
        f.write("* table:\n")
        f.write("* 0: not a HW sprite\n")
        f.write("* 4: standard 16x16 sprite (non andor, non bridge)\n")
        f.write("* 8: bridge sprite origin\n")
        f.write("* 12: bridge tile (others, do not display)\n")
        f.write("* 16: andor tile, do not display\n")
        f.write("* 20: origin andor tile (first sprite)\n")
        f.write("* 24: second origin andor tile (second sprite)\n")
        for d in ("left","right"):
            f.write("\t.global\tandor_genesis_{}\n".format(d))
        f.write("\t.global\tbridge\n")
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
        f.write("* bridge sprite\n")
        f.write("""bridge:
    .word    BT_SPRITE
* 2 sprite(s)
    .word    {0}   | sprite number
* palette
""".format(4))
        bitplanelib.palette_dump(first_half_bridge,f,bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
        f.write("""
* bitmap
    .long    bridge_00
    .word    {0}   | sprite number
* palette
""".format(5))
        bitplanelib.palette_dump(second_half_bridge,f,bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
        f.write("""
* bitmap
    .long    bridge_01
    .word    -1   | end of sprite(s)
""")
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

        for i in range(2):
            sp = bridge_sprites[i]
            f.write("bridge_{:02d}:\n".format(i))
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
