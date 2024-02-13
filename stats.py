import sys
import os

def get_chapters_left():
    ret = []
    for dir in os.listdir("output"):
        dir_fp = f"output/{dir}/.working"
        if not os.path.isdir(dir_fp):
            continue
        with open(f"{dir_fp}/sch.txt","r") as schf:
            sch = int(schf.read())
            with open(f"{dir_fp}/pch.txt","r") as pchf:
                pch = int(pchf.read())
                ret += [(sch-pch+1,dir)]
    return ret 

def get_current_time():
    ret = []
    for dir in os.listdir("output"):
        dir_fp = f"output/{dir}/.working"
        if not os.path.isdir(dir_fp):
            continue
        with open(f"{dir_fp}/t.txt","r") as tf:
            t = float(tf.read())
            with open(f"{dir_fp}/pch.txt","r") as pchf:
                pch = int(pchf.read())
                ret += [(pch,t,dir)]
    return ret 

def main():
    if "s" in sys.argv[1]:
        print("Chapters left:")
        for c,dir in get_chapters_left():
            print(f"  {dir}: {c}")
    if "c" in sys.argv[1]:
        print("Current chapter and time:")
        for c,t,dir in get_current_time():
            print(f"  {dir}: ch {c} t {t}")
if __name__ == "__main__":
    main()
