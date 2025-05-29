from selenium import webdriver 
from selenium.webdriver.firefox.options import Options 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

import time 
import os
from cleantext import clean
import re
from lib.pytui.pytui import Tui

print_text = False 
debug = False
print_progress = True


def get_dests():
    dests = []
    for dir in os.listdir("output"):
        if dir == ".logging" or os.path.exists(f"output/{dir}/.complete"):
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

os.makedirs("output/.logging", exist_ok=True)
logfile = open('output/.logging/getter.log', 'w')
import random
import logging
import traceback

url_logger = logging.getLogger('urllib3.connectionpool')
url_logger.setLevel(logging.CRITICAL)
sel_logger = logging.getLogger('selenium.webdriver.common.selenium_manager')
sel_logger.setLevel(logging.CRITICAL)
fh = logging.FileHandler('output/.logging/getter.log')
fh.setLevel(logging.DEBUG)
sel_logger.addHandler(fh)
url_logger.addHandler(fh)
def worker(dest, tui):
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
            full_txt_fp = f"{txt_dir}/ch{ch:04}.txt"
            if url != "":
                if print_progress:
                    tui.place_text(f"Getting: {dest}/{ch}")
                driver.get(f'about:reader?url={url}')
                time.sleep(2)
                text = driver.find_element(By.CLASS_NAME,"moz-reader-content").text
                if len(text) < 100:
                    print(f"Could not fetch {dest}/{ch}. Fetched text: {text}", file=logfile)
                    os.remove(ch_dir)
                    done = True
                    break
                with open(full_txt_fp,"w") as f:
                    f.write(text)
            else:
                if not os.path.isfile(full_txt_fp):
                    done = True
                    break
                with open(full_txt_fp,"r") as f:
                    text = f.read()
            text_to_blocks(tui, dest, text, ch, ch_dir, url)
            if url == "":
                with open(tch_fp,"w") as chf:
                    chf.write(str(ch+1))
            else:
                new_cnt = 0 
                while True:
                    driver.get(url)
                    time.sleep(0.5)
                    url = driver.current_url
                    ActionChains(driver).key_down(Keys.ARROW_RIGHT).key_up(Keys.ARROW_RIGHT).perform()
                    time.sleep(0.5)
                    c_url = driver.current_url
                    if len(c_url.split('/')) != len(url.split('/')):
                        if print_progress:
                            tui.place_text(f"No more accessable chapter texts {dest}")
                        done = True
                        break
                    new = url != c_url
                    url = c_url
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
        driver.quit()
        return True
    except Exception as e:
        traceback.print_exc()
    finally:
        driver.quit()
        return True

def text_to_blocks(tui, dest, text, ch, ch_dir, url):
    folder = f"output/{dest}"
    working = f"{folder}/.working"
    txt_dir = f"{working}/txt"
    if not os.path.isdir(folder):
        os.makedirs(folder)
    if not os.path.isdir(working):
        os.makedirs(working)
    if not os.path.isdir(txt_dir):
        os.makedirs(txt_dir)
    ch_dir = f"{txt_dir}/ch{ch:04}"
    if not os.path.isdir(ch_dir):
        os.makedirs(ch_dir)
    else:
        for dir in os.listdir(ch_dir):
            if re.search(r"b\d{4}.txt", dir):
                os.remove(f"{ch_dir}/{dir}")
    text = clean_text(text)
    if 'novelfull' in url:
        text = novel_full_clean(text)
    if 'libread' in url or 'freewebnovel.noveleast' in url:
        text = libread_clean(text)

    sentances = text.split('\n')
    if not re.search('chapter', sentances[0], re.IGNORECASE):
        sentances = [f"chapter {ch}"] + sentances

    blocks = [" ".join(sentances[i:i+2]).strip() for i in range(0, len(sentances), 2)]
    text = "\n".join(blocks)


    if print_text:
        tui.place_text(text)
    b = 0 
    for block in blocks:
        block = block.strip()
        if block != "":
            fp = f"{ch_dir}/b{b:04}.txt"
            with open(fp,"w") as f:
                f.write(block)
            b += 1

def clean_text(text):
    text = clean(text, lower=False, no_urls=True, replace_with_url="", to_ascii=True)
    text = expand_contractions(remove_emoji(uncensor_text(misc_clean(text))))
    text = remove_after(r'If you find any errors \( Ads popup, ads redirect, broken links, non-standard content, etc\. \), Please let us know < report chapter > so we can fix it as soon as possible\.', text)
    text = remove_after(r"Tip: You can use left, right, A and D keyboard keys to browse between chapters\.", text)
    text = remove_after(r"Tap the screen to use reading tools", text)
    return text

def misc_clean(text):
    text = re.sub("'", '', text) #remove 's for now, figure contractions out. 
    text = re.sub('"', '', text)  
    text = re.sub(r'\\n', '\n', text)  
    text = re.sub(r'\.+', '.', text)
    text = re.sub(r'\?+', '?', text)
    text = re.sub(r'\[|\]', '', text)
    text = re.sub(r'\(|\)', '', text)
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
    text = re.sub(r'(m|M) ?\* ?th ?\* ?rf ?\* ?ck ?\* ?r', r'\1otherfucker', text)
    text = re.sub(r'(b|B) ?\* ?itch', r'\1itch', text)
    text = re.sub(r'(g|G) ?\* ?dd ?\* ?mn ?\* ?d', r'\1oddamned', text)
    text = re.sub(r'(g|G) ?\* ?dd ?\* ?mm ?\* ?t', r'\1oddammit', text)
    text = re.sub(r'(f|F) ?\* ?ck ?\* ?ng', r'\1ucking', text)
    text = re.sub(r'(f|F) ?\* ?ck', r'\1uck', text)
    text = re.sub(r'(b|B) ?\* ?llsh ?\* ?t', r'\1ullshit', text)
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
    while lines[-1].strip() == "":
        lines = lines[:-1]
    if 'libread' in lines[-1] or 'free' in lines[-1] or 'novel' in lines[-1] or 'web' in lines[-1]: 
        text = '\n'.join(lines[:-1])


    text = remove("Translated by NEET", text)
    text = remove("Edited by (Ilesyt)?(, )?(Oberon)?", text)
    text = remove("Dear reader, our website is running thanks to our ads.", text)
    text = remove("Please consider supporting us and the translators by disabling your ad blocker", text)
    text = remove("Currently, 55% of our readers have turned their ad-block on.", text)
    text = remove(r"Alternatively, (if you dont like ads, )?you could also subscribe for only \$3 a month at Disabled for now.", text)
    text = remove(r"Alternatively, (if you dont like ads, )?you could also subscribe for only \$3 for 30 days.", text)
    text = remove("With the subscription you will enjoy an ad-free experience, and also have access to all the VIP chapters.", text)
    text = remove("libread.com", text)
    text = remove_after(r'Written( and Directed)? by Avans, Published( exclusively)? by W\.e\.b\.n\.o\.v\.e\.l', text)
    text = remove_after(r'For discussion Join Avans Discord server', text)
    return text


def novel_full_clean(text):
    text = re.sub('= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =(.|\n)*', '', text)
    text = remove_after(r'If you find any errors ( Ads popup, ads redirect, broken links, non-standard content, etc.. ), Please let us know < report chapter > so we can fix it as soon as possible',text)
    text = remove_after(r'Tip: You can use left, right, A and D keyboard keys to browse between chapters',text)
    return text 
def main(tui=Tui()):
    tui.clear_box()
    dests = get_dests()
    for d in dests:
        while not worker(d,tui):
            time.sleep(10)
    tui.place_text("Done getting!")

if __name__ == '__main__':
    main()
