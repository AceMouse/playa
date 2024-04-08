from selenium import webdriver 
from selenium.webdriver.firefox.options import Options 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time 
import string
import os
from cleantext import clean
import re
import urllib.parse
from multiprocessing import Pool

print_text = False 
debug = False
def get_dests():
    dests = []
    for dir in os.listdir("output"):
        if os.path.exists(f"output/{dir}/.complete"):
            continue
        dir_fp = f"output/{dir}"
        if not os.path.isdir(dir_fp):
            continue
        dests += [dir]
    return dests

def worker(dest):
    print(dest)
    firefox_options = Options()
    firefox_options.add_argument('--headless')
    driver = webdriver.Firefox(options=firefox_options)

    try:
        folder = f"output/{dest}"
        working = f"{folder}/.working"
        txt_dir = f"{working}/txt"
        if not os.path.isdir(folder):
           os.makedirs(folder)
        if not os.path.isdir(working):
           os.makedirs(working)
        if not os.path.isdir(txt_dir):
           os.makedirs(txt_dir)
        done = False
        while not done:
            url_fp = f"{working}/url.txt"
            tch_fp = f"{working}/tch.txt"
            url = ""
            with open(url_fp,"r") as urlf:
                url = urlf.read()

            if not os.path.isfile(tch_fp):
                sch_fp = f"{working}/sch.txt"
                with open(tch_fp, "w") as chf:
                    with open(sch_fp, "r") as schf:
                        chf.write(str(schf.read()))
            ch = 1
            with open(tch_fp,"r") as chf:
                ch = int(chf.read())


            ch_dir = f"{txt_dir}/ch{ch:04}"
            if not os.path.isdir(ch_dir):
               os.makedirs(ch_dir)


            print(f"getting: {dest}/{ch}", flush=True)
            driver.get(f'about:reader?url={url}')
            time.sleep(2)
            full_txt_fp = f"{txt_dir}/ch{ch:04}.txt"
            text = driver.find_element(By.CLASS_NAME,"moz-reader-content").text
            with open(full_txt_fp,"w") as f:
                f.write(text)

            text = clean_text(text)
            if 'novelfull' in url:
                text = novel_full_clean(text)
            if 'libread' in url:
                text = libread_clean(text)


            sentances = text.split('\n')
            if not re.search('chapter', sentances[0], re.IGNORECASE):
                sentances = [f"chapter {ch}"] + sentances

            blocks = ["\n".join(sentances[i:i+2]) for i in range(0, len(sentances), 2)]
            text = "\n".join(blocks)

            if print_text:
                print(text, flush=True)

            for b, block in enumerate(blocks):
                fp = f"{ch_dir}/b{b:04}.txt"
                with open(fp,"w") as f:
                    f.write(block)

            new_cnt = 0 
            while True:
                driver.get(url)
                time.sleep(0.5)
                ActionChains(driver).key_down(Keys.ARROW_RIGHT).key_up(Keys.ARROW_RIGHT).perform()
                time.sleep(0.5)
                if len(driver.current_url.split('/')) != len(url.split('/')):
                    print(f"No more accessable chapter texts {dest}", flush=True)
                    done = True
                    break
                new = url != driver.current_url
                url = driver.current_url
                if new:
                    with open(url_fp,"w") as urlf:
                        urlf.write(str(url))
                    with open(tch_fp,"w") as chf:
                        chf.write(str(ch+1))
                    break
                else:
                    new_cnt += 1 
                    if new_cnt > 5: 
                        done = True
                        break
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
if __name__ == '__main__':
    dests = get_dests()
    for d in dests:
        worker(d)
    #with Pool(len(dests)) as p:
    #    p.map(worker, dests)
