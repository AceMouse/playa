from selenium import webdriver 
from selenium.webdriver.firefox.options import Options 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from stats import get_chapters_left
import torch
import subprocess
import time 
import os
import sys 
import string
from cleantext import clean
import re
import urllib.parse
import signal

def signal_handler(sig, frame):
    if 'driver' in frame.f_locals:
        frame.f_locals['driver'].quit()
    elif 'driver' in frame.f_globals:
        frame.f_globals['driver'].quit()
    sys.exit(0)

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
syn = True 
debug = False 
print_text = False 
profile = {x:{'success_time':0, 'success_words':0, 'fault_time':0, 'fault_words':0, 'faults':[]} for x in ["gpu", "cpu", "espeak"]}
show_profiling = True
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
    for b,block in enumerate(blocks):
        clear_line(line=2+lines_offset)
        print(f"{b:02}/{len(blocks)}")
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

def merge(folder,dest,fps):
    _print(f"merging: {folder}")
    merge_order=""
    for fp in fps:
        merge_order += f"file '{fp.split('/')[-1]}'\n"
    merge_fp = f"{folder}/merge_order.txt"
    with open(merge_fp,"w") as f:
        f.write(merge_order)
    wav_fp = f"{folder}/merged.wav"
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
exhausted = set()
def get_dest():
    if len(sys.argv) > 1:
        dir = sys.argv[1]
        if dir in exhausted or os.path.exists(f"output/{dir}/.complete"):
            return []
        return dir
    m = 100000 
    md = ""
    for dir in os.listdir("output"):
        if os.path.exists(f"output/{dir}/.complete"):
            continue
        dir_fp = f"output/{dir}/.working"
        if not os.path.isdir(dir_fp):
            continue
        if dir in exhausted:
            continue
        with open(f"{dir_fp}/sch.txt","r") as schf:
            sch = int(schf.read())
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
    


def main():
    global lines_offset
    clear_after_line()
    firefox_options = Options()
    firefox_options.add_argument('--headless')
    driver = webdriver.Firefox(options=firefox_options)
    try:
        new = True
        new_cnt = 0
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
        if len(sys.argv)>2:
            with open(url_fp,"w") as urlf:
                urlf.write(str(sys.argv[2]))
            with open(sch_fp,"w") as schf:
                schf.write(str(sys.argv[3]))
        while True:
            if new_cnt > 2: 
                clear_line(line=1+lines_offset)
                print(f"No more accessable chapters {dest}")
                lines_offset+=1 
                new_cnt = 0 
                exhausted.add(dest)
            new_dest = get_dest()
            if new_dest != dest:
                new = True 
            dest = new_dest
            folder = f"output/{dest}"
            working = f"{folder}/.working"
            ch_dir = f"{working}/ch"
            url_fp = f"{working}/url.txt"
            sch_fp = f"{working}/sch.txt"
            pch_fp = f"{working}/pch.txt"
            t_fp   = f"{working}/t.txt"
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
            driver.get(f'about:reader?url={url}')
            time.sleep(2)
            mp3_fp = f"{folder}/ch{ch:04}.mp3"
            if new and not os.path.isfile(mp3_fp):
                text = driver.find_element(By.CLASS_NAME,"moz-reader-content").text
                text = clean_text(text)
                if 'novelfull' in url:
                    text = novel_full_clean(text)
                if 'libread' in url:
                    text = libread_clean(text)
                text = f"chapter {ch}\n{text}"
                if print_text:
                    print(text)
                if syn:
                    sentances = text.split('\n')
                    blocks = ["\n".join(sentances[i:i+2]) for i in range(0, len(sentances), 2)]
                    model = tts_models[0]
                    clear_line(line=1+lines_offset)
                    print(f"synthing: {dest}/{ch}")
                    fps = synth(blocks,model,ch_dir,pref=f"{ch:04}b")
                    merge(ch_dir, mp3_fp, fps)
                    rm_content(ch_dir)
                new_cnt = 0 
            elif not new:
                new_cnt += 1
            driver.get(url)
            time.sleep(0.5)
            ActionChains(driver).key_down(Keys.ARROW_RIGHT).key_up(Keys.ARROW_RIGHT).perform()
            time.sleep(0.5)
            if len(driver.current_url.split('/')) != len(url.split('/')):
                clear_line(line=1+lines_offset)
                print(f"No more accessable chapters {dest}")
                lines_offset+=1 
                new_cnt = 0 
                exhausted.add(dest)
                continue
            new = url != driver.current_url
            url = driver.current_url
            with open(url_fp,"w") as urlf:
                urlf.write(str(url))
            if new:
                with open(sch_fp,"w") as schf:
                    schf.write(str(ch+1))
    finally:
        driver.quit()

def clean_text(text):
    text = clean(text, lower=False, no_urls=True, replace_with_url="")
    text = expand_contractions(remove_emoji(uncensor_text(misc_clean(text))))
    text = re.sub('If you find any errors \( Ads popup, ads redirect, broken links, non-standard content, etc\. \), Please let us know < report chapter > so we can fix it as soon as possible\.', '', text, flags= re.MULTILINE|re.IGNORECASE)
    return text
def misc_clean(text):
    text = re.sub("'", '', text) #remove 's for now, figure contractions out. 
    text = re.sub('"', '', text)  
#    text = re.sub('\\n', '', text)  
    text = re.sub('\.\.+', '.', text)
    text = re.sub('\[|\]', '', text)
    text = re.sub('([a-zA-Z])([0-9])', r'\1 \2', text, flags=re.MULTILINE)
    text = re.sub('(\d+(\.\d+)?) */ *(\d+(\.\d+)?)', r'\1 out of \3', text)
    text = re.sub('^[\W_]+$', '', text, flags=re.MULTILINE)
    text = re.sub('([\W_ ])lv([\W_ ])', r'\1level\2', text, flags=re.IGNORECASE)
    text = re.sub('([\W_ ])e?xp([\W_ ])', r'\1experience\2', text, flags=re.IGNORECASE)
    text = re.sub('(->)|(~)', ' to ', text)
    text = re.sub(' +', ' ', text)
    return text 

def uncensor_text(text):
    text = re.sub('(m|M) ?\* ?th ?\* ?rf ?\* ?ck ?\* ?r', r'\1otherfucker', text)
    text = re.sub('(b|B) ?\* ?itch', r'\1itch', text)
    text = re.sub('(g|G) ?\* ?dd ?\* ?mn ?\* ?d', r'\1oddamned', text)
    text = re.sub('(g|G) ?\* ?dd ?\* ?mm ?\* ?t', r'\1oddammit', text)
    text = re.sub('(f|F) ?\* ?ck ?\* ?ng', r'\1ucking', text)
    text = re.sub('(f|F) ?\* ?ck', r'\1uck', text)
    text = re.sub('(b|B) ?\* ?llsh ?\* ?t', r'\1ullshit', text)
    return text 

import emoji 
def remove_emoji(text):
    return emoji.replace_emoji(text, replace='')

#from pycontractions import Contractions
def expand_contractions(text):
    return text

def remove_after(rtext,text):
    return re.sub(rtext + r'(.|\n)*', '', text, flags=re.MULTILINE | re.IGNORECASE)

def libread_clean(text):
    lines = text.split('\n')
    if 'libread' in lines[-1]: 
        text = '\n'.join(lines[:-1])
    text = remove_after(r'Written( and Directed)? by Avans, Published( exclusively)? by W\.e\.b\.n\.o\.v\.e\.l', text)
    text = remove_after(r'For discussion Join Avans Discord server', text)
    return text


def novel_full_clean(text):
    text = re.sub('= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =(.|\n)*', '', text)
    text = remove_after(r'If you find any errors ( Ads popup, ads redirect, broken links, non-standard content, etc.. ), Please let us know < report chapter > so we can fix it as soon as possible',text)
    text = remove_after(r'Tip: You can use left, right, A and D keyboard keys to browse between chapters',text)
    return text 



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



