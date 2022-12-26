
GCC_BIN = C:\amiga-gcc\bin
ASM = $(GCC_BIN)/m68k-amigaos-as -c 
OBJS = amiga.o xevious_main.o graphics.o xevious_sub.o map_rom.o 
MAIN = ../xevious
all: $(MAIN)

$(MAIN): $(OBJS)
	$(GCC_BIN)/m68k-amigaos-ld -o $(MAIN) $(OBJS)

xevious_main.o: xevious_main.68k src/xevious.inc
	$(ASM) xevious_main.68k -o xevious_main.o
map_rom.o: map_rom.68k
	$(ASM) map_rom.68k -o map_rom.o
xevious_sub.o: xevious_sub.68k src/xevious.inc
	$(ASM) xevious_sub.68k -o xevious_sub.o
amiga.o: amiga/amiga.68k
	$(ASM) -Iamiga amiga/amiga.68k -o amiga.o
graphics.o: amiga/graphics.68k
	$(ASM) amiga/graphics.68k -o graphics.o
