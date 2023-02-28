import subprocess,os,struct,glob,tempfile
import shutil

sox = "sox"

if not shutil.which("sox"):
    raise Exception("sox command not in path, please install it")
# BTW convert wav to mp3: ffmpeg -i input.wav -codec:a libmp3lame -b:a 330k output.mp3

#wav_files = glob.glob("sounds/*.wav")

this_dir = os.path.dirname(__file__)
sound_dir = os.path.join(this_dir,"..","sounds")

this_dir = os.path.dirname(__file__)
src_dir = os.path.join(this_dir,"../../src/amiga")
outfile = os.path.join(src_dir,"sounds.68k")
sndfile = os.path.join(src_dir,"sound_entries.68k")

hq_sample_rate = 22050
lq_sample_rate = 8000

sound_dict = {"CREDIT_SND":{"index":0,"channel":0,"sample_rate":hq_sample_rate},
"ORDINAL_1_SND"          :{"index":0x01,"channel":0,"sample_rate":lq_sample_rate},
"HIGHEST_SCORE_SND"      :{"index":0x02,"channel":0,"sample_rate":lq_sample_rate,"loop":True},
"HIGH_SCORE_SND"         :{"index":0x03,"channel":0,"sample_rate":lq_sample_rate,"loop":True},
"EXTRA_SOLVALOU_SND"     :{"index":0x04,"channel":3,"sample_rate":hq_sample_rate},
"FLYING_ENEMY_HIT_SND"   :{"index":0x05,"channel":2,"sample_rate":hq_sample_rate},
"GARU_ZAKATO_SND"        :{"index":0x06,"channel":3,"sample_rate":hq_sample_rate},
"ANDOR_GENESIS_SND"      :{"index":0x07,"channel":3,"sample_rate":hq_sample_rate},
"SHEONITE_SND"           :{"index":0x08,"channel":3,"sample_rate":hq_sample_rate},
"TELEPORT_SND"           :{"index":0x09,"channel":2,"sample_rate":hq_sample_rate},
"BACURA_HIT_SND"         :{"index":0x0a,"channel":1,"sample_rate":hq_sample_rate},
"SHOT_SND"               :{"index":0x0b,"channel":1,"sample_rate":hq_sample_rate},
"BOMB_SND"               :{"index":0x0c,"channel":1,"sample_rate":hq_sample_rate},
"BONUS_FLAG_SND"         :{"index":0x0d,"channel":3,"sample_rate":hq_sample_rate},
"SOLVALOU_SND"           :{"index":0x0e,"channel":0,"sample_rate":lq_sample_rate,"loop":True},
}

sound_table = [""]*len(sound_dict)
sound_table_simple = [""]*len(sound_dict)



snd_header = rf"""
FXFREQBASE = 3579564

    .macro    SOUND_ENTRY    sound_name,size,channel,soundfreq,volume
\sound_name\()_sound:
    .long    \sound_name\()_raw
    .word   \size
    .word   FXFREQBASE/\soundfreq,\volume
    .byte    \channel
    .byte    1
    .endm

"""

raw_file = os.path.join(tempfile.gettempdir(),"out.raw")
with open(sndfile,"w") as fst,open(outfile,"w") as fw:
    fst.write(snd_header)

    fw.write("\t.datachip\n")
    for wav_file in sound_dict:
        wav_name = os.path.basename(wav_file).lower()[:-4]
        fw.write("\t.global\t{}_raw\n".format(wav_name))


    for wav_entry,details in sound_dict.items():
        wav_name = os.path.basename(wav_entry).lower()[:-4]
        wav_file = os.path.join(sound_dir,wav_name+".wav")

        def get_sox_cmd(sr,output):
            return [sox,"--volume","1.0",wav_file,"--channels","1","--bits","8","-r",str(sr),"--encoding","signed-integer",output]


        used_sampling_rate = details["sample_rate"]

        cmd = get_sox_cmd(used_sampling_rate,raw_file)

        subprocess.check_call(cmd)
        with open(raw_file,"rb") as f:
            contents = f.read()

        # compute max amplitude so we can feed the sound chip with a amped sound sample
        # and reduce the replay volume. this gives better sound quality than replaying at max volume
        signed_data = [x if x < 128 else x-256 for x in contents]
        maxsigned = max(signed_data)
        minsigned = min(signed_data)

        amp_ratio = max(maxsigned,abs(minsigned))/128

        wav = os.path.splitext(wav_name)[0]
        channel = details["channel"]
        sound_index = details["index"]
        sound_table[sound_index] = "    SOUND_ENTRY {},{},{},{},{}\n".format(wav,len(signed_data)//2,channel,used_sampling_rate,int(64*amp_ratio))
        sound_table_simple[sound_index] = f"\t.long\t{wav}_sound\n"

        maxed_contents = [int(x/amp_ratio) for x in signed_data]

        signed_contents = bytes([x if x >= 0 else 256+x for x in maxed_contents])
        # pre-pad with 0W, used by ptplayer for idling
        if signed_contents[0] != b'\x00' and signed_contents[1] != b'\x00':
            # add zeroes
            signed_contents = struct.pack(">H",0) + signed_contents
        with open(raw_file,"rb") as f:
            contents = f.read().rstrip(b"\x00")
        # pre-pad with 0W, used by ptplayer for idling
        if contents[0] != b'\x00' and contents[1] != b'\x00':
            # add zeroes
            contents = b'\x00\x00' + contents

        fw.write("{}_raw:   | {} bytes".format(wav,len(contents)))
        n = 0
        if len(contents)>65530:
            raise Exception(f"Sound {wav_entry} is too long")
        for c in contents:
            if n%16 == 0:
                fw.write("\n\t.byte\t0x{:x}".format(c))
            else:
                fw.write(",0x{:x}".format(c))
            n += 1
        fw.write("\n")
    # make sure next section will be aligned
    fw.write("\t.align\t8\n")
    fst.writelines(sound_table)
    fst.write("\n\t.global\t{0}\n\n{0}:\n".format("sound_table"))
    fst.writelines(sound_table_simple)

