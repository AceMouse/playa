from stats import get_chapters_left
import torch
import subprocess
import time 
import os
import signal
import re

debug = False 
print_text = False 
show_profiling = True

def signal_handler(sig, frame):
    if 'driver' in frame.f_locals:
        frame.f_locals['driver'].quit()
    elif 'driver' in frame.f_globals:
        frame.f_globals['driver'].quit()
    clear_after_line(line=2+lines_offset)
    print("Interrupted")
    print("Chapters ready for reading:")
    x = get_chapters_left()
    l = len(str(max(x, key=lambda item: item[0])[0]))
    for c,_,_,dir in x:
        print(f"  {c:>{l}}: {dir} ")
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
def _print(x):
    if debug:
        for _ in range(3):
            try:
                print(x)
            except:
                print("error when printing, retrying!")
                continue
            break

def print_models():
    for x in TTS().list_models():
        if 'en' in x:
            _print(x)
profile = {x:{'success_time':0, 'success_words':0, 'fault_time':0, 'fault_words':0, 'faults':[]} for x in ["gpu", "cpu", "espeak"]}
prog_aliases = {"tts":"tts", "espeak":"espeak", "ffmpeg":"ffmpeg", "ffplay":"ffplay", "ffprobe":"ffprobe"}
for k in prog_aliases.keys():
    alias = f".{k}_alias"
    if os.path.isfile(alias):
        with open(alias, "r") as a:
            prog_aliases[k] = a.read().strip()

def run(cmd):
    d = {'args': cmd} if debug else {'args': cmd,'stdout':subprocess.DEVNULL,'stderr':subprocess.DEVNULL}
    for _ in range(3):
        try:
            p = subprocess.Popen(**d)
            p.wait()
            return p.returncode
        except TypeError:
            time.sleep(2)

def show_profile():
    if show_profiling:
        clear_after_line(line=3+lines_offset)
        for k,v in profile.items():
            s = v["success_time"]+v["fault_time"]
            wps = v["success_words"]/s if s != 0 else 0 
            print(f'{k}: {wps:.2f} wps')
            for k, v in v.items():
                print(f"\t{k}: {v}")


def tts(text, cuda, fp, model):
    t = time.time()
    res = run([prog_aliases["tts"], "--text", text, "--use_cuda",str(cuda),"--model_name", model,"--out_path",fp])
    t = time.time()-t 
    pkey = "gpu" if cuda else "cpu"
    ppref = "success" if res == 0 else "fault"
    profile[pkey][f"{ppref}_time"] += t 
    profile[pkey][f"{ppref}_words"] += text.count(' ') +1 
    if res != 0:
        profile[pkey]["faults"] += [(text,res)]
    show_profile()
    return res  

def espeak(text, fp): 
    t = time.time()
    res = run([prog_aliases["espeak"], text, "-w",fp]) 
    t = time.time()-t 
    pkey = "espeak"
    ppref = "success" if res == 0 else "fault"
    profile[pkey][f"{ppref}_time"] += t 
    profile[pkey][f"{ppref}_words"] += text.count(' ') +1 
    if res != 0:
        profile[pkey]["faults"] += [(text,res)]
    show_profile()
    return res  


def synth(blocks,model,folder,pref="b",split=True):
    fps = []
    if not os.path.exists(folder):
       os.makedirs(folder)
       _print(f"made folder {folder}")
    cuda = torch.cuda.is_available()
    show_profile()
    for b,block in enumerate(blocks):
        clear_line(line=2+lines_offset)
        print(f"{b:02}/{len(blocks)-1}")
        fp = f"{folder}/{pref}{b:04}.wav"
        if (os.path.isfile(fp)):
            fps += [fp]
            continue
        _print(f"synthing: {pref}{b:04}.wav")
        if cuda:
            torch.cuda.empty_cache()
            _print("try on gpu")
            if tts(block,cuda,fp,model) == 0:
                _print("success")
                fps += [fp]
                continue
        _print("try on cpu")
        if tts(block,False,fp,model) == 0:
            _print("success")
            fps += [fp]
            continue
        if split:
            splits = block.split('.')
            if len(splits) > 1:
                _print("trying split:")
                synth(splits,b,model,pref=f"{pref}{b:04}s",split=False)
        else:
            _print("fallback to espeak")
            espeak(block,fp)
            fps += [fp]
    return fps 

def concat(merge_fp, wav_fp):
    return run([prog_aliases["ffmpeg"], "-f", "concat","-safe","0","-y", "-i", merge_fp, wav_fp])

def to_mp3(wav_fp,out,highpass=200, lowpass=3000, debug=False):
    return run([prog_aliases["ffmpeg"],"-y", "-i", wav_fp, "-acodec", "mp3","-filter:a", f"highpass=f={highpass}, lowpass=f={lowpass}", out])

def get_duration(wav_fp):
    cmd = [prog_aliases["ffprobe"], "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", wav_fp]
    d = {'args': cmd,'capture_output':True} 
    s = subprocess.run(**d).stdout.decode()
    return float(s)

def merge(working,dest,fps, ch):
    ch_fp = f"{working}/ch"
    _print(f"merging: {ch_fp}")
    merge_fp = f"{ch_fp}/merge_order.txt"
    with open(f"{working}/txt/ch{ch:04}/timestamps.txt", "w") as ts:
        with open(merge_fp,"w") as f:
            for fp in fps:
                dur = get_duration(fp)
                ts.write(f"{dur}\n")
                f.write(f"file '{fp.split('/')[-1]}'\n")
    wav_fp = f"{ch_fp}/merged.wav"
    concat(merge_fp, wav_fp)
    to_mp3(wav_fp,dest)

tts_models = [ 
    "tts_models/en/ljspeech/vits",
    "tts_models/en/jenny/jenny",
    "tts_models/en/ek1/tacotron2",
    "tts_models/en/ljspeech/tacotron2-DDC",
    "tts_models/en/ljspeech/tacotron2-DDC_ph",
    "tts_models/en/ljspeech/tacotron2-DCA",
    "tts_models/en/sam/tacotron-DDC",
    "tts_models/en/ljspeech/glow-tts",
    "tts_models/en/ljspeech/speedy-speech",
    "tts_models/en/ljspeech/vits--neon",
    "tts_models/en/ljspeech/fast_pitch",
    "tts_models/en/ljspeech/overflow",
    "tts_models/en/ljspeech/neural_hmm",
    "tts_models/en/vctk/vits",
    "tts_models/en/vctk/fast_pitch",
    "tts_models/en/blizzard2013/capacitron-t2-c50",
    "tts_models/en/blizzard2013/capacitron-t2-c150_v2",
    "tts_models/en/multi-dataset/tortoise-v2"
]
def get_dest():
    m = 100000 
    md = ""
    for dir in os.listdir("output"):
        if os.path.exists(f"output/{dir}/.complete"):
            continue
        dir_fp = f"output/{dir}/.working"
        if not os.path.isdir(dir_fp):
            continue
        sch = 0 
        with open(f"{dir_fp}/sch.txt","r") as schf:
            sch = int(schf.read())
        with open(f"{dir_fp}/tch.txt","r") as tchf:
            tch = int(tchf.read())
            if tch-sch <= -1:
                continue
        with open(f"{dir_fp}/pch.txt","r") as pchf:
            pch = int(pchf.read())
            if sch-pch<m:
                m = sch-pch 
                md = dir 
    if m == 100000:
        clear_after_line(line=1+lines_offset)
        print("Nothing to synth")
        print("Chapters ready for reading:")
        x = get_chapters_left()
        l = len(str(max(x, key=lambda item: item[0])[0]))
        for c,_,_,dir in x:
            print(f"  {c:>{l}}: {dir} ")
        exit(0)
    return md
    
def get_blocks(dest, ch):
    ch_fp = f"output/{dest}/.working/txt/ch{ch:04}"
    print(ch_fp)
    if not os.path.isdir(ch_fp):
        print("no blocks")
        return []
    blocks = []
    dirs = os.listdir(ch_fp)
    dirs = sorted(dirs)
    print(dirs)
    for dir in dirs:
        if re.search(r"b\d{4}.txt", dir):
            with open(f"{ch_fp}/{dir}", "r") as b:
                blocks += [str(b.read())]
    print("blocks: ")
    [print(b) for b in blocks]
    return blocks

def main():
    global lines_offset
    clear_after_line()
    dest = get_dest()
    folder = f"output/{dest}"
    working = f"{folder}/.working"
    ch_dir = f"{working}/ch"
    url_fp = f"{working}/url.txt"
    sch_fp = f"{working}/sch.txt"
    pch_fp = f"{working}/pch.txt"
    t_fp   = f"{working}/t.txt"
    if not os.path.isdir(folder):
       os.makedirs(folder)
    if not os.path.isdir(working):
       os.makedirs(working)
    if not os.path.isdir(ch_dir):
       os.makedirs(ch_dir)
    ch = 0 
    while True:
        dest = get_dest()
        folder = f"output/{dest}"
        working = f"{folder}/.working"
        ch_dir = f"{working}/ch"
        url_fp = f"{working}/url.txt"
        sch_fp = f"{working}/sch.txt"
        pch_fp = f"{working}/pch.txt"
        t_fp   = f"{working}/t.txt"
        txt_fp   = f"{working}/txt"
        with open(url_fp,"r") as urlf:
            url = urlf.read()
        with open(sch_fp,"r") as chf:
            ch = int(chf.read())
        if not os.path.isfile(pch_fp):
            with open(pch_fp, "w") as pchf:
                pchf.write(str(ch))
        if not os.path.isfile(t_fp):
            with open(t_fp, "w") as tf:
                tf.write("0")
        mp3_fp = f"{folder}/ch{ch:04}.mp3"
        if not os.path.isfile(mp3_fp):
            blocks = get_blocks(dest, ch) 
            model = tts_models[0]
            clear_after_line(line=1+lines_offset)
            print(f"synthing: {dest}/{ch}")
            if len(blocks) < 2:
                print("no blocks")
                quit(0)
            fps = synth(blocks,model,ch_dir,pref=f"{ch:04}b")
            merge(working, mp3_fp, fps, ch)
            rm_content(ch_dir)

        with open(sch_fp,"w") as schf:
            schf.write(str(ch+1))

import shutil
def rm_content(folder):
    shutil.rmtree(folder)

def clear_line(line=1):
    if not debug: 
        print(f"\033[{line};1H\033[0K", end="", flush=True)
    
def clear_after_line(line=1):
    if not debug: 
        print(f"\033[{line};1H\033[0J", end="", flush=True)
LINE_UP = '' if debug else '\033[1A' 
LINE_CLEAR = '' if debug else '\x1b[2K'
lines_offset=0
main()



