import subprocess
import time 
import os
import sys 
from pytimedinput import timedKey, timedKeyOrNumber
import safer
from lib.pytui.pytui import Tui
pollRate = 0.1

def _print(x):
    for _ in range(3):
        try:
            print(x)
        except:
            print("error when printing, retrying!")
            continue
        break

debug = False

def popen(cmd):
    d = {'args': cmd} if debug else {'args': cmd,'stdout':subprocess.DEVNULL, 'stderr':subprocess.DEVNULL}
    return subprocess.Popen(**d)

def run(cmd):
    d = {'args': cmd,'capture_output':True} 
    return subprocess.run(**d)

from multiprocessing import Process 

import signal
def signal_handler(sig, frame):
    if 'ui_p' in frame.f_locals:
        frame.f_locals['ui_p'].terminate()
    elif 'ui_p' in frame.f_globals:
        frame.f_globals['ui_p'].terminate()
    if 'player_p' in frame.f_locals:
        frame.f_locals['player_p'].kill()
    elif 'player_p' in frame.f_globals:
        frame.f_globals['player_p'].kill()
    sys.exit(sig)

signal.signal(signal.SIGINT, signal_handler)

def format_time(in_sec):
    hr = int(in_sec/(60*60))
    min = int((in_sec-hr*60*60)/60)
    sec = int(in_sec%60)
    msec = int((in_sec*1000)%1000)
    return f"{hr:02}:{min:02}:{sec:02}:{msec:03}"

def progress_bar(t,dur):
    l = 20
    fill = int((t*l)/dur)
    empty = 20-fill 
    return f"{format_time(t)} [{'#'*fill}{'.'*empty}] {format_time(dur)}"

def get_ch_txt_fp(book, ch):
    return f"output/{book}/.working/txt/ch{ch:04}"

def get_block_times(book, ch):
    ts_fp = f"{get_ch_txt_fp(book,ch)}/timestamps.txt"
    if not os.path.isfile(ts_fp):
        return None
    block_times = [0]
    with safer.open(ts_fp, "r") as ts :
        times = [float(d) for d in ts.read().split("\n")[:-1]]
        for d in times:
            block_times += [block_times[-1] + d]
    return block_times

def get_block(t, block_times, book, ch, prev_block=0):
    if block_times is None:
        return ("", prev_block)
    block = prev_block
    while block + 1 < len(block_times) and t > block_times[block+1]:
        block += 1 
    b_fp = f"{get_ch_txt_fp(book,ch)}/b{block:04}.txt"
    if not os.path.exists(b_fp):
        return ("", block)
    with safer.open(b_fp, "r") as f:
        return (str(f.read()), block)

def update_t(book,speed,dur,ch,tui,once=False):
    t = 0
    dt = 1/speed 
    block_times = get_block_times(book, ch)
    block = 0 
    first = True
    while True:
        with safer.open(get_t_fp(book),"r") as tf:
            t = float(tf.read())
        with safer.open(get_t_fp(book),"w") as tf:
            tf.write(str(t+speed*dt))
        tui.set_buffered(True)
        tui.place_text(progress_bar(t,dur), row=1, height=1)
        text, n_block = get_block(t, block_times, book, ch, block)
        if first or n_block != block:
            tui.clear_box(row=2, height=10)
            tui.place_text(text.replace('\n', ' '), row=2, height=10)
            first = False 
            block = n_block
        tui.flush()
        tui.set_buffered(False)

        if once:
            break
        time.sleep(dt)
        

def get_mp3_fp(book, ch):
    return f"output/{book}/ch{ch:04}.mp3"

def get_duration(mp3_fp):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", mp3_fp]).stdout.decode())

def start_mp3(mp3_fp, speed, t):
    return popen(["ffplay","-af",f"atempo={speed}", "-nodisp", "-autoexit", "-stats", "-ss", f"{t}s", mp3_fp])

def get_t_fp(book):
    return f"output/{book}/.working/t.txt"

def get_pch_fp(book):
    return f"output/{book}/.working/pch.txt"

def get_header(book, ch, speed):
    return f"playing {book} ch: {ch} ({speed}x)\n"

def play_ch(speed,book,tui):
    ch = 0
    t = 0
    with safer.open(get_pch_fp(book),"r") as chf:
        ch = int(chf.read())
    with safer.open(get_t_fp(book),"r") as tf:
        try:
            t = max(float(tf.read())-5,0)
        except:
            t = 0
    with safer.open(get_t_fp(book),"w") as tf:
        tf.write(str(t))
    mp3_fp = get_mp3_fp(book, ch)
    tui.clear()
    tui.place_text(get_header(book,ch,speed), row=0, height=1)
    w = 1 
    while not os.path.isfile(mp3_fp):
        tui.clear()
        tui.place_text(f"{mp3_fp} not found, retrying in 10s ({w})", row=0, height=1)
        w += 1
        x, timedOut = timedKey(timeout=10, resetOnInput = False, allowCharacters=f"t", pollRate = pollRate)
        if timedOut:
            continue
        if x == 't':
            return 1 
    dur = get_duration(mp3_fp) 
    ui_p = Process(target=update_t, args=(book,speed,dur,ch,tui))
    ui_p.start()
    player_p = start_mp3(mp3_fp, speed, t)
    unpaused = True
    prec1 = ''
    prec2 = ''
    block_times = get_block_times(book, ch)
    while True:
        with safer.open(get_t_fp(book),"r") as tf:
            t = float(tf.read())

        if dur-t <= 0:
            break

        x, timedOut = timedKey(timeout=-1 if not unpaused else (dur-t)/speed, resetOnInput = False, allowCharacters=f" pt{KEY_LEFT}{KEY_RIGHT}{KEY_UP}{KEY_DOWN}{PREC}wsjk",pollRate = pollRate, eatInput = True)
        if timedOut:
            break
        prec = prec1 + prec2
        prec1 = prec2
        prec2 = x
        
        if x in ' p':
            unpaused = not unpaused
            if unpaused:
                player_p = start_mp3(mp3_fp, speed, t)
                ui_p = Process(target=update_t, args=(book,speed,dur,ch,tui))
                ui_p.start()
            else:
                player_p.kill()
                ui_p.terminate()
        if x == 't':
            if unpaused:
                player_p.kill()
                ui_p.terminate()
            return 1 
        if (x in f"{KEY_LEFT}{KEY_RIGHT}" and prec == PREC) or x in "jk":
            player_p.kill()
            ui_p.terminate()
            with safer.open(get_t_fp(book),"r") as tf:
                t = float(tf.read())
            with safer.open(get_t_fp(book),"w") as tf:
                if x in f"{KEY_LEFT}j": 
                    if t < 15 and os.path.isfile(get_mp3_fp(book, ch-1)):
                        ch -= 1
                        block_times = get_block_times(book, ch)
                        mp3_fp = get_mp3_fp(book, ch)
                        dur = get_duration(mp3_fp)
                        t += dur 
                        tui.place_text(get_header(book,ch,speed), row=0, height=1)
                        with safer.open(get_pch_fp(book),"w") as chf:
                            chf.write(str(ch))
                    t = max(t-15,0)
                else: 
                    if t > dur - 15 and os.path.isfile(get_mp3_fp(book, ch+1)):
                        ch += 1
                        block_times = get_block_times(book, ch)
                        mp3_fp = get_mp3_fp(book, ch)
                        t -= dur 
                        dur = get_duration(mp3_fp)
                        tui.place_text(get_header(book,ch,speed), row=0, height=1)
                        with safer.open(get_pch_fp(book),"w") as chf:
                            chf.write(str(ch))
                    t = min(t+15,dur)
                tf.write(str(t))
            tui.place_text(progress_bar(t,dur), row=1, height=1)
            text, b = get_block(t, block_times, book, ch, 0)
            tui.place_text(text.replace('\n', ' '), row=2, height=10)
            if unpaused:
                player_p = start_mp3(mp3_fp, speed, t)
                ui_p = Process(target=update_t, args=(book,speed,dur,ch,tui))
                ui_p.start()
        if(x in f"{KEY_UP}{KEY_DOWN}" and prec == PREC) or x in "ws":
            player_p.kill()
            ui_p.terminate()
            with safer.open(get_t_fp(book),"r") as tf:
                t = float(tf.read())
            if x in f"{KEY_DOWN}s":
                speed = max(speed-0.25, 0.25)
            else:
                speed = speed+0.25
            with safer.open(dsfp, "w") as dsf:
                dsf.write(str(speed))
            tui.place_text(get_header(book,ch,speed), row=0, height=1)
            if unpaused:
                player_p = start_mp3(mp3_fp, speed, t)
                ui_p = Process(target=update_t, args=(book,speed,dur,ch,tui))
                ui_p.start()

    player_p.wait()
    ui_p.terminate()
    with safer.open(get_t_fp(book),"w") as tf:
        tf.write("0")
    with safer.open(get_pch_fp(book),"w") as chf:
        chf.write(str(ch+1))
    return 0 

dbfp = "output/.def_book"
dsfp = "output/.def_speed"
def get_speed(tui):
    default_speed_existed = True
    if not os.path.isfile(dsfp):
        default_speed_existed = False 
        with safer.open(dsfp, "w") as dsf:
            dsf.write("1")
    with safer.open(dsfp, "r") as dsf:
        default_speed = float(dsf.read())
    speed = default_speed
    if not default_speed_existed:
        tui.clear()
        tui.place_text(f"Choose a speed ({default_speed}):\n",row=0, height=1)
        i, _ = timedKeyOrNumber(timeout = -1, allowCharacters = "t", allowNegative = False, pollRate = pollRate)
        tui.clear()
        if i == 't':
            return get_book()
        if i != None:
            speed = i
        with safer.open(dsfp, "w") as dsf:
            dsf.write(str(speed))
    return speed

def get_book(tui):
    tui.clear()
    book = "" 
    books = []
    for dir in os.listdir("output"):
        dir_fp = f"output/{dir}"
        if not os.path.isdir(dir_fp):
            continue
        books += [dir] 
    if not os.path.isfile(dbfp):
        with safer.open(dbfp, "w") as dbf:
            dbf.write(books[0])

    default_book = ""
    with safer.open(dbfp, "r") as dbf:
        default_book = str(dbf.read())
    book = default_book
    tui.set_buffered(True)
    tui.clear()
    tui.place_text(f"Choose a book (1-{len(books)}):", height=1, row=0)
    for i,b in enumerate(books):
        tui.place_text(f"{i+1:>2} {b}", height=1, col=2, row=i+1)
    tui.flush()
    tui.set_buffered(False)
    arrow_number = books.index(default_book)
    while True:
        tui.place_text("->", row=arrow_number+1, width = 2, height=1)
        i, _ = timedKeyOrNumber(timeout = -1, allowCharacters = f"tws", allowNegative = False, allowFloat = False, pollRate = pollRate)
        if i == 't':
            tui.clear()
            tui.hide_cursor(False)
            quit(0)
        if i == "w":
            tui.place_text("", row=arrow_number+1, width = 2, height=1)
            arrow_number = max(0, arrow_number-1)
            book = books[arrow_number]
            continue
        if i == "s":
            tui.place_text("", row=arrow_number+1, width = 2, height=1)
            arrow_number = min(len(books)-1, arrow_number+1)
            book = books[arrow_number]
            continue
        if i != None:
            if i == 0 or i > len(books):
                continue
            book = books[i-1]
        with safer.open(dbfp, "w") as dbf:
            dbf.write(book)
        break
    tui.clear()
    return book

def play():
    os.nice(19)
    tui = Tui()
    book = get_book(tui)
    while True:
        speed = get_speed(tui)
        if play_ch(speed, book,tui) == 1:
            book = get_book(tui)

PREC = '\033['
KEY_UP    = 'A'
KEY_LEFT  = 'D'
KEY_DOWN  = 'B'
KEY_RIGHT = 'C'
play() 
