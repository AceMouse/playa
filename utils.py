import os
import safer 
from pytimedinput import timedKeyOrNumber
from lib.pytui.pytui import Tui

pollRate = 0.01
def get_file(title, tui=Tui(), default_file='.def', directory='.', exclude=[], include_dirs=True, include_files=True):
    dfp = f"{directory}/{default_file}"
    exclude += [default_file]
    tui.clear()
    book = "" 
    books = []
    for dir in os.listdir(directory):
        dir_fp = f"{directory}/{dir}"
        if (os.path.isdir(dir_fp) and not include_dirs) or (os.path.isfile(dir_fp) and not include_files) or dir in exclude:
            continue
        books += [dir] 
    if not os.path.isfile(dfp):
        with safer.open(dfp, "w") as dbf:
            dbf.write(books[0])
    books.sort()

    default_book = ""
    with safer.open(dfp, "r") as dbf:
        default_book = str(dbf.read())
    book = default_book
    tui.buffered=True
    tui.clear()
    tui.place_text(f"{title} (1-{len(books)}):", height=1, row=0)
    for i,b in enumerate(books):
        tui.place_text(f"{i+1:>2} {b}", height=1, col=2, row=i+1)
    tui.buffered=False
    arrow_number = books.index(default_book) if default_book in books else 0
    while True:
        tui.place_text("->", row=arrow_number+1, width = 2, height=1)
        i, _ = timedKeyOrNumber(timeout = -1, allowCharacters = f"tws ", allowNegative = False, allowFloat = False, pollRate = pollRate,eatKeyInput=True,newline=False,delayedEatInput=True, ignoreCase=True)
        if i == 't':
            return None
        if i == "w":
            tui.place_text("", row=arrow_number+1, width = 2, height=1)
            arrow_number = max(0, arrow_number-1)
            book = books[arrow_number]
            continue
        if i == "s":
            tui.place_text("", row=arrow_number+1, width = 2, height=1)
            arrow_number = min(len(books)-1, arrow_number+1)
            book = books[arrow_number]
            continue
        if i != None and i != " ":
            i = int(i)
            if i == 0 or i > len(books):
                continue
            book = books[i-1]
        with safer.open(dfp, "w") as dbf:
            dbf.write(book)
        break
    tui.clear()
    return book
