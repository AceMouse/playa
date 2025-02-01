from utils import get_file
def edit():
    book = get_file("Choose a book",default_file=".def_book", directory="output", include_files=False, exclude=[".logging"]) 
    if book is None:
        return

    folder = f"output/{book}/.working"
    file = get_file("Choose a file to edit",directory=folder, include_dirs=False)
    if file is None:
        return
    file = f"{folder}/{file}"
    content = ""
    print(f"{file} content:")
    with open(file,"r") as f:
        content = f.read()
        print(f"\t{content}")
    print("write new content:")
    with open(file,"w") as f:
        i = input()
        if i.strip() == "":
            i = content
        elif i[0] == '+':
            i = str(int(i[1:]) + int(content))
        elif i[0] == '-':
            i = str(-int(i[1:]) + int(content))
        f.write(i)
        print(f"new content: {i}")

edit()
