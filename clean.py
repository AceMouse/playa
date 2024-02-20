import sys
import os
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
if __name__ == "__main__":
    clean()
