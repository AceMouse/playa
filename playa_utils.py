
def get_var(name, default=None):
    if name in locals():
        return locals()[name]
    elif name in globals():
        return globals()[name]
    return default
