from synth import main as syn_main
from web_ch import main as get_main 
from player import main as play_main 
from lib.pytui.pytui import Tui

import sys
import time
import signal
import os
from multiprocessing import Process, active_children
from playa_utils import get_var
def signal_handler(sig, frame):
    fn = get_var('stop')
    if fn:
        fn(sig)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
def stop(sig):
    syn_tui = get_var('syn_tui')
    if syn_tui:
        syn_tui.buffered  = True 
        syn_tui.clear_box(row=2+lines_offset)
        syn_tui.place_text("Synth interrupted",row = 2+lines_offset, height=1)
        syn_tui.place_text("Chapters ready for reading:",row = 3+lines_offset, height=1)
        x = get_chapters_left()
        l = len(str(max(x, key=lambda item: item[0])[0]))
        for i, (c,_,_,dir) in enumerate(x):
            syn_tui.place_text(f"{c:>{l}}: {dir}", col = 2, row=lines_offset+4+i, height=1)
        syn_tui.flush()
    for child in [get_var('ui_p'), get_var('player_p'), get_var('get_p'), get_var('syn_p')]:
        if child:
            os.kill(child.pid, sig)
    driver = get_var('driver')
    get_tui = get_var('get_tui')
    if driver:
        driver.quit()
    if get_tui:
        get_tui.place_text("Web getter Interrupted", height=1)
    for child in active_children():
        os.kill(child.pid, sig)
    time.sleep(0.1)
    for child in active_children():
        os.kill(child.pid, signal.SIGKILL)
    if __name__ == '__main__':
        tui=Tui(hide_cursor=False)
    exit(0)

def main():
    do = "gsp"
    if len(sys.argv) > 1:
        do = sys.argv[1]
    ps = []
    tui=Tui()
    tui.clear()
    input_pos = (0,30)
    all_col_offset = 0 
    all_row_offset = 0 
    if "g" in do:
        get_tui = Tui(col_offset=all_col_offset+(70 if "p" in do else 0),row_offset=all_row_offset, default_cursor_pos=input_pos) 
        if "s" in do: 
            get_tui.max_height = 2
        get_p = Process(target=get_main, args=(get_tui,))
        get_p.start()
        ps += [get_p]

    if "s" in do:
        syn_tui = Tui(col_offset=all_col_offset+(70 if "p" in do else 0),row_offset=all_row_offset+(3 if "g" in do else 0), default_cursor_pos=input_pos) 
        syn_p = Process(target=syn_main, args=(syn_tui,))
        syn_p.start()
        ps += [syn_p]

    if "p" in do:
        play_tui = Tui(col_offset=all_col_offset,row_offset=all_row_offset,default_cursor_pos=input_pos) 
        if "s" in do or "g" in do:
            play_tui.max_width = 60
        play_main(play_tui)
        stop(signal.SIGTERM)


    for child in multiprocessing.active_children():
        child.wait()


if __name__ == "__main__":
    main()
