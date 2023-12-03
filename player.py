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
    d = {'args': cmd,'capture_output':True} if debug else {'args': cmd,'capture_output':True}
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

def format_time(sec):
    hr = int(sec/(60*60))
    min = int((sec-hr*60*60)/60)
    sec = sec%60
    return f"{hr:02}:{min:02}:{sec:02}"

def update_t(folder,speed,dur):
    t = 0
    len = 20
    while True:
        with open(f"{folder}/t.txt","r") as tf:
            t = int(tf.read())
        with open(f"{folder}/t.txt","w") as tf:
            tf.write(str(t+speed))
        fill = int((t*len)/dur)
        empty = 20-fill 
        print(LINE_UP, end=LINE_CLEAR)
        print(f"{format_time(t)} [{'#'*fill}{'.'*empty}] {format_time(dur)}")
        time.sleep(1)

        
def play_ch(folder,speed,book):
    ch = 0
    t = 0
    working = f"{folder}/.working"
    with open(f"{working}/pch.txt","r") as chf:
        ch = int(chf.read())
    with open(f"{working}/t.txt","r") as tf:
        t = max(int(tf.read())-5,0)
    with open(f"{working}/t.txt","w") as tf:
        tf.write(str(t))
    mp3_fp = f"{folder}/ch{ch:04}.mp3"
    print(LINE_UP, end=LINE_CLEAR)
    print(LINE_UP, end=LINE_CLEAR)
    print(f"playing {book} ch: {ch}\n")
    w = 1 
    while not os.path.isfile(mp3_fp):
        print(LINE_UP, end=LINE_CLEAR)
        print(LINE_UP, end=LINE_CLEAR)
        print(f"{mp3_fp} not found, retrying in 10s ({w})")
        w += 1
        x, timedOut = timedKey(timeout=10, allowCharacters=f"t")
        if timedOut:
            continue
        if x == 't':
            quit(0)
    dur = int(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", mp3_fp]).stdout.decode().split('.')[0])+1

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
                    t = int(z)
                    break
            except Exception as e:
                print(e)
                continue

        if dur-t <= 0:
            break

        x, timedOut = timedKey(timeout=-1 if paused else int((dur-t)/speed), allowCharacters=f" pt{KEY_LEFT}{KEY_RIGHT}")
        if timedOut:
            break

#        print("key:", x)
        if x in ' p':
            if paused:
                os.kill(player_p.pid, signal.SIGCONT)
                os.kill(p.pid, signal.SIGCONT)
            else:
                os.kill(player_p.pid, signal.SIGSTOP)
                os.kill(p.pid, signal.SIGSTOP)
            paused = not paused
        if x == 't':
            player_p.terminate()
            p.terminate()
            quit(0)
        if x in [KEY_LEFT,KEY_RIGHT]:
            with open(f"{working}/t.txt","r") as tf:
                t = int(tf.read())
            with open(f"{working}/t.txt","w") as tf:
                t = max(t-15,0)if x == KEY_LEFT else min(t+15,dur)
                tf.write(str(t))
            player_p.terminate()
            player_p = popen(["ffplay","-af",f"atempo={speed}", "-nodisp", "-autoexit", "-stats", "-ss", f"{t}s", mp3_fp])
            if paused:
                os.kill(player_p.pid, signal.SIGSTOP)

    player_p.wait()
    p.terminate()
    with open(f"{working}/t.txt","w") as tf:
        tf.write(str(0))
    with open(f"{working}/pch.txt","w") as chf:
        chf.write(str(ch+1))

def play():
    book = "" 
    if len(sys.argv) <= 1:
        books = []
        for dir in os.listdir("output"):
            dir_fp = f"output/{dir}"
            if not os.path.isdir(dir_fp):
                continue
            books += [dir] 
        print(f"chose a book (1-{len(books)}):")
        for i,b in enumerate(books):
            print(f"  {i+1} {b}")
        book = books[int(input())-1]
        for _ in range(len(books)+2):
            print(LINE_UP, end=LINE_CLEAR)
    else:
        book = sys.argv[1]

    folder = f"output/{book}"
    speed = int(input("choose a speed:\n"))

    if len(sys.argv) > 2:
        with open(f"{folder}/.working/pch.txt","w") as chf:
            chf.write(sys.argv[2])
        with open(f"{folder}/.working/t.txt","w") as tf:
            tf.write("0")
    if len(sys.argv) > 3:
        with open(f"{folder}/.working/t.txt","w") as tf:
            tf.write(sys.argv[3])
    while True:
        play_ch(folder, speed, book)

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'
ARROW_PRECURSOR_1 = '\033'
ARROW_PRECURSOR_2 = '['
KEY_UP    = 'A'
KEY_LEFT  = 'D'
KEY_DOWN  = 'B'
KEY_RIGHT = 'C'
play() 
