import os,re,bitplanelib,ast,json
from PIL import Image,ImageOps

import collections


block_dict = {}

BG_NB_PLANES = 7

# where tile & sprite CLUT used configuration logs are fetch from
# we cannot possibly generate all tile & sprite CLUT configurations
# as that would generate gigabytes of graphics when only one or
# a few CLUTs are used for each background tile/sprite
#
# tile logs are dumped in debug mode when running the game, experiencing
# dashed tiles / flashing colors to indicate that such or such tile CLUT
# configuration is missing

winuae_dir = r"C:\Users\Public\Documents\Amiga Files\WinUAE"

def load_names(json_file):
    rval = {}
    try:
        with open(json_file) as f:
            d = json.load(f)

        for k,v in d.items():
            if k.isdigit():
                rng = [int(k)]
            else:
                start,end = map(int,k.split("-"))
                rng = range(start,end+1)
            for k in rng:
                rval[k] = v

    except OSError:
        pass
    return rval

def load_binary_tile_file(infile):
    contents = b""
    if os.path.exists(infile):
        with open(infile,"rb") as f:
            contents = f.read()
    else:
        # normal when rebuilding with a complete .json file
        print("{} file not dumped")

    return contents

def load_json_tile_file(filename):
    rval = collections.defaultdict(set)
    try:
        with open(filename) as f:
            d = json.load(f)

        rval.update({int(k):set(v) for k,v in d.items()})
    except OSError:
        pass
    return rval

def save_json_tile_file(filename,rval,old_rval):
    if rval != old_rval:
        print("Updating {}".format(filename))
        with open(filename,"w") as f:
            json.dump({k:sorted(v) for k,v in rval.items()},f,indent=2)
    else:
        print("{} already contains all tile/clut info".format(filename))

def get_used_bg_cluts():
    infile = os.path.join(winuae_dir,"bg_tile_log")
    bg_json_base = "bg_tile_clut.json"
    # load previously recorded configurations
    rval = load_json_tile_file(bg_json_base)
    copy_rval = {k:v.copy() for k,v in rval.items()}

    # update with what was ripped in WinUAE directory
    contents = load_binary_tile_file(infile)

    if contents:
        row_index = 0
        for tile_index in range(512):
            for idx in range(64):   # table still needs tile index to get bit 4 of clut index
                v = contents[row_index+idx]
                if v == 0xdd:
                    clut_index = 0
                    if tile_index & 0x80:
                        clut_index = 1<<4
                    clut_index |= (idx>>2) & 0xF
                    clut_index |= (idx&0x3) << 5
                    rval[tile_index].add(clut_index)
                    print("found: tile_index: {}, clut_index: {}".format(tile_index,clut_index))
            row_index += 64

        save_json_tile_file(bg_json_base,rval,copy_rval)

    return rval

def get_used_sprite_cluts():
    infile = os.path.join(winuae_dir,"sprite_tile_log")
    sprite_json_base = "sprite_tile_clut.json"

    rval = load_json_tile_file(sprite_json_base)
    copy_rval = rval.copy()

    contents = load_binary_tile_file(infile)
    if contents:
        row_index = 0
        for tile_index in range(320):
            for idx in range(128):
                if contents[row_index+idx] == 0xee:
                    clut_index = idx
                    rval[tile_index].add(clut_index)
            row_index += 128

        save_json_tile_file(sprite_json_base,rval,copy_rval)

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

sprite_names = load_names("sprite_names.json")

bg_tile_clut = block_dict["bg_tile_clut"]["data"]
sprite_tile_clut = block_dict["sprite_clut"]["data"]


dump_graphics = True
dump_pngs = True

def mkdir(d):
    if not os.path.exists(d):
        os.mkdir(d)

if dump_pngs:
    dump_root = "dumps"
    mkdir(dump_root)
    for d in ["bg","fg","sprite"]:
        mkdir(os.path.join(dump_root,d))

def write_tiles(t,matrix,f,is_sprite,compress_blank_planes):
    # background tiles/sprites: this is trickier as we have to write a big 2D table tileindex + all possible 64 color configurations (a lot are null pointers)

    f.write("\t.global\t{0}_picbase\n\t.global\t_{0}_tile\n_{0}_tile:".format(t))

    c = 0
    pic_list = []

    for i,row in enumerate(matrix):
        f.write("\n* row {}".format(i))
        for item in row:
            if c==0:
                f.write("\n\t.word\t")
            else:
                f.write(",")
            if item is None:
                f.write(nullptr)
            elif item == 0:
                f.write(blankptr)
            else:
                f.write("{1}_pic_{0:03d}-{1}_picbase".format(len(pic_list),t))
                pic_list.append(item)
            c += 1
            if c == 8:
                c = 0
        f.write("\n")

    # add 2 bytes so relative addresses aren't 0
    f.write("{}_picbase:\n\tdc.w\t0\n".format(t))
    # now write all defined pointers to pics (no relative shit
    # as data can be pretty big and overshoot 0x7FFF limit, which
    # explains the double indirection in the tables
    # 1) one table with word offsets to save memory, pointing on pointers
    # 2) one table of pointers that point on actual data
    #
    for i,_ in enumerate(pic_list):
        picname = "{}_pic_{:03d}".format(t,i)
        f.write("{0}:\n\tdc.l\t{0}_bytes\n".format(picname))
    if is_sprite:
        f.write("\t.datachip\n")
    for i,item in enumerate(pic_list):
        f.write("{}_pic_{:03d}_bytes:".format(t,i))
        if compress_blank_planes:
            # we have to rework data
            if is_sprite:
                # not supported
                pass
            else:
                # bg tile
                item_pack = []

                for p in range(BG_NB_PLANES):
                    block = item[p*8:p*8+8]
                    if any(block):
                        # non-zero somewhere
                        item_pack.append(0xca)
                        item_pack.extend(block)
                    else:
                        item_pack.append(0)
                item = item_pack

        dump_asm_bytes(item,f)

def generate_tile(pic,side,current_palette,global_palette,nb_planes,is_sprite):
    input_image = Image.new("RGB",(side,side))
    for i,p in enumerate(pic):
        col = current_palette[p]
        y,x = divmod(i,side)
        input_image.putpixel((x,y),col)

    rval = []
    for the_tile in [input_image,ImageOps.mirror(input_image)]:
        raw = bitplanelib.palette_image2raw(the_tile,output_filename=None,
        palette=global_palette,
        forced_nb_planes=nb_planes,
        generate_mask=is_sprite,
        blit_pad=is_sprite)
        rval.append(raw)

    return {"png":input_image,"standard":rval[0],"mirror":rval[1]}

def dump_asm_bytes(block,f):
    c = 0
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

if dump_graphics:
# temp add all white for foreground
    bitplanelib.palette_dump(palette+[(255,)*3]*128,os.path.join(src_dir,"palette.68k"),
                            bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)

    raw_blocks = {}

    # foreground data, simplest of all 3
    table = "fg_tile"
    fg_data = block_dict[table]
    current_palette = [(0,0,0),(96, 96, 96)]

    side = 8
    scale = 4
    pics = fg_data["data"]
    raw_blocks[table] = []
    for i,pic in enumerate(pics):
        d = generate_tile(pic,side,current_palette,current_palette,nb_planes=1,is_sprite=False)
        raw_blocks[table].append(d["standard"])
        raw_blocks[table].append(d["mirror"])
        if dump_pngs:
            ImageOps.scale(d["png"],scale,0).save("dumps/fg/img_{:02}.png".format(i))

    # background data: requires to generate as many copies of each tile that there are used CLUTs on that tile
    # the only way to know which CLUTs are used is to run the game and log them... We can't generate all pics, that
    # would take too much memory (512*64 pics of 16 color 8x8 tiles!!)

    table = "bg_tile"
    bg_data = block_dict[table]

    bg_matrix = raw_blocks[table] = [[None]*256 for _ in range(512)]
    # compute the RGB configuration used for each used tile. Generate a lookup table with
    bg_tile_clut_dict = get_used_bg_cluts()

    side = 8
    pics = bg_data["data"]

    for tile_index,cluts in bg_tile_clut_dict.items():
        # select the used tile
        pic = pics[tile_index]
        # select the proper row (for all tile color configurations - aka bitplane configurations)
        row = bg_matrix[tile_index]
        # generate the proper palette
        for clut_index in cluts:
            current_palette = [palette[i] for i in bg_tile_clut[clut_index]]
            if all(x==(0,0,0) for x in current_palette):
                row[clut_index*2] = 0
                row[clut_index*2+1] = 0
            else:
                d = generate_tile(pic,side,current_palette,palette,nb_planes=BG_NB_PLANES,is_sprite=False)
                row[clut_index*2] = d["standard"]
                row[clut_index*2+1] = d["mirror"]
                if dump_pngs:
                    ImageOps.scale(d["png"],scale,0).save("dumps/bg/img_{:02}_{}.png".format(tile_index,clut_index))


    table = "sprite"
    raw_pic_data = block_dict[table]

    sprite_matrix = raw_blocks[table] = [[None]*256 for _ in range(320)]
    # compute the RGB configuration used for each used tile. Generate a lookup table with
    sprite_tile_clut_dict = get_used_sprite_cluts()

    side = 16
    pics = raw_pic_data["data"]

    for tile_index,cluts in sprite_tile_clut_dict.items():
        # select the used tile
        pic = pics[tile_index]
        # select the proper row (for all tile color configurations - aka bitplane configurations)
        row = sprite_matrix[tile_index]
        # generate the proper palette
        for clut_index in cluts:
            current_palette = [palette[i & 0x7F] for i in sprite_tile_clut[clut_index]]
            if all(x==(0,0,0) for x in current_palette):
                row[clut_index*2] = 0
                row[clut_index*2+1] = 0
            else:
                d = generate_tile(pic,side,current_palette,palette,nb_planes=7,is_sprite=True)
                row[clut_index*2] = d["standard"]
                row[clut_index*2+1] = d["mirror"]
                if dump_pngs:
                    ImageOps.scale(d["png"],5,0).save("dumps/sprite/{}_{:02}_{}.png".format(sprite_names.get(tile_index,"img"),tile_index,clut_index))



    outfile = os.path.join(src_dir,"graphics.68k")
    #print("writing {}".format(os.path.abspath(outfile)))
    with open(outfile,"w") as f:
        nullptr = "NULLPTR"
        blankptr = "BLANKPTR"
        f.write("{} = 0\n".format(nullptr))
        f.write("{} = 1\n".format(blankptr))
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


        write_tiles("bg",bg_matrix,f,is_sprite=False,compress_blank_planes=True)

        # sprites are blitted, so require chipmem

        write_tiles("sprite",sprite_matrix,f,is_sprite=True,compress_blank_planes=False)
