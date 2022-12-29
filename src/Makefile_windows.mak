PROGNAME = xevious
HDBASE = K:\jff\AmigaHD
WHDBASE = $(HDBASE)\PROJETS\HDInstall\DONE\WHDLoad
WHDLOADER = ../$(PROGNAME).slave
SOURCE = $(PROGNAME)HD.s
MAIN = ..\$(PROGNAME)

GCC_BIN = C:\amiga-gcc\bin
ASM = $(GCC_BIN)/m68k-amigaos-as -I.. -c 
OBJS = amiga.o xevious_main.o graphics.o xevious_sub.o map_rom.o 

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
amiga.o: amiga/amiga.68k xevious.inc
	$(ASM) -Iamiga amiga/amiga.68k -o amiga.o
graphics.o: amiga/graphics.68k xevious.inc
	$(ASM) amiga/graphics.68k -o graphics.o

$(WHDLOADER) : $(SOURCE)
	wdate.py> datetime
	vasmm68k_mot -DDATETIME -I$(HDBASE)/amiga39_JFF_OS/include -I$(WHDBASE)\Include -I$(WHDBASE) -devpac -nosym -Fhunkexe -o $(WHDLOADER) $(SOURCE)
