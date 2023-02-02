import subprocess,os,struct,tempfile

sox = r"k:\progs\sox-14-4-2\sox.exe"

wav_files = ["credit.wav"]
outfile = "../src/amiga/sounds.68k"


sampling_rate = 22050
alt_sampling_rate = 16000
nb_duplicates = 2

raw_file = os.path.join(tempfile.gettempdir(),"out.raw")
with open(outfile,"w") as fw:
    fw.write("\t.datachip\n")
    for wav_file in wav_files:
        wav_name = os.path.splitext(wav_file)[0]
        fw.write("\t.global\t{}_raw\n".format(wav_name))
        fw.write("\t.global\t{}_raw_end\n".format(wav_name))
    for wav_file in wav_files:
        wav_name = os.path.splitext(wav_file)[0]

        def get_sox_cmd(sr,output):
            return [sox,"--volume","1.0",wav_file,"--channels","1","--bits","8","-r",str(sr),"--encoding","signed-integer",output]
        used_sampling_rate = sampling_rate  #alt_sampling_rate if "loop_fright" in wav_file else sampling_rate

        cmd = get_sox_cmd(used_sampling_rate,raw_file)

        subprocess.check_call(cmd)
        with open(raw_file,"rb") as f:
            contents = f.read().rstrip(b"\x00")
        # pre-pad with 0W, used by ptplayer for idling
        if contents[0] != b'\x00' and contents[1] != b'\x00':
            # add zeroes
            contents = b'\x00\x00' + contents

        fw.write("{}_raw:   | {} bytes".format(wav_name,len(contents)))
        n = 0
        for c in contents:
            if n%16 == 0:
                fw.write("\n\t.byte\t0x{:x}".format(c))
            else:
                fw.write(",0x{:x}".format(c))
            n += 1
        fw.write("\n{}_raw_end:\n".format(wav_name))
