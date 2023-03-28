; Jim Power slave
	INCDIR	Include:
	INCLUDE	whdload.i
	INCLUDE	whdmacros.i
;CHIP_ONLY
	IFD	CHIP_ONLY
CHIPMEMSIZE = $200000
EXPMEMSIZE = 0
	ELSE
CHIPMEMSIZE = $100000
EXPMEMSIZE = $100000
	ENDC
	
_base	SLAVE_HEADER					; ws_security + ws_id
	dc.w	17					; ws_version (was 10)
	dc.w	WHDLF_NoError|WHDLF_ReqAGA|WHDLF_Req68020
	dc.l	CHIPMEMSIZE					; ws_basememsize
	dc.l	0					; ws_execinstall
	dc.w	start-_base		; ws_gameloader
	dc.w	_data-_base					; ws_currentdir
	dc.w	0					; ws_dontcache
_keydebug
	dc.b	$0					; ws_keydebug
_keyexit
	dc.b	$59					; ws_keyexit
_expmem
	dc.l	EXPMEMSIZE					; ws_expmem
	dc.w	_name-_base				; ws_name
	dc.w	_copy-_base				; ws_copy
	dc.w	_info-_base				; ws_info
    dc.w    0     ; kickstart name
    dc.l    $0         ; kicksize
    dc.w    $0         ; kickcrc
    dc.w    _config-_base
;---
_config
	dc.b    "C1:L:lives:3,1,2,5;"
	dc.b    "C2:L:skill level:normal,easy,hard,hardest;"
	dc.b    "C3:X:flag awards bonus life:0;"    
	dc.b    "C3:X:no in-game music:1;"    
	dc.b	0

	IFD BARFLY
	DOSCMD	"WDate  >T:date"
	ENDC

DECL_VERSION:MACRO
	dc.b	"1.0"
	IFD BARFLY
		dc.b	" "
		INCBIN	"T:date"
	ENDC
	IFD	DATETIME
		dc.b	" "
		incbin	datetime
	ENDC
	ENDM
_data   dc.b    0
_name	dc.b	'Xevious',0
_copy	dc.b	'1982 Namco',0
_info
    dc.b	"68k transcode & design by Mark Mc Dougall",10
    dc.b	"Amiga port by JOTD",0
	dc.b	0
_kickname   dc.b    0
;--- version id

    dc.b	0
    even

start:
	LEA	_resload(PC),A1
	MOVE.L	A0,(A1)
	move.l	a0,a2

    IFD CHIP_ONLY
    lea  _expmem(pc),a0
    move.l  #CHIPMEMSIZE/2,(a0)
	; full chipmem: enable cache for representativity
	move.l	#WCPUF_Base_WT|WCPUF_Exp_CB|WCPUF_Slave_CB|WCPUF_IC|WCPUF_DC|WCPUF_BC|WCPUF_SS|WCPUF_SB,d0	
	ELSE
	move.l	#WCPUF_Base_NC|WCPUF_Exp_CB|WCPUF_Slave_CB|WCPUF_IC|WCPUF_DC|WCPUF_BC|WCPUF_SS|WCPUF_SB,d0	
    ENDC
	
	;enable cache
	move.l	#WCPUF_All,d1
	jsr	(resload_SetCPU,a2)


    lea progstart(pc),a0
    move.l  _expmem(pc),(a0)

	move.l	_expmem(pc),d0
	add.l	#EXPMEMSIZE,D0
	move.l	d0,a7
	
	lea	exe(pc),a0
	move.l  progstart(pc),a1
	jsr	(resload_LoadFileDecrunch,a2)
	move.l  progstart(pc),a0
    bsr   _Relocate
	move.l	_resload(pc),a0
    move.l  #'WHDL',d0
    move.b  _keyexit(pc),d1
	move.l  progstart(pc),-(a7)
    
    lea  _custom,a1
    move.w  #$1200,bplcon0(a1)
    move.w  #$0024,bplcon2(a1)
    

    rts
	
_Relocate	movem.l	d0-d1/a0-a2,-(sp)
        clr.l   -(a7)                   ;TAG_DONE
;        pea     -1                      ;true
;        pea     WHDLTAG_LOADSEG
        move.l  #$400,-(a7)       ;chip area
        pea     WHDLTAG_CHIPPTR        
        pea     8                       ;8 byte alignment
        pea     WHDLTAG_ALIGN
        move.l  a7,a1                   ;tags		move.l	_resload(pc),a2
		jsr	resload_Relocate(a2)
        add.w   #5*4,a7

        movem.l	(sp)+,d0-d1/a0-a2
		rts

_resload:
	dc.l	0
progstart
    dc.l    0
exe
	dc.b	"xevious",0
	