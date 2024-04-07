import subprocess
import time 
import os
import sys 
from pytimedinput import timedKey, timedKeyOrNumber
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
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def format_time(in_sec):
    hr = int(in_sec/(60*60))
    min = int((in_sec-hr*60*60)/60)
    sec = int(in_sec%60)
    msec = int((in_sec*1000)%1000)
    return f"{hr:02}:{min:02}:{sec:02}:{msec:03}"

def update_t(folder,speed,dur):
    t = 0
    len = 20
    dt = 1/speed 
    while True:
        with open(f"{folder}/t.txt","r") as tf:
            t = float(tf.read())
        with open(f"{folder}/t.txt","w") as tf:
            tf.write(str(t+speed*dt))
        fill = int((t*len)/dur)
        empty = 20-fill 
        clear(lines=2)
        print(f"{format_time(t)} [{'#'*fill}{'.'*empty}] {format_time(dur)}")
        time.sleep(dt)

def get_fp(folder, ch):
    return f"{folder}/ch{ch:04}.mp3"

def get_duration(mp3_fp):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", mp3_fp]).stdout.decode().split('.')[0])+1

def start_mp3(mp3_fp, speed, t):
    return popen(["ffplay","-af",f"atempo={speed}", "-nodisp", "-autoexit", "-stats", "-ss", f"{t}s", mp3_fp])

def pause(processes, unpause = False):
    s = signal.SIGCONT if unpause else signal.SIGSTOP
    for p in processes:
        os.kill(p.pid, s)

def unpause(processes):
    return pause(processes, unpause = True)


def play_ch(folder,speed,book):
    ch = 0
    t = 0
    working = f"{folder}/.working"
    with open(f"{working}/pch.txt","r") as chf:
        ch = int(chf.read())
    with open(f"{working}/t.txt","r") as tf:
        t = max(float(tf.read())-5,0)
    with open(f"{working}/t.txt","w") as tf:
        tf.write(str(t))
    mp3_fp = get_fp(folder, ch)
    clear()
    print(f"playing {book} ch: {ch} ({speed}x)\n")
    w = 1 
    while not os.path.isfile(mp3_fp):
        clear()
        print(f"{mp3_fp} not found, retrying in 10s ({w})")
        w += 1
        x, timedOut = timedKey(timeout=10, resetOnInput = False, allowCharacters=f"t", pollRate = pollRate)
        if timedOut:
            continue
        if x == 't':
            return 1 
    dur = get_duration(mp3_fp) 
    ui_p = Process(target=update_t, args=(working,speed,dur))
    ui_p.start()
    player_p = start_mp3(mp3_fp, speed, t)
    unpaused = True
    while True:
        with open(f"{working}/t.txt","r") as tf:
            z = tf.read()
            if z == "":
                z = 0 
            t = float(z)

        if dur-t <= 0:
            break

        x, timedOut = timedKey(timeout=-1 if not unpaused else int((dur-t)/speed), resetOnInput = False, allowCharacters=f" pt{KEY_LEFT}{KEY_RIGHT}{KEY_UP}{KEY_DOWN}wsjk",pollRate = pollRate)
        if timedOut:
            break
        #print("\n")
        clear(lines=3)
        if x in ' p':
            unpaused = not unpaused
            pause([player_p, ui_p], unpause = unpaused)
        if x == 't':
            if not unpaused:
                unpause([player_p, ui_p])
            player_p.terminate()
            ui_p.terminate()
            return 1 
        if x in f"{KEY_LEFT}{KEY_RIGHT}jk":
            with open(f"{working}/t.txt","r") as tf:
                t = float(tf.read())
            with open(f"{working}/t.txt","w") as tf:
                if x in f"{KEY_LEFT}j": 
                    if t < 2 and os.path.isfile(get_fp(folder, ch-1)):
                        ch -= 1
                        mp3_fp = get_fp(folder, ch)
                        dur = get_duration(mp3_fp)
                        t += dur 
                    t = max(t-15,0)
                    clear()
                    print(f"playing {book} ch: {ch} ({speed}x)\n")
                else: 
                    t = min(t+15,dur)
                tf.write(str(t))
            player_p.terminate()
            player_p = start_mp3(mp3_fp, speed, t)
            ui_p.terminate()
            ui_p = Process(target=update_t, args=(working,speed,dur))
            ui_p.start()
            if not unpaused:
                pause([player_p])
        if x in f"{KEY_UP}{KEY_DOWN}ws":
            _print(f"key = {x}")
            player_p.terminate()
            ui_p.terminate()
            with open(f"{working}/t.txt","r") as tf:
                t = float(tf.read())
            if x in f"{KEY_DOWN}s":
                speed = max(speed-0.25, 0.25)
            else:
                speed = speed+0.25
            with open(dsfp, "w") as dsf:
                dsf.write(str(speed))
            clear()
            print(f"playing {book} ch: {ch} ({speed}x)\n")
            player_p = start_mp3(mp3_fp, speed, t)
            ui_p = Process(target=update_t, args=(working,speed,dur))
            ui_p.start()
            if not unpaused:
                pause([player_p, ui_p])

    player_p.wait()
    ui_p.terminate()
    with open(f"{working}/t.txt","w") as tf:
        tf.write("0")
    with open(f"{working}/pch.txt","w") as chf:
        chf.write(str(ch+1))
    return 0 

dbfp = "output/.def_book"
dsfp = "output/.def_speed"
def get_input():
    default_speed_existed = True
    if not os.path.isfile(dsfp):
        default_speed_existed = False 
        with open(dsfp, "w") as dsf:
            dsf.write("1")
    book = "" 
    clear()
    if len(sys.argv) <= 1:
        books = []
        for dir in os.listdir("output"):
            dir_fp = f"output/{dir}"
            if not os.path.isdir(dir_fp):
                continue
            books += [dir] 
        if not os.path.isfile(dbfp):
            with open(dbfp, "w") as dbf:
                dbf.write(books[0])

        default_book = ""
        with open(dbfp, "r") as dbf:
            default_book = str(dbf.read())
        book = default_book
        arrow_number = books.index(default_book)
        while True:
            clear()
            print(f"Choose a book (1-{len(books)}):")
            for i,b in enumerate(books):
                if i == arrow_number:
                    print(f"->{i+1} {b}")
                else: 
                    print(f"  {i+1} {b}")
            i, _ = timedKeyOrNumber("", timeout = -1, allowCharacters = f"tws", allowNegative = False, allowFloat = False, pollRate = pollRate)
            if i == 't':
                quit(0)
            if i == "w":
                arrow_number = max(0, arrow_number-1)
                book = books[arrow_number]
                continue
            if i == "s":
                arrow_number = min(len(books)-1, arrow_number+1)
                book = books[arrow_number]
                continue
            if i != None:
                if i == 0 or i > len(books):
                    continue
                book = books[i-1]
            with open(dbfp, "w") as dbf:
                dbf.write(book)
            break
        clear()
    else:
        book = sys.argv[1]

    folder = f"output/{book}"
    default_speed = 1   
    with open(dsfp, "r") as dsf:
        default_speed = float(dsf.read())
    speed = default_speed
    if not default_speed_existed:
        i, _ = timedKeyOrNumber(f"Choose a speed ({default_speed}):\n", timeout = -1, allowCharacters = "t", allowNegative = False, pollRate = pollRate)
        clear()
        if i == 't':
            return get_input()
        if i != None:
            speed = i
        with open(dsfp, "w") as dsf:
            dsf.write(str(speed))

    if len(sys.argv) > 2:
        with open(f"{folder}/.working/pch.txt","w") as chf:
            chf.write(sys.argv[2])
        with open(f"{folder}/.working/t.txt","w") as tf:
            tf.write("0")
    if len(sys.argv) > 3:
        with open(f"{folder}/.working/t.txt","w") as tf:
            tf.write(sys.argv[3])
    return (folder,speed,book)

def play():
    os.nice(19)
    folder, speed, book = get_input()
    print()
    while True:
        if play_ch(folder, speed, book) == 1:
            folder, speed, book = get_input()

def clear(lines=1):
    if not debug: 
        print(f"\033[{lines};1H\033[0J", end="")

LINE_UP = '' if debug else '\033[1A' 
LINE_CLEAR = '' if debug else '\x1b[2K'
ARROW_PRECURSOR_1 = '\033'
ARROW_PRECURSOR_2 = '['
KEY_UP    = 'A'
KEY_LEFT  = 'D'
KEY_DOWN  = 'B'
KEY_RIGHT = 'C'
play() 
