import os,re,bitplanelib,ast,json
from PIL import Image,ImageOps

import gen_color_dict

import collections



dump_graphics = True  # uncomment for dry-run
dump_pngs = True  # uncomment for faster operation, pngs aren't needed for asset generation per se

sprite_color_count = collections.Counter()
sprite_color_usage = collections.defaultdict(set)

title_tiles = {240, 241, 242, 243, 244, 245, 246, 247, 248,
249, 256, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425,
426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437,
438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449,
 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461,
 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473,
 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485,
 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497,
 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511}

# this script uses the original graphics.c with palette & cluts
# and generates the bitmaps for the amiga version
#
# it uses a json file which is enriched by in-game logs of used
# bg tile/color & sprite/color used configurations (not all configurations
# are used). Without those in-game logs, it would be impossible to generate
# all possible combinations, it would take too much space (I think) even if
# there are already some optimizations to re-use bitplanes of differently colored
# sprites

block_dict = {}

black = (0,0,0)
white = (255,255,255)

BG_NB_PLANES = 4
STD_MIRROR_LIST = ("standard","mirror")

# where tile & sprite CLUT used configuration logs are fetch from
# we cannot possibly generate all tile & sprite CLUT configurations
# as that would generate gigabytes of graphics when only one or
# a few CLUTs are used for each background tile/sprite
#
# tile logs are dumped in debug mode when running the game, experiencing
# dashed tiles / flashing colors to indicate that such or such tile CLUT
# configuration is missing

winuae_dir = r"C:\Users\Public\Documents\Amiga Files\WinUAE"

def dump_json(data,outname):
    with open(outname,"w") as f:
        if isinstance(data,dict):
            data = {str(k):v for k,v in data.items()}
        json.dump(data,f,indent=2)

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
        print("{} log file was not dumped (normal when rebuilding with a complete .json file)".format(infile))

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
                    #print("found: tile_index: {}, clut_index: {}".format(tile_index,clut_index))
            row_index += 64

        save_json_tile_file(bg_json_base,rval,copy_rval)

    return rval

# used to predict which sprites will be used
# this feeds from a log computed at runtime and dumped with WinUAE
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
                attributes = contents[row_index+idx]
                if attributes:
                    # bit 7 already encoded in tile_index
                    # bit 3 = yflip: ignored atm we always generate both pics (which is maybe a waste!)
                    # bit 2 = xflip: can be done dynamically with inverted blitter
                    # bit 1 = double height: means we have to log others sprites with the same clut
                    # bit 0 = double width: idem

                    clut_index = idx
                    rval[tile_index].add(clut_index)
                    if attributes & 1:
                        rval[tile_index+1].add(clut_index)
                    if attributes & 2:
                        rval[tile_index+2].add(clut_index)
                        if attributes & 1:
                            rval[tile_index+3].add(clut_index)
            row_index += 128

        save_json_tile_file(sprite_json_base,rval,copy_rval)

    return rval

def remap_colors(tile_clut,color_dict,mask = 0xFF):
    # remap colors can fail to fetch color because quantization only considered
    # used CLUTs, not ALL cluts, but we need to keep the indices of the global CLUT

    return [[color_dict.get(tuple(x & mask for x in c),black) for c in clut] for clut in tile_clut]

def get_reduced_palette(reduced_color_dict):
    # we don't care about the keys here
    # sort unique values which ensures that 0,0,0 comes first :)
    lst = sorted(set(reduced_color_dict.values()))
    nb_colors = 1<<BG_NB_PLANES
    lst += [black]*(nb_colors-len(lst))
    return lst

# ATM all colors are considered the same weight
# should rather 1) create a big pic with all sprites & all cluts
# 2) apply quantize on that image
def quantize_palette_16(rgb_tuples,img_type):
    rgb_configs = set(rgb_tuples)
    # remove 0, we don't want it quantized
    rgb_configs.remove(black)
    rgb_configs.remove(white)
    rgb_configs = sorted(rgb_configs)
    dump_graphics = False
    # now compose an image with the colors
    clut_img = Image.new("RGB",(len(rgb_configs),1))
    for i,rgb in enumerate(rgb_configs):
        #rgb_value = (rgb[0]<<16)+(rgb[1]<<8)+rgb[2]
        clut_img.putpixel((i,0),rgb)

    reduced_colors_clut_img = clut_img.quantize(colors=14,dither=0).convert('RGB')

    # get the reduced palette
    reduced_palette = [reduced_colors_clut_img.getpixel((i,0)) for i,_ in enumerate(rgb_configs)]
    # apply rounding now
    # reduced_palette = bitplanelib.palette_round(reduced_palette,0xF0)
    #print(len(set(reduced_palette))) # should still be 15
    # now create a dictionary by associating the original & reduced colors
    rval = dict(zip(rgb_configs,reduced_palette))

    # add black back
    rval[black] = black
    rval[white] = white

    if False:  # debug it
        s = clut_img.size
        ns = (s[0]*30,s[1]*30)
        clut_img = clut_img.resize(ns,resample=0)
        clut_img.save("{}_colors_not_quantized.png".format(img_type))
        reduced_colors_clut_img = reduced_colors_clut_img.resize(ns,resample=0)
        reduced_colors_clut_img.save("{}_colors_quantized.png".format(img_type))

    # return it
    return rval

src_dir = "../../src/amiga"

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


# convert palette indexes to actual colors
# getting rid of palette imposed order, which allow us to organize the palette
# as we want to - for instance - impose color order so we can use sprites for
# most displayed items which are:
# player ship, bomb sights, shots, bombs (colors 16-31)
#

for n in ("bg_tile_clut","sprite_clut"):
    tc = block_dict[n]["data"]
    block_dict[n]["data"] = [[palette[i] for i in tile_clut] for tile_clut in tc ]

# reorganize palete like we want, leaving 0,0,0 first, keeping the xevious title
# filling color index unchanged (now that we found the color !) and putting the sprite
# colors in the required locations (bobs & bg tiles can still use them)
##import random
##palette = [palette[0]]+random.sample(palette[1:],len(palette)-1)

bg_tile_clut = block_dict["bg_tile_clut"]["data"]
sprite_tile_clut = block_dict["sprite_clut"]["data"]


def mkdir(d):
    if not os.path.exists(d):
        os.mkdir(d)

if dump_pngs:
    dump_root = "dumps"
    mkdir(dump_root)
    for d in ["bg_tile","fg_tile","sprite"]:
        mkdir(os.path.join(dump_root,d))

def populate_tile_matrix(matrix,side,pics,tile_clut_dict,is_sprite,image_names_dict,img_type,
                        tile_clut,
                        reduced_tile_clut,
                        global_palette):

    dumpdir = "dumps/{}".format(img_type)
    if dump_pngs:
        for x in ["orig","reduced"]:
            sd = os.path.join(dumpdir,x)
            if not os.path.isdir(sd):
                os.mkdir(sd)

    for tile_index,cluts in tile_clut_dict.items():
        # select the used tile
        pic = pics[tile_index]
        # select the proper row (for all tile color configurations - aka bitplane configurations)
        row = matrix[tile_index]
        # generate the proper palette
        for clut_index in cluts:
            used_palette = global_palette if is_sprite or tile_index not in title_tiles else title_tile_palette

            if dump_pngs:
                current_palette = tile_clut[clut_index]
                input_image = Image.new("RGB",(side,side))
                img_name = image_names_dict.get(tile_index,"img")
                for i,p in enumerate(pic):
                    col = current_palette[p]
                    y,x = divmod(i,side)
                    input_image.putpixel((x,y),col)
                    # statistics / color usage
                    sprite_color_count[col] += 1
                    sprite_color_usage[col].add(img_name)

                ImageOps.scale(input_image,scale,0).save("dumps/{}/orig/{}_{:02}_{}.png".format(img_type,img_name,tile_index,clut_index))

            current_palette = reduced_tile_clut[clut_index]
            if all(x==black for x in current_palette):
                row[clut_index] = 0
            else:

                try:
                    d = generate_tile(pic,side,current_palette,used_palette,nb_planes=BG_NB_PLANES,is_sprite=is_sprite)
                    # put dict in each slot
                    row[clut_index] = d
                    if dump_pngs:
                        ImageOps.scale(d["png"],scale,0).save("dumps/{}/reduced/{}_{:02}_{}.png".format(img_type,image_names_dict.get(tile_index,"img"),tile_index,clut_index))
                except bitplanelib.BitplaneException as e:
                    print("{}:{}: {}".format(tile_index,clut_index,e))

def write_tiles(t,matrix,f,is_bob):
    # background tiles/sprites: this is trickier as we have to write a big 2D table tileindex + all possible 64 color configurations (a lot are null pointers)

    f.write("\t.global\t{0}_picbase\n\t.global\t_{0}_tile\n_{0}_tile:".format(t))

    c = 0
    pic_list = []

    bob_plane_cache = {}
    bob_plane_id = 0

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
    # now write all defined pointers to pics (no relative shit
    # as data can be pretty big and overshoot 0x7FFF limit, which
    # explains the double indirection in the tables
    # 1) one table with word offsets to save memory, pointing on pointers
    # 2) one table of pointers that point on actual data
    #

    if is_bob:
        for i,item_data in enumerate(pic_list):
            if i == len(pic_list)//2:
                # base in the middle of the pics to avoid overflow
                f.write("{}_picbase:\n\tdc.w\t0\n".format(t))

            picname = "{}_pic_{:03d}".format(t,i)
            f.write("{0}:\n".format(picname))
            for k in STD_MIRROR_LIST:
                item = item_data[k]
                f.write("* {}\n".format(k))
                # first y offset & height
                f.write("\tdc.w\t{bitmap_type},0,{y_offset},{height}   | bitmap_type,pad,y_offset,height \n".format(**item_data))
                # we know that a lot of images are similar:
                # the palettes are different so the bitplanes are identical
                # only in a different order. Also, there's a lot of only-zero
                # planes as only 8 colors are used
                # so the picture (including mask) is a list of pointers on planes
                # plane data (32 bytes) are only listed once, and used a lot of times

                plane_size = 4*item_data["height"]   # 64 max

                for p in range(BG_NB_PLANES+1):  # +1: mask
                    block = tuple(item[p*plane_size:p*plane_size+plane_size])
                    block_id = bob_plane_cache.get(block)
                    if block_id is None:
                        # block is not in cache
                        block_id = bob_plane_id
                        bob_plane_cache[block] = block_id
                        bob_plane_id += 1
                    f.write("\tdc.l\tplane_pic_{}\n".format(block_id))
        f.write("\t.datachip\n")
        for k,v in sorted(bob_plane_cache.items(),key=lambda x:x[1]):
            f.write("plane_pic_{}:".format(v))
            dump_asm_bytes(k,f)
    else:
        f.write("{}_picbase:\n\tdc.w\t0\n".format(t))
        for i,_ in enumerate(pic_list):
            picname = "{}_pic_{:03d}".format(t,i)
            f.write("{0}:\n".format(picname))
            for k in STD_MIRROR_LIST:
                f.write("\tdc.l\t{}_{}_bytes\n".format(picname,k))
        for i,item_data in enumerate(pic_list):
            for k in STD_MIRROR_LIST:
                item = item_data[k]
                f.write("{}_pic_{:03d}_{}_bytes:".format(t,i,k))
                # bg tile
                item_pack = []
                # "compress" tile: detect all-zero plane and remove it
                # so if 0, clear plane, if nonzero (0xca), consider the 8 following bytes
                for p in range(BG_NB_PLANES):
                    block = item[p*8:p*8+8]
                    if any(block):
                        # non-zero somewhere
                        item_pack.append(0xca)   # 8 next bytes are useful
                        item_pack.extend(block)
                    else:
                        item_pack.append(0)      # clear tile plane
                item = item_pack

                dump_asm_bytes(item,f)

def generate_tile(pic,side,current_palette,global_palette,nb_planes,is_sprite):
    input_image = Image.new("RGB",(side,side))
    first_non_black_y = None
    last_non_black_y = 0
    for i,p in enumerate(pic):
        col = current_palette[p]
        y,x = divmod(i,side)
        input_image.putpixel((x,y),col)
        # note down first & last non-black line
        if col != black:
            if first_non_black_y is None:
                first_non_black_y = y
            if y > last_non_black_y:
                last_non_black_y = y

    if is_sprite:
        if first_non_black_y is None:
            first_non_black_y = 0
        # crop image to reduce size
        # saves memory and blitter bandwidth
        height = last_non_black_y-first_non_black_y+1

        if first_non_black_y != 0 or last_non_black_y != side:
            input_image = input_image.crop((0,first_non_black_y,side,first_non_black_y+height))
        y_offset = first_non_black_y
    else:
        y_offset = 0
        height = side

    rval = []
    for the_tile in [input_image,ImageOps.mirror(input_image)]:
        raw = bitplanelib.palette_image2raw(the_tile,output_filename=None,
        palette=global_palette,
        forced_nb_planes=nb_planes,
        generate_mask=is_sprite,
        blit_pad=is_sprite)
        rval.append(raw)

    return {"bitmap_type":"BT_BOB","png":input_image,"y_offset":y_offset,"height":height,"standard":rval[0],"mirror":rval[1]}

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

def clut_dict_to_rgb(tile_clut,used_cluts):
    cluts = (tile_clut[idx] for s in used_cluts.values() for idx in s)
    # flatten rgb
    return {x for c in cluts for x in c}


if dump_graphics:
# temp add all white for foreground

    raw_blocks = {}

    # foreground data, simplest of all 3
    table = "fg_tile"
    fg_data = block_dict[table]
    current_palette = [black,(96, 96, 96)]

    side = 8
    scale = 4
    pics = fg_data["data"]
    raw_blocks[table] = []
    for i,pic in enumerate(pics):
        d = generate_tile(pic,side,current_palette,current_palette,nb_planes=1,is_sprite=False)
        for s in STD_MIRROR_LIST:
            raw_blocks[table].append(d[s])
        if dump_pngs:
            ImageOps.scale(d["png"],scale,0).save("dumps/fg/img_{:02}.png".format(i))

    # background data: requires to generate as many copies of each tile that there are used CLUTs on that tile
    # the only way to know which CLUTs are used is to run the game and log them... We can't generate all pics, that
    # would take too much memory (512*64 pics of 16 color 8x8 tiles!!)

    reduced_color_dict = gen_color_dict.doit()

    table = "bg_tile"
    bg_data = block_dict[table]

    bg_matrix = raw_blocks[table] = [[None]*128 for _ in range(512)]
    # compute the RGB configuration used for each used tile. Generate a lookup table with

    used_bg_cluts = get_used_bg_cluts()
    #bg_used_colors = clut_dict_to_rgb(bg_tile_clut,used_bg_cluts)
    tilemap_quantized_rgb =  reduced_color_dict["map_tiles"]

    reduced_bg_tile_clut = remap_colors(bg_tile_clut,tilemap_quantized_rgb | reduced_color_dict["title_tiles"])
    partial_palette_bg = get_reduced_palette(tilemap_quantized_rgb)
    title_tile_palette = get_reduced_palette(reduced_color_dict["title_tiles"])
    # should be no all 32,64,0

    populate_tile_matrix(
    matrix = bg_matrix,
    side=8,
    pics = bg_data["data"],
    tile_clut_dict = used_bg_cluts,
    is_sprite = False,
    image_names_dict = {},
    img_type = table,
    reduced_tile_clut = reduced_bg_tile_clut,
    tile_clut = bg_tile_clut,
    global_palette = partial_palette_bg)

    # same for sprites

    table = "sprite"
    raw_pic_data = block_dict[table]

    # first dump all sprites with no particular color, doesn't matter
    #print()
    dummy_palette = ((0,0,0),(255,0,0),(0,255,0),(255,255,0),(255,0,255),(0,0,255),(255,255,255),(0,255,255))
    side = 16
    img = Image.new("RGB",(40*side,8*side))
    sx=0
    sy=0
    for pic in block_dict[table]["data"]:
        for i,p in enumerate(pic):
            col = dummy_palette[p]
            y,x = divmod(i,side)
            img.putpixel((sx+x,sy+y),col)
        sx += side
        if sx == img.size[0]:
            sx = 0
            sy += side

    img.save("dumps/sprites.png")
    used_sprite_cluts = get_used_sprite_cluts()
    sprite_used_colors = clut_dict_to_rgb(sprite_tile_clut,used_sprite_cluts)

    # what would be tremendous would be to remove mothership colors from palette, then use 2 AGA sprites
    # (with another palette, of course) to display it
    #bitplanelib.palette_dump(sprite_used_colors,"sprites.png",bitplanelib.PALETTE_FORMAT_PNG)
    to_remove = {(174,143,67):(98,)*3,
                (98,98,67):(98,)*3,
                (143,143,98):(143,)*3,
                # (174,174,143):(174,)*3,  used in explosion
                (210,210,174):(210,)*3}
    to_remove = {}
    sprite_used_colors = [x for x in sprite_used_colors if x not in to_remove]
    sprite_quantized_rgb = quantize_palette_16(sprite_used_colors,table) #reduced_color_dict["sprites"]


    reduced_sprite_tile_clut = remap_colors(sprite_tile_clut,sprite_quantized_rgb)
    partial_palette_sprite = get_reduced_palette(sprite_quantized_rgb)
    # pick a gray for the default fg tile color
    #gray = (0x8F,0x8F,0x79)
    #partial_palette_sprite.remove(gray)
    #partial_palette_sprite.insert(1,gray)
    # dump the (reduced) palette

    sprite_matrix = raw_blocks[table] = [[None]*128 for _ in range(320)]
    # compute the RGB configuration used for each used tile. Generate a lookup table with
    populate_tile_matrix(
    side = 16,
    pics = raw_pic_data["data"],
    tile_clut_dict = used_sprite_cluts,
    is_sprite = True,
    matrix = sprite_matrix,
    image_names_dict = sprite_names,
    img_type = "sprite",
    reduced_tile_clut = reduced_sprite_tile_clut,
    tile_clut = sprite_tile_clut,
    global_palette = partial_palette_sprite)

    # dump statistics on sprites
    color_stats = sorted([{"color":str(color),"used":sorted(sprite_color_usage[color]),"count":count}
    for color,count in sprite_color_count.items()],key=lambda x:x["count"])

    with open("dumps/spritecolors.json","w") as f:
        json.dump(color_stats,f,indent=2)

    # first background then sprites (bitplanes are configured accordingly)
    # also sprites are mainly bobs but to get the chance to use real HW sprites
    # the palette must be in 16-32 not in 0-16

    bitplanelib.palette_dump(gen_color_dict.original_palette,os.path.join(src_dir,"original_palette.68k"),
                            bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
    bitplanelib.palette_dump(partial_palette_bg+partial_palette_sprite,os.path.join(src_dir,"palette.68k"),
                            bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)
    bitplanelib.palette_dump(title_tile_palette,os.path.join(src_dir,"title_palette.68k"),
                            bitplanelib.PALETTE_FORMAT_ASMGNU,high_precision = True)


    outfile = os.path.join(src_dir,"graphics.68k")
    #print("writing {}".format(os.path.abspath(outfile)))
    with open(outfile,"w") as f:
        nullptr = "NULLPTR"
        blankptr = "BLANKPTR"
        f.write("{} = 0\n".format(nullptr))
        f.write("{} = 1\n".format(blankptr))
        f.write("""BT_BOB = 0
BT_SPRITE = 1
""")
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


        write_tiles("bg",bg_matrix,f,is_bob=False)

        # sprites are blitted, so require chipmem

        write_tiles("sprite",sprite_matrix,f,is_bob=True)
