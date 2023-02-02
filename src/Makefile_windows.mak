PROGNAME = xevious
HDBASE = K:\jff\AmigaHD
WHDBASE = $(HDBASE)\PROJETS\HDInstall\DONE\WHDLoad
WHDLOADER = ../$(PROGNAME).slave
SOURCE = $(PROGNAME)HD.s
MAIN = ..\$(PROGNAME)

GCC_BIN = C:\amiga-gcc\bin
ASM = $(GCC_BIN)/m68k-amigaos-as -c 
MAIN_OBJ = amiga.o
# leave MAIN_OBJ first
OBJS = $(MAIN_OBJ) sounds.o xevious_main.o graphics.o xevious_sub.o map_rom.o ReadJoyPad.o ptplayer.o 
all: $(MAIN) $(WHDLOADER)

clean:
	del $(OBJS) "$(MAIN)"
	
$(MAIN): $(OBJS)
	$(GCC_BIN)/m68k-amigaos-ld -o $(MAIN) $(OBJS)

xevious_main.o: xevious_main.68k xevious.inc
	$(ASM) xevious_main.68k -o xevious_main.o
map_rom.o: map_rom.68k xevious.inc
	$(ASM) map_rom.68k -o map_rom.o
xevious_sub.o: xevious_sub.68k xevious.inc
	$(ASM) xevious_sub.68k -o xevious_sub.o
amiga.o: amiga/amiga.68k xevious.inc amiga/ReadJoyPad.inc amiga/palette.68k
	$(ASM) -Iamiga amiga/amiga.68k -o amiga.o
ptplayer.o: amiga/ptplayer.68k
	$(ASM) -Iamiga amiga/ptplayer.68k -o ptplayer.o
sounds.o: amiga/sounds.68k
	$(ASM) -Iamiga amiga/sounds.68k -o sounds.o
ReadJoyPad.o: amiga/ReadJoyPad.68k amiga/ReadJoyPad.inc
	$(ASM) -Iamiga amiga/ReadJoyPad.68k -o ReadJoyPad.o
graphics.o: amiga/graphics.68k xevious.inc
	$(ASM) amiga/graphics.68k -o graphics.o

$(WHDLOADER) : $(SOURCE)
	wdate.py> datetime
	vasmm68k_mot -DDATETIME -I$(HDBASE)/amiga39_JFF_OS/include -I$(WHDBASE)\Include -I$(WHDBASE) -devpac -nosym -Fhunkexe -o $(WHDLOADER) $(SOURCE)
