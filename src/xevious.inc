
* xevious.inc

***    
*** BUILD OPTIONS
***

    * hardware options
    OPT_DISABLE_FG_LAYER=0
    OPT_DISABLE_BG_LAYER=0
    OPT_DISABLE_SPRITES=0
    OPT_DISABLE_DISPLAY_MASKS=0

    * optimisation options
    OPT_SUB_HAS_IRQ=1
    * game options    
    OPT_START_AREA=14
    OPT_LOOP_AREA=0
    OPT_INVINCIBLE=1
    OPT_INFINITE_LIVES=0
    * score is BCD format
    OPT_START_SCORE=0x0000000
    OPT_ENABLE_HIGH_SCORE_IO=1
    OPT_TCDEV_EASTER_EGG=1
    OPT_REVEAL_SOL_TOWER=1
    OPT_REVEAL_BONUS_FLAG=1
    OPT_DISPLAY_AREA=0
    OPT_SKIP_SPLASH=0
    OPT_SKIP_ATTRACT=0

***
*** end of BUILD OPTIONS
***

* offsets into object table
    .equ  _STATE,     0
    .equ  _ATTR,      1
    .equ  _EXTRA,     4
    .equ  _X,         8
    .equ  _dX,        10
    .equ  _ddX,       12
    .equ  _Y,         14
    .equ  _dY,        16
    .equ  _ddY,       18
    .equ  _CODE,      20
    .equ  _COLOUR,    21
    .equ  _PTS,       22
    .equ  _TIMER,     24
    .equ  _TIMER1,    25
      .equ  _NVEC,    25
    .equ  _TIMER2,    26
      .equ  _VECLEN,  26
    .equ  _FFREQ,     28
    .equ  _TYPE,      30

    .equ  _OBJSIZE,   32

* video functions
    .equ  BANK_FG_COLORRAM,   (0<<2)
    .equ  BANK_BG_COLORRAM,   (1<<2)
    .equ  BANK_FG_VIDEORAM,   (2<<2)
    .equ  BANK_BG_VIDEORAM,   (3<<2)

* sound ordinals

    .equ  MAIN_THEME_SND,         0x01
    .equ  HIGHEST_SCORE_SND,      0x02
    .equ  HIGH_SCORE_SND,         0x03
    .equ  EXTRA_SOLVALOU_SND,     0x04
    .equ  FLYING_ENEMY_HIT_SND,   0x05
    .equ  GARU_ZAKATO_SND,        0x06
    .equ  ANDOR_GENESIS_SND,      0x07
    .equ  SHEONITE_SND,           0x08
    .equ  TELEPORT_SND,           0x09
    .equ  BACURA_HIT_SND,         0x0a
    .equ  SHOT_SND,               0x0b
    .equ  BOMB_SND,               0x0c
    .equ  BONUS_FLAG_SND,         0x0d
    .equ  SOLVALOU_SND,           0x0e
    * 60XX (noise chip?)
    .equ  COIN_SND,               0x10
    .equ  GROUND_EXPLOSION_SND,   0x11
    .equ  SOLVALOU_EXPLOSION_SND, 0x12
    
***
*** global variables
***
    .global vb_semaphore_sub
    .global two_player_game
    .global curr_player_score_msb
    .global area_obj_ptr
    .global start_pressed
    .global bg_scroll_x_shadow
    .global scroll_cntr
    .global maincpu_inited
    .global countup_timer_1
    .global curr_player
    .global is_real_game
    .global area
    .global enemy_AI_level
    .global solvalou_number
    .global bacura_inc_cnt
    .global ffreq_mask_derota
    .global ffreq_mask_kapi
    .global ffreq_mask_terrazi
    .global ffreq_mask_logram
    .global ffreq_mask_zoshi
    .global ffreq_mask_boza_logram
    .global ffreq_mask_domogram
    .global ffreq_mask_andor_genesis
    .global gnd_stop_firing_row
    .global scroll_disabled
    .global num_flying_enemies
    .global flying_enemy_type_tbl_offset
    .global num_bacura
    .global sheonite_end_flag
    .global andor_genesis_end_flag
    .global scroll_delta
    .global area_offset_in_map
    .global dswb
    .global pulsing_colour_1
    .global pulsing_colour_2
    .global next_domogram
    .global domogram_tbl

***
*** global data structures
***
    .global area_offset_in_map_tbl
    .global sprite_shadow_msb

    