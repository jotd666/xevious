import os,re,bitplanelib,ast,json
from PIL import Image,ImageOps

import collections


block_dict = {}

# where tile & sprite CLUT used configuration logs are fetch from
# we cannot possibly generate all tile & sprite CLUT configurations
# as that would generate gigabytes of graphics when only one or
# a few CLUTs are used for each background tile/sprite
#
# tile logs are dumped in debug mode when running the game, experiencing
# dashed tiles / flashing colors to indicate that such or such tile CLUT
# configuration is missing

winuae_dir = r"C:\Users\Public\Documents\Amiga Files\WinUAE"

dump_dir = "dumps/bg_tile/orig"
if not os.path.isdir(dump_dir):
    raise Exception("{} doesn't exist".format(dump_dir))
def dump_png(bg_data):
    with open(bg_data,"rb") as f:
        color_data = f.read(0x800)
        tile_data = f.read(0x800)

    used_tiles = set()
    row = 0
    col = 0
    scale = 4

    outimg = Image.new("RGB",(32*8*scale,64*8*scale))

    for idx,tile_index in zip(color_data,tile_data):
        # rework
        clut_index = 0
        if idx & 1:
            tile_index += 0x100
        if tile_index & 0x80:
            clut_index = 1<<4
        clut_index |= ((idx & 0x3F)>>2)
        clut_index |= (idx&0x3) << 5
        used_tiles.add(tile_index)
        img = "img_{:02d}_{}.png".format(tile_index,clut_index)
        img = os.path.join(dump_dir,img)

        if os.path.exists(img):

            pixels = Image.open(img)
            if idx & 0x40:
                pixels = ImageOps.flip(pixels)
            if idx & 0x80:
                pixels = ImageOps.mirror(pixels)
            outimg.paste(pixels,((32-row)*8*scale,col*8*scale))
        col += 1
        if col == 64:
            col = 0
            row += 1

    outimg.save(os.path.join("dumps","{}.png".format(os.path.basename(bg_data))))
    return used_tiles

ut = dump_png("bg_tile_bug")

ut = dump_png("bg_data_scroll")
ut = dump_png("bg_data_title")
print(ut)

