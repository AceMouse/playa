import sys
import os
def edit():
    book = "" 
    if len(sys.argv) <= 1:
        books = []
        for dir in os.listdir("output"):
            dir_fp = f"output/{dir}"
            if not os.path.isdir(dir_fp):
                continue
            books += [dir] 
        print(f"chose a book to edit (1-{len(books)}):")
        for i,b in enumerate(books):
            print(f"  {i+1} {b}")
        book = books[int(input())-1]
        for _ in range(len(books)+2):
            print(LINE_UP, end=LINE_CLEAR)
    else:
        book = sys.argv[1]

    folder = f"output/{book}"
    files = []
    for dir in os.listdir(f"{folder}/.working"):
        files += [dir] 
    print(f"chose a file to edit (1-{len(files)}):")
    for i,f in enumerate(files):
        print(f"  {i+1} {f}")
    file = f"{folder}/.working/{files[int(input())-1]}"
    for _ in range(len(files)+2):
        print(LINE_UP, end=LINE_CLEAR)
    content = ""
    print(f"{file} content:")
    with open(file,"r") as f:
        content = f.read()
        print(f"\t{content}")
    print("write new content:")
    with open(file,"w") as f:
        i = input()
        print(LINE_UP, end=LINE_CLEAR)
        print(LINE_UP, end=LINE_CLEAR)
        print(LINE_UP, end=LINE_CLEAR)
        if i[0] == '+':
            i = str(int(i[1:]) + int(content))
        if i[0] == '-':
            i = str(-int(i[1:]) + int(content))
        f.write(i)
        print(f"new content: {i}")

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'
edit()
