import os,re,bitplanelib,ast
from PIL import Image,ImageOps

import collections


block_dict = {}

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

palette = bitplanelib.palette_round(palette,0xF0)
bitplanelib.palette_dump(palette,os.path.join(src_dir,"palette.68k"),bitplanelib.PALETTE_FORMAT_ASMGNU)

raw_blocks = collections.defaultdict(list)

for table,data in block_dict.items():
    if data["size"] in [64,256]:
        is_sprite = table == "sprite"
        side = int(data["size"]**0.5)
        pics = data["data"]
        dump_width = side * 64
        img = Image.new("RGB",(dump_width,side*(len(pics)//(dump_width//side))))
        cur_x = 0
        cur_y = 0
        for pic in pics:
            input_image = Image.new("RGB",(side,side))
            for i,p in enumerate(pic):
                col = palette[p]
                y,x = divmod(i,side)
                img.putpixel((cur_x+x,cur_y+y),col)  # for dump
                input_image.putpixel((x,y),col)

            cur_x += side
            if cur_x == dump_width:
                cur_x = 0
                cur_y += side
            for the_tile in [input_image,ImageOps.mirror(input_image)]:
                raw = bitplanelib.palette_image2raw(the_tile,output_filename=None,
                palette=palette[0:16],forced_nb_planes=4,
                palette_precision_mask=0xF0,
                generate_mask=is_sprite,
                blit_pad=is_sprite)
                raw_blocks[table].append(raw)

        img.save(table+".png")
        maxcol = max(max(pic) for pic in pics)

outfile = os.path.join(src_dir,"graphics.68k")
#print("writing {}".format(os.path.abspath(outfile)))
with open(outfile,"w") as f:
    for t in ["fg_tile","bg_tile","sprite"]:
        if t == "sprite":
            f.write("\t.datachip\n")
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