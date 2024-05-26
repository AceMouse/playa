import os

def main():
    dest = input("title of the novel: ").strip().replace(' ', '-')
    if os.path.exists(f"output/{dest}/"):
        print(f"{dest} already exists.")
        quit()
    url = input("url: ")
    ch = int(input("chapter: "))
    working = f"output/{dest}/.working"
    url_fp = f"{working}/url.txt"
    sch_fp = f"{working}/sch.txt"
    tch_fp = f"{working}/tch.txt"
    pch_fp = f"{working}/pch.txt"
    ch_dir = f"{working}/ch"
    t_fp   = f"{working}/t.txt"
    os.makedirs(ch_dir, exist_ok=True)
    with open(url_fp,"w") as urlf:
        urlf.write(url)
    with open(sch_fp,"w") as schf:
        schf.write(str(ch))
    with open(pch_fp,"w") as pchf:
        pchf.write(str(ch))
    with open(tch_fp,"w") as tchf:
        tchf.write(str(ch))
    with open(t_fp,"w") as tf:
        tf.write(str(0))

if __name__ == "__main__":
    main()
