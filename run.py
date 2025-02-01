from synth import main as syn_main
from web_ch import main as get_main 
from player import main as play_main 
from lib.pytui.pytui import Tui
from stats import get_meta_data

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
initial_s = []
for _,s,_,_,_,_ in get_meta_data():
    initial_s += [s]


import math
def stats_thread(tui=Tui()):
    while True:
        tui.buffered  = True 
        tui.place_text("Chapters ready for reading:",row = 0, height=1)
        x = get_meta_data()
        l = len(str(max(x, key=lambda item: item[0])[0]))
        for i, (c,s,p,t,_,dir) in enumerate(x):
            r = min(int(math.log2(s-initial_s[i]+1)*64),255)
            tui.bg_colour = (r,0,64)
            if t <= s:
                s-=1
            if c == 0:
                if t == s:
                    tui.place_text(f"{c:>{l+2}}: {dir}", col = 0, row=i+1, height=1)
                else:
                    tui.place_text(f"{c:>{l+2}}: {dir} (ch {s}-{t})", col = 0, row=i+1, height=1)
            else:
                tui.place_text(f"{c:>{l+2}}: {dir} ch {p}-{s}", col = 0, row=i+1, height=1)
            tui.flush()
        tui.bg_colour = (0,0,64)
        time.sleep(.5)

def get_thread(tui=Tui()):
    while True:
        get_main(tui=tui)
        time.sleep(5*60)

def synth_thread(tui=Tui()):
    while True:
        syn_main(tui=tui)
        time.sleep(5*60)



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
        get_tui = Tui(col_offset=119,row_offset=2, max_width=80,max_height = 4, default_cursor_pos=input_pos,border=u"\u2588",bg_colour=bg) 
        get_p = Process(target=get_thread, args=(get_tui,))
        get_p.start()
        ps += [get_p]

    if "s" in do:
        syn_tui = Tui(col_offset=119,row_offset=5,max_width=80, max_height=19, default_cursor_pos=input_pos,border=u"\u2588",bg_colour=bg) 
        syn_p = Process(target=synth_thread, args=(syn_tui,))
        syn_p.start()
        ps += [syn_p]

    if "x" in do:
        stat_tui = Tui(col_offset=119,row_offset=23,max_width=80, max_height=22, default_cursor_pos=input_pos,border=u"\u2588",bg_colour=bg) 
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
    os.system("xset dpms force on")
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
