
from synth import main as syn_main
from web_ch import main as get_main 
from player import main as play_main 
from lib.pytui.pytui import Tui
from stats import get_chapters_left
import screen_brightness_control as sbc
initial_brightness = sbc.get_brightness()[0]

def get_var(name, default=None):
    if name in locals():
        return locals()[name]
    elif name in globals():
        return globals()[name]
    return default
import time
import signal
import os
import sys
os.makedirs("output/.logging", exist_ok=True)
sys.stderr = open('output/.logging/run.log', 'w')
from multiprocessing import Process, active_children

def stats_thread(tui=Tui()):
    while True:
        tui.buffered  = True 
        tui.place_text("Chapters ready for reading:",row = 0, height=1)
        x = get_chapters_left()
        l = len(str(max(x, key=lambda item: item[0])[0]))
        for i, (c,_,_,dir) in enumerate(x):
            tui.place_text(f"{c:>{l}}: {dir}", col = 2, row=i+1, height=1)
        tui.flush()
        time.sleep(.5)

def get_thread(tui=Tui()):
    while True:
        get_main(tui=tui)
        time.sleep(15*60)

def synth_thread(tui=Tui()):
    while True:
        syn_main(tui=tui)
        time.sleep(15*60)



def main():
    do = "gspx"
    if len(sys.argv) > 1:
        do = sys.argv[1]
    
    tui=Tui()
    tui.clear()
    input_pos = (1,1)
    bg = (0,0,64)
    ps = []

    if "g" in do:
        get_tui = Tui(col_offset=119,row_offset=2, max_width=60,max_height = 4, default_cursor_pos=input_pos,border=u"\u2588",bg_colour=bg) 
        get_p = Process(target=get_thread, args=(get_tui,))
        get_p.start()
        ps += [get_p]

    if "s" in do:
        syn_tui = Tui(col_offset=119,row_offset=5,max_width=60, max_height=19, default_cursor_pos=input_pos,border=u"\u2588",bg_colour=bg) 
        syn_p = Process(target=synth_thread, args=(syn_tui,))
        syn_p.start()
        ps += [syn_p]

    if "x" in do:
        stat_tui = Tui(col_offset=119,row_offset=23,max_width=60, max_height=22, default_cursor_pos=input_pos,border=u"\u2588",bg_colour=bg) 
        stat_p = Process(target=stats_thread, args=(stat_tui,))
        stat_p.start()
        ps += [stat_p]

    if "p" in do:
        play_tui = Tui(col_offset=0,row_offset=2,default_cursor_pos=input_pos,max_width=120, max_height=43,border=u"\u2588",bg_colour=bg) 
        play_main(play_tui)
        for p in ps:
            p.terminate()
        stop(signal.SIGTERM)

def signal_handler(sig, frame):
    fn = get_var('stop')
    if fn:
        fn(sig)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
def stop(sig):
    initial_brightness = get_var('initial_brightness')
    if initial_brightness:
        sbc.set_brightness(initial_brightness)
    driver = get_var('driver')
    if driver:
        driver.quit()
    for child in [get_var('ui_p'), get_var('player_p'), get_var('get_p'), get_var('syn_p'), get_var('stat_p')]:
        if child:
            os.kill(child.pid, sig)
    for child in active_children():
        if child.pid:
            os.kill(child.pid, sig)
    time.sleep(0.1)
    for child in active_children():
        if child.pid:
            os.kill(child.pid, signal.SIGKILL)
    if __name__ == '__main__':
        Tui(hide_cursor=False)
    exit(0)


if __name__ == "__main__":
    main()
