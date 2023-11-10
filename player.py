import subprocess
import time 
import os
import sys 

def _print(x):
    for _ in range(3):
        try:
            print(x)
        except:
            print("error when printing, retrying!")
            continue
        break

debug = False

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
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def format_time(sec):
    hr = int(sec/(60*60))
    min = int((sec-hr*60*60)/60)
    sec = sec%60
    return f"{hr:02}:{min:02}:{sec:02}"

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'
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
    _print(f"playing {book} ch: {ch}\n")
    while not os.path.isfile(mp3_fp):
        _print(f"{mp3_fp} not found, retrying in 10s")
        time.sleep(10)
    dur = int(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", mp3_fp]).stdout.decode().split('.')[0])+1
    p = Process(target=update_t, args=(working,speed,dur))
    p.start()
    run(["ffplay","-af",f"atempo={speed}", "-nodisp", "-autoexit", "-stats", "-ss", f"{t}s", mp3_fp])
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

play() 
