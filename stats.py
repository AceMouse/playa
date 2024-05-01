import sys
import os

def get_chapters_left():
    ret = []
    for dir in os.listdir("output"):
        complete = os.path.exists(f"output/{dir}/.complete")
        dir_fp = f"output/{dir}/.working"
        if not os.path.isdir(dir_fp):
            continue
        with open(f"{dir_fp}/sch.txt","r") as schf:
            sch = int(schf.read())
            with open(f"{dir_fp}/pch.txt","r") as pchf:
                pch = int(pchf.read())
                ret += [(sch-pch,sch,complete,dir)]
    return ret 

def get_current_time():
    ret = []
    for dir in os.listdir("output"):
        complete = os.path.exists(f"output/{dir}/.complete")
        dir_fp = f"output/{dir}/.working"
        if not os.path.isdir(dir_fp):
            continue
        with open(f"{dir_fp}/t.txt","r") as tf:
            z = tf.read()
            t = 0 if z == '' else float(z)
            with open(f"{dir_fp}/pch.txt","r") as pchf:
                pch = int(pchf.read())
                ret += [(pch,t,complete,dir)]
    return ret 

def get_urls():
    ret = []
    for dir in os.listdir("output"):
        complete = os.path.exists(f"output/{dir}/.complete")
        dir_fp = f"output/{dir}/.working"
        if not os.path.isdir(dir_fp):
            continue
        with open(f"{dir_fp}/url.txt","r") as tf:
            url = tf.read()
            ret += [(url,complete)]
    return ret 

def get_urls_by_domain(show_complete):
    ret = dict()
    urls = get_urls()
    for (url,complete) in urls:
        if show_complete or not complete:
            d = url.split('/')[2] 
            if d in ret:
                ret[d] += [(url,complete)]
            else: 
                ret[d] = [(url,complete)]
    return ret 

def main():
    show_complete = "x" in sys.argv[1]
    if "s" in sys.argv[1]:
        print("Chapters left:")
        for c,t,complete,dir in get_chapters_left():
            if show_complete or not complete:
                print(f"  {'*'*int(complete)}{dir}: {c} ({t})")
    if "c" in sys.argv[1]:
        print("Current chapter and time:")
        for c,t,complete,dir in get_current_time():
            if show_complete or not complete:
                print(f"  {'*'*int(complete)}{dir}: ch {c} t {t}")
    if "u" in sys.argv[1]:
        print("Current urls:")
        for url,complete in get_urls():
            if show_complete or not complete:
                print(f"  {'*'*int(complete)}{url}")
    if "d" in sys.argv[1]:
        print("Current urls by domain:")
        for d, urls in get_urls_by_domain(show_complete).items():
            print(f"  {d}:")
            for u,complete in urls:
                if show_complete or not complete:
                    print(f"    {'*'*int(complete)}{u}")

if __name__ == "__main__":
    main()
