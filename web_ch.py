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
print_progress = True
def get_dests():
    dests = []
    for dir in os.listdir("output"):
        if os.path.exists(f"output/{dir}/.complete"):
            continue
        dir_fp = f"output/{dir}"
        if not os.path.isdir(dir_fp):
            continue

        folder = f"output/{dir}"
        working = f"{folder}/.working"
        pch_fp = f"{working}/pch.txt"
        tch_fp = f"{working}/tch.txt"
        with open(tch_fp, "r") as chf:
            with open(pch_fp, "r") as pchf:
                dests += [(dir,int(pchf.read())-int(chf.read()))]
    dests = [x for x,_ in sorted(dests, key = lambda x:x[1], reverse = True)]
    return dests

uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.1"
        ]
import random
def worker(dest):
    firefox_options = Options()
    my_user_agent = uas[random.randint(0, len(uas)-1)]
    firefox_options.add_argument(f"--user-agent={my_user_agent}")

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

            if print_progress:
                print(f"getting: {dest}/{ch}", flush=True)
            driver.get(f'about:reader?url={url}')
            time.sleep(2)
            full_txt_fp = f"{txt_dir}/ch{ch:04}.txt"
            text = driver.find_element(By.CLASS_NAME,"moz-reader-content").text
            if len(text) < 100:
                print(f"could not fetch\n text: {text}")
                quit(0)
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
            b = 0 
            for block in blocks:
                block = block.strip()
                if block != "":
                    fp = f"{ch_dir}/b{b:04}.txt"
                    with open(fp,"w") as f:
                        f.write(block)
                    b += 1

            new_cnt = 0 
            while True:
                driver.get(url)
                time.sleep(0.5)
                ActionChains(driver).key_down(Keys.ARROW_RIGHT).key_up(Keys.ARROW_RIGHT).perform()
                time.sleep(0.5)
                if len(driver.current_url.split('/')) != len(url.split('/')):
                    if print_progress:
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
    text = re.sub(r'\\n', '\n', text)  
    text = re.sub(r'\.\.+', '.', text)
    text = re.sub(r'\[|\]', '', text)
    text = re.sub(r'([a-zA-Z])([0-9])', r'\1 \2', text, flags=re.MULTILINE)
    text = re.sub(r'(\d+(\.\d+)?) */ *(\d+(\.\d+)?)', r'\1 out of \3', text)
    text = re.sub(r'^[\W_]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'([\W_ ])lv([\W_ ])', r'\1level\2', text, flags=re.IGNORECASE)
    text = re.sub(r'([\W_ ])e?xp([\W_ ])', r'\1experience\2', text, flags=re.IGNORECASE)
    text = re.sub(r'(->)|(~)', ' to ', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\<|\>','', text)
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

def remove(rtext,text):
    return re.sub(rtext, '', text, flags=re.MULTILINE | re.IGNORECASE)

def libread_clean(text):
    lines = text.split('\n')
    if 'libread' in lines[-1]: 
        text = '\n'.join(lines[:-1])
    text = remove("Dear reader, our website is running thanks to our ads. Please consider supporting us and the translators by disabling your ad blocker", text)
    text = remove("Alternatively, you could also subscribe for only $3 a month at Disabled for now. With the subscription you will enjoy an ad-free experience, and also have access to all the VIP chapters.", text)
    text = remove("libread.com", text)
    text = remove_after(r'Written( and Directed)? by Avans, Published( exclusively)? by W\.e\.b\.n\.o\.v\.e\.l', text)
    text = remove_after(r'For discussion Join Avans Discord server', text)
    return text


def novel_full_clean(text):
    text = re.sub('= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =(.|\n)*', '', text)
    text = remove_after(r'If you find any errors ( Ads popup, ads redirect, broken links, non-standard content, etc.. ), Please let us know < report chapter > so we can fix it as soon as possible',text)
    text = remove_after(r'Tip: You can use left, right, A and D keyboard keys to browse between chapters',text)
    return text 

if __name__ == '__main__':
    dests = get_dests()
    for d in dests:
        time.sleep(10)
        worker(d)
