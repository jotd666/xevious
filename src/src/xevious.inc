
* xevious.inc

***    
*** BUILD OPTIONS
***

		* hardware options
		OPT_DISABLE_FG_LAYER=0
		OPT_DISABLE_BG_LAYER=0
		OPT_DISABLE_SPRITES=0
		OPT_DISABLE_DISPLAY_MASKS=0

		* game options		
		OPT_START_AREA=9
		OPT_LOOP_AREA=1
		OPT_INVINCIBLE=0
		OPT_INFINITE_LIVES=0
		OPT_NEOGEO_EASTER_EGG=1
		OPT_REVEAL_SOL_TOWER=0
		OPT_REVEAL_BONUS_FLAG=0
		OPT_DISPLAY_AREA=1

***
*** end of BUILD OPTIONS
***

* offsets into object table
		.equ	_STATE,			0
		.equ	_ATTR,			1
		.equ	_EXTRA,			4
		.equ	_X,					8
		.equ	_dX,				10
		.equ  _ddX,       12
		.equ	_Y,					14
		.equ	_dY,				16
		.equ  _ddY,       18
		.equ 	_CODE, 			20
		.equ	_COLOUR,		21
		.equ	_PTS,				22
		.equ	_TIMER,			24
		.equ	_TIMER1,		25
		  .equ	_NVEC,		25
		.equ	_TIMER2,		26
		  .equ	_VECLEN,	26
		.equ	_FFREQ,			28
		.equ	_TYPE,			30

		.equ	_OBJSIZE,		32

* video functions
		.equ	BANK_FG_COLORRAM,		0
		.equ	BANK_BG_COLORRAM,		1
		.equ	BANK_FG_VIDEORAM,		2
		.equ	BANK_BG_VIDEORAM,		3


***
***	global variables
***
		.global vb_semaphore_sub
		.global two_player_game
		.global area_obj_ptr
		.global start_pressed
		.global bg_scroll_x_shadow
		.global scroll_cntr
		.global maincpu_inited
		.global countup_timer_1
		.global curr_player
		.global is_real_game
		.global area
		.global fire_freq_mask_derota
		.global fire_freq_mask_kapi
		.global fire_freq_mask_terrazi
		.global fire_freq_mask_logram
		.global fire_freq_mask_81A4
		.global fire_freq_mask_boza_logram
		.global fire_freq_mask_domogram
		.global byte_81A7
		.global gnd_stop_firing_row
		.global scroll_disabled
		.global num_flying_enemies
		.global flying_enemy_type_tbl_offset
		.global max_bacura
		.global scroll_delta
		.global area_offset_in_map
		.global pulsing_colour_1
		.global pulsing_colour_2
		.global next_domogram
		.global domogram_tbl

***
*** global data structures
***
		.global area_offset_in_map_tbl
		