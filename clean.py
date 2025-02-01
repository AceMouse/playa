import sys
import os
import shutil

def clean():
    if len(sys.argv) == 2:
        preserve = max(int(sys.argv[1]),1)
    else:
        print(f"usage: {sys.argv[0]} <preserve>")
        exit(0)
    for dir in os.listdir("output"):
        dir_fp = f"output/{dir}/.working"
        if not os.path.isdir(dir_fp):
            continue
        with open(f"{dir_fp}/pch.txt","r") as pchf:
            pch = int(pchf.read())
            if pch <= preserve:
                continue
            pch -= preserve
            for ch in range(pch):
                ch_path = f"output/{dir}/ch{ch:04}.mp3"
                if os.path.exists(ch_path):
                    os.remove(ch_path)

    for dir in os.listdir("output"):
        dir_fp = f"output/{dir}/.working"
        if not os.path.isdir(dir_fp):
            continue
        ch_dir = f"{dir_fp}/ch"
        if os.path.isdir(ch_dir):
            shutil.rmtree(ch_dir)
        with open(f"{dir_fp}/tch.txt","r") as tchf:
            tch = int(tchf.read())
            for ch in range(tch+1,9999):
                ch_path = f"output/{dir}/ch{ch:04}.mp3"
                txt_file = f"{dir_fp}/txt/ch{ch:04}.txt"
                txt_dir = f"{dir_fp}/txt/ch{ch:04}"
                if os.path.isfile(ch_path):
                    os.remove(ch_path)
                if os.path.isfile(txt_file):
                    os.remove(txt_file)
                if os.path.isdir(txt_dir):
                    shutil.rmtree(txt_dir)

if __name__ == "__main__":
    clean()
