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

dump_dir = "dumps/bg"
bg_data = os.path.join(winuae_dir,"bg_data")

with open(bg_data,"rb") as f:
    color_data = f.read(0x800)
    tile_data = f.read(0x800)

row = 0
col = 0

outimg = Image.new("RGB",(32*8,64*8))

for idx,tile_index in zip(color_data,tile_data):
    # rework
    clut_index = 0
    if tile_index & 0x80:
        clut_index = 1<<4
    clut_index |= (idx>>2) & 0xF
    clut_index |= (idx&0x3) << 5
    img = "img_{:02d}_{}.png".format(tile_index,clut_index)
    img = os.path.join(dump_dir,img)

    if os.path.exists(img):

        pixels = Image.open(img)
        outimg.paste(pixels,(row*8,col*8))
    col += 1
    if col == 32:
        col = 0
        row += 1

outimg.save("dumps/bgmap.png")
