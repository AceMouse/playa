import subprocess
import time 
import os
import sys 
from pytimedinput import timedKey

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
    if 'p' in frame.f_locals:
        frame.f_locals['p'].terminate()
    elif 'p' in frame.f_globals:
        frame.f_globals['p'].terminate()
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
    mp3_fp = f"{folder}/ch{ch:04}.mp3"
    clear()
    print(f"playing {book} ch: {ch}\n")
    w = 1 
    while not os.path.isfile(mp3_fp):
        clear()
        print(f"{mp3_fp} not found, retrying in 10s ({w})")
        w += 1
        x, timedOut = timedKey(timeout=10, allowCharacters=f"t")
        if timedOut:
            continue
        if x == 't':
            return 1 
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", mp3_fp]).stdout.decode().split('.')[0])+1

    p = Process(target=update_t, args=(working,speed,dur))
    p.start()
    player_p = popen(["ffplay","-af",f"atempo={speed}", "-nodisp", "-autoexit", "-stats", "-ss", f"{t}s", mp3_fp])
    paused = False 
    while True:
        while True:
            try:
                with open(f"{working}/t.txt","r") as tf:
                    z = tf.read()
                    #print(f"\n\nt: '{z}'\n\n")
                    t = float(z)
                    break
            except Exception as e:
                print(e)
                continue

        if dur-t <= 0:
            break

        x, timedOut = timedKey(timeout=-1 if paused else int((dur-t)/speed), allowCharacters=f" pt{KEY_LEFT}{KEY_RIGHT}jk")
        print()
        print()
        if timedOut:
            break
        clear(lines=3)
        if x in ' p':
            if paused:
                os.kill(player_p.pid, signal.SIGCONT)
                os.kill(p.pid, signal.SIGCONT)
            else:
                os.kill(player_p.pid, signal.SIGSTOP)
                os.kill(p.pid, signal.SIGSTOP)
            paused = not paused
        if x == 't':
            if paused:
                os.kill(player_p.pid, signal.SIGCONT)
                os.kill(p.pid, signal.SIGCONT)
            player_p.terminate()
            p.terminate()
            return 1 
        if x in [KEY_LEFT,KEY_RIGHT,"j","k"]:
            with open(f"{working}/t.txt","r") as tf:
                t = float(tf.read())
            with open(f"{working}/t.txt","w") as tf:
                t = max(t-15,0)if x in [KEY_LEFT,"j"] else min(t+15,dur)
                tf.write(str(t))
            player_p.terminate()
            player_p = popen(["ffplay","-af",f"atempo={speed}", "-nodisp", "-autoexit", "-stats", "-ss", f"{t}s", mp3_fp])
            if paused:
                os.kill(player_p.pid, signal.SIGSTOP)

    player_p.wait()
    p.terminate()
    with open(f"{working}/t.txt","w") as tf:
        tf.write("0")
    with open(f"{working}/pch.txt","w") as chf:
        chf.write(str(ch+1))
    return 0 

def get_input():
    dbfp = "output/.def_book"
    dsfp = "output/.def_speed"
    if not os.path.isfile(dbfp):
        with open(dbfp, "w") as dbf:
            dbf.write("0")
    if not os.path.isfile(dsfp):
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

        default_book = 0  
        with open(dbfp, "r") as dbf:
            default_book = int(dbf.read())
        book = books[default_book]
        print(f"Choose a book (1-{len(books)}):")
        for i,b in enumerate(books):
            if i == default_book:
                print(f"->{i+1} {b}")
            else: 
                print(f"  {i+1} {b}")
        i = input()
        if i == 't':
            quit(0)

        if i.isdigit():
            with open(dbfp, "w") as dbf:
                dbf.write(str(int(i)-1))
            book = books[int(i)-1]
        clear()
    else:
        book = sys.argv[1]

    folder = f"output/{book}"
    default_speed = 1   
    with open(dsfp, "r") as dsf:
        default_speed = float(dsf.read())
    speed = default_speed
    i = input(f"Choose a speed ({default_speed}):\n")
    clear()
    if i == 't':
        quit(0)
    if i.replace('.','',1).isdigit(): 
        speed = float(i)
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
