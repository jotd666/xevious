import os,re,bitplanelib,ast
from PIL import Image,ImageOps

import collections


block_dict = {}

def get_used_bg_cluts():
    infile = r"C:\Users\Public\Documents\Amiga Files\WinUAE\bg_tile_log"
    rval = collections.defaultdict(list)
    with open(infile,"rb") as f:
        contents = f.read()

    row_index = 0
    for tile_index in range(512):
        for idx in range(64):
            if contents[row_index+idx] == 0xdd:
                clut_index = 0
                if tile_index & 0x80:
                    clut_index = 1<<4
                clut_index |= (idx>>2) & 0xF
                clut_index |= (idx&0x3) << 5
                rval[tile_index].append(clut_index)
        row_index += 64

    return rval

def quantize_palette(tile_clut,global_palette):
    rgb_configs = set(global_palette[i & 0x7F] for clut in tile_clut for i in clut)  # 75 unique colors now
    # remove 0, we don't want it quantized
    black = (0,0,0)
    white = (255,255,255)
    rgb_configs.remove(black)
    rgb_configs.remove(white)
    rgb_configs = sorted(rgb_configs)
    dump_graphics = False
    # now compose an image with the colors
    clut_img = Image.new("RGB",(len(rgb_configs),1))
    for i,rgb in enumerate(rgb_configs):
        rgb_value = (rgb[0]<<16)+(rgb[1]<<8)+rgb[2]
        clut_img.putpixel((i,0),rgb_value)

    reduced_colors_clut_img = clut_img.quantize(colors=15,dither=0).convert('RGB')

    # get the reduced palette
    reduced_palette = [reduced_colors_clut_img.getpixel((i,0)) for i,_ in enumerate(rgb_configs)]
    # apply rounding now
    reduced_palette = bitplanelib.palette_round(reduced_palette,0xF0)
    #print(len(set(reduced_palette))) # should still be 15
    # now create a dictionary
    rval = dict(zip(rgb_configs,reduced_palette))
    # add black back
    rval[black] = black
    rval[white] = white

    if False:  # debug it
        s = clut_img.size
        ns = (s[0]*30,s[1]*30)
        clut_img = clut_img.resize(ns,resample=0)
        clut_img.save("colors_not_quantized.png")
        reduced_colors_clut_img = reduced_colors_clut_img.resize(ns,resample=0)
        reduced_colors_clut_img.save("colors_quantized.png")

    # return it
    return rval

src_dir = "../src/amiga"

# hackish convert of c gfx table to dict of lists
with open("xevious_gfx.c") as f:
    block = []
    block_name = ""
    start_block = False

    for line in f:
        if "uint8" in line:
            # start group
            start_block = True
            if block:
                txt = "".join(block).strip().strip(";")
                block_dict[block_name] = {"size":size,"data":ast.literal_eval(txt)}
                block = []
            block_name = line.split()[1].split("[")[0]
            size = int(line.split("[")[2].split("]")[0])
        elif start_block:
            line = re.sub("//.*","",line)
            line = line.replace("{","[").replace("}","]")
            block.append(line)

    if block:
        txt = "".join(block).strip().strip(";")
        block_dict[block_name] = {"size":size,"data":ast.literal_eval(txt)}
        # for fg, remove the upper 256 tiles as they're used only in cocktail mode
        del block_dict["fg_tile"]["data"][256:]


palette = [tuple(x) for x in block_dict["palette"]["data"]]
palette = bitplanelib.palette_round(palette)



bg_tile_clut = block_dict["bg_tile_clut"]["data"]

# compute the RGB configuration used for each used tile. Generate a lookup table with
bg_tile_clut_dict = get_used_bg_cluts()
for tile,cluts in bg_tile_clut_dict.items():
    used_cluts = [[palette[i] for i in bg_tile_clut[c]] for c in cluts]
    used_clut_indexes = [bg_tile_clut[c] for c in cluts]
    print(tile,used_cluts,used_clut_indexes)

dump_graphics = True

def generate_tile(pic,side,current_palette,nb_planes,is_sprite):
    input_image = Image.new("RGB",(side,side))
    for i,p in enumerate(pic):
        col = current_palette[p]
        y,x = divmod(i,side)
        input_image.putpixel((x,y),col)

    rval = []
    for the_tile in [input_image,ImageOps.mirror(input_image)]:
        raw = bitplanelib.palette_image2raw(the_tile,output_filename=None,
        palette=current_palette,
        forced_nb_planes=nb_planes,
        palette_precision_mask=0xF0,
        generate_mask=is_sprite,
        blit_pad=is_sprite)
        rval.append(raw)

    return rval

if dump_graphics:
# temp add all white for foreground
    bitplanelib.palette_dump(palette+[(240,240,240)]*128,os.path.join(src_dir,"palette.68k"),bitplanelib.PALETTE_FORMAT_ASMGNU)

    raw_blocks = collections.defaultdict(list)

    for table,data in block_dict.items():
        if data["size"] in [64,256]:
            is_sprite = table == "sprite"
            is_fg = "fg" in table
            nb_planes = 1 if is_fg else 7
            nb_colors = 1<<nb_planes
            current_palette = [(0,0,0),(96, 96, 96)] if is_fg else palette

            side = int(data["size"]**0.5)
            pics = data["data"]
            for pic in pics:
                couple = generate_tile(pic,side,current_palette,nb_planes,is_sprite)
                raw_blocks[table].extend(couple)

##            dump_width = side * 64
##            dump_height = side * (len(pics)//64)
##            img = Image.new("RGB",(dump_width,dump_height))
##            cur_x = 0
##            cur_y = 0
##                img.putpixel((cur_x+x,cur_y+y),col)  # for dump
##                cur_x += side
##                if cur_x == dump_width:
##                    cur_x = 0
##                    cur_y += side
#            img.save(table+".png")

    outfile = os.path.join(src_dir,"graphics.68k")
    #print("writing {}".format(os.path.abspath(outfile)))
    with open(outfile,"w") as f:
        f.write("NULLPTR = 0\n")
        t = "fg_tile"
        # foreground tiles: just write the 1-bitplane tiles and their mirrored counterpart
        f.write("\t.global\t_{0}\n_{0}:".format(t))
        c = 0
        for block in raw_blocks[t]:
            for d in block:
                if c==0:
                    f.write("\n\t.byte\t")
                else:
                    f.write(",")
                f.write("0x{:02x}".format(d))
                c += 1
                if c == 8:
                    c = 0
        f.write("\n")
        # background tiles: this is trickier as we have to write a big 2D table tileindex + all possible 64 color configurations (a lot are null pointers)
        t = "bg_tile"
        f.write("\t.global\t_{0}\n_{0}:".format(t))

        # TEMP TEMP TEMP
        c = 0
        for block in raw_blocks[t]:
            for d in block:
                if c==0:
                    f.write("\n\t.byte\t")
                else:
                    f.write(",")
                f.write("0x{:02x}".format(d))
                c += 1
                if c == 8:
                    c = 0
        f.write("\n")
        # TEMP TEMP TEMP

        t = "sprite"
        f.write("\t.datachip\n")
        f.write("\t.global\t_{0}\n_{0}:\n".format(t))
        sprite_blocks = raw_blocks[t]
        for i in range(len(sprite_blocks)):
            f.write("\t.long\tsprite_{:03}\n".format(i))
        c = 0

        for i,block in enumerate(sprite_blocks):
            f.write("\nsprite_{:03}:".format(i))
            for d in block:
                if c==0:
                    f.write("\n\t.byte\t")
                else:
                    f.write(",")
                f.write("0x{:02x}".format(d))
                c += 1
                if c == 8:
                    c = 0
        f.write("\n")