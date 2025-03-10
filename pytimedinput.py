#stolen from: https://github.com/WereCatf/pytimedinput/blob/main/pytimedinput/pytimedinput.py 
#added sleep to while loop to not let my pc melt. 
import sys
import time
from typing import Tuple, Union
if(sys.platform == "win32"):
    import msvcrt
    import ctypes
    from ctypes import wintypes
else:
    import select
    import tty
    import termios


def timedInput(prompt: str = "", timeout: float = 5, resetOnInput: bool = True, maxLength: int = 0, allowCharacters: str = "", endCharacters: str = "\x1b\n\r", pollRate: float = 0, eatInput: bool = False,newline:bool=True,delayedEatInput:bool=False, ignoreCase:bool=False) -> Tuple[str, bool]:
    """Ask the user for text input with an optional timeout and limit on allowed characters.

    Args:
        prompt (str, optional): The prompt to be displayed to the user. Defaults to "".
        timeout (float, optional): How many seconds to wait for input. Defaults to 5, use -1 to wait forever.
        resetOnInput (bool, optional): Reset the timeout-timer any time user presses a key. Defaults to True.
        maxLength (int, optional): Maximum length of input user is to be allowed to type. Defaults to 0, use 0 to disable. 
        allowCharacters (str, optional): Which characters the user is allowed to enter. Defaults to "", ie. any character.
        endCharacters (str, optional): On which characters to stop accepting input. Defaults to "\\x1b\\n\\r", ie. ESC and Enter. Cannot be empty.
        pollRate (float, optional): How long to sleep between polls. Defaults to 0, use 0 to disable.

    Returns:
        Tuple[str, bool]: The characters input by the user and whether the input timed out or not.
    """
    if(maxLength < 0):
        return "", False
    if(len(endCharacters) == 0):
        return "", False
    return __timedInput(prompt, timeout, resetOnInput, maxLength, allowCharacters, endCharacters, pollRate=pollRate, eatInput=eatInput,newline=newline,delayedEatInput=delayedEatInput, ignoreCase=ignoreCase)

def timedKeyOrNumber(prompt: str = "", timeout: float = 5, resetOnInput: bool = True, allowCharacters: str = "",allowNegative: bool = True, allowFloat: bool = True, pollRate: float = 0, eatInput: bool = False, eatKeyInput: bool = False, newline:bool=True,delayedEatInput:bool=False, ignoreCase:bool=False) -> Tuple[Union[str, int, float, None], bool]:
    """Ask the user to press a single key out of an optional list of allowed ones or an integer or float value.

    Args:
        prompt (str, optional): The prompt to be displayed to the user. Defaults to "".
        timeout (float, optional): How many seconds to wait for input. Defaults to 5, use -1 to wait forever.
        resetOnInput (bool, optional): Reset the timeout-timer any time user presses a key. Defaults to True.
        allowCharacters (str, optional): Which characters the user is allowed to enter. Defaults to "", ie. any character.
        allowNegative (bool, optional): Whether to allow the user to enter a negative value or not.
        allowFloat (bool, optional): Whether to allow the user to enter a floating point number.
        pollRate (float, optional): How long to sleep between polls. Defaults to 0, use 0 to disable.

    Returns:
        Tuple[Union[str, int, float, None], bool]: Which key the user pressed or the value entered by the user, and whether the input timed out or not.
    """
    extraAllowedCharacters = set("0123456789".split())
    if allowNegative:
        extraAllowedCharacters.add("-")
    if allowFloat:
        extraAllowedCharacters.add(",")
        extraAllowedCharacters.add(".")
    for c in allowCharacters:
        if c in extraAllowedCharacters:
            extraAllowedCharacters.remove(c) 
    extraAllowedCharactersFinal = "".join(extraAllowedCharacters)

    x, timedOut = __timedInput(prompt, timeout, resetOnInput, maxLength=1, allowCharacters=allowCharacters + extraAllowedCharactersFinal, endCharacters="\x1b\n\r", inputType="single", pollRate = pollRate, newline = False, eatInput = eatKeyInput, ignoreCase=ignoreCase)
    if x == "":
        return None, timedOut
    if timedOut or x in allowCharacters: 
        return x, timedOut
    userInput, timedOut = __timedInput(
        "", timeout, resetOnInput, allowCharacters="", inputType="float" if allowFloat else "integer", pollRate = pollRate, userInput = x, eatInput=eatInput, newline=newline,delayedEatInput=delayedEatInput)
    try:
        return float(userInput) if allowFloat else int(userInput), timedOut
    except:
        return None, timedOut




def timedKey(prompt: str = "", timeout: float = 5, resetOnInput: bool = True, allowCharacters: str = "", pollRate: float = 0, eatInput: bool = False,newline:bool = True,delayedEatInput:bool=False, ignoreCase:bool=False) -> Tuple[str, bool]:
    """Ask the user to press a single key out of an optional list of allowed ones.

    Args:
        prompt (str, optional): The prompt to be displayed to the user. Defaults to "".
        timeout (float, optional): How many seconds to wait for input. Defaults to 5, use -1 to wait forever.
        resetOnInput (bool, optional): Reset the timeout-timer any time user presses a key. Defaults to True.
        allowCharacters (str, optional): Which characters the user is allowed to enter. Defaults to "", ie. any character.
        pollRate (float, optional): How long to sleep between polls. Defaults to 0, use 0 to disable.

    Returns:
        Tuple[str, bool]: Which key the user pressed and whether the input timed out or not.
    """
    return __timedInput(prompt, timeout, resetOnInput, maxLength=1, allowCharacters=allowCharacters, endCharacters="", inputType="single", pollRate = pollRate, eatInput = eatInput,newline=newline, delayedEatInput=delayedEatInput, ignoreCase=ignoreCase)


def timedInteger(prompt: str = "", timeout: float = 5, resetOnInput: bool = True, allowNegative: bool = True, pollRate: float = 0, eatInput: bool = False,newline:bool=True,delayedEatInput:bool=False) -> Tuple[Union[int, None], bool]:
    """Ask the user to enter an integer value.

    Args:
        prompt (str, optional): The prompt to be displayed to the user. Defaults to "".
        timeout (float, optional): How many seconds to wait for input. Defaults to 5, use -1 to wait forever.
        resetOnInput (bool, optional): Reset the timeout-timer any time user presses a key. Defaults to True.
        allowNegative (bool, optional): Whether to allow the user to enter a negative value or not.
        pollRate (float, optional): How long to sleep between polls. Defaults to 0, use 0 to disable.

    Returns:
        Tuple[Union[int, None], bool]: The value entered by the user and whether the input timed out or not.
    """
    userInput, timedOut = __timedInput(
        prompt, timeout, resetOnInput, allowCharacters="-" if(allowNegative) else "", inputType="integer", pollRate = pollRate, eatInput = eatInput, newline=newline,delayedEatInput=delayedEatInput)
    try:
        return int(userInput), timedOut
    except:
        return None, timedOut


def timedFloat(prompt: str = "", timeout: float = 5, resetOnInput: bool = True, allowNegative: bool = True, pollRate: float = 0, eatInput: bool = False,newline:bool=True,delayedEatInput:bool=False) -> Tuple[Union[float, None], bool]:
    """Ask the user to enter a floating-point value.

    Args:
        prompt (str, optional): The prompt to be displayed to the user. Defaults to "".
        timeout (float, optional): How many seconds to wait for input. Defaults to 5, use -1 to wait forever.
        resetOnInput (bool, optional): Reset the timeout-timer any time user presses a key. Defaults to True.
        allowNegative (bool, optional): Whether to allow the user to enter a negative value or not.
        pollRate (float, optional): How long to sleep between polls. Defaults to 0, use 0 to disable.

    Returns:
        Tuple[Union[float, None], bool]: The value entered by the user and whether the input timed out or not.
    """
    userInput, timedOut = __timedInput(
        prompt, timeout, resetOnInput, allowCharacters="-" if(allowNegative) else "", inputType="float", pollRate = pollRate, eatInput = eatInput,newline=newline,delayedEatInput=delayedEatInput)
    try:
        return float(userInput), timedOut
    except:
        return None, timedOut

def __timedInput(prompt: str = "", timeout: float = 5, resetOnInput: bool = True, maxLength: int = 0, allowCharacters: str = "", endCharacters: str = "\x1b\n\r", inputType: str = "text", pollRate: float = 0, newline: bool = True, userInput: str = "", eatInput: bool = False,delayedEatInput:bool=False, ignoreCase:bool=False) -> Tuple[str, bool]:
    def checkStdin():
        if(sys.platform == "win32"):
            return msvcrt.kbhit()
        else:
            return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    def readStdin():
        if(sys.platform == "win32"):
            return msvcrt.getwch()
        else:
            return sys.stdin.read(1)

    if(not sys.__stdin__.isatty()):
        raise RuntimeError(
            "timedInput() requires an interactive shell, cannot continue.")
    else:
        __savedConsoleSettings = __getStdoutSettings()
        __enableStdoutAnsiEscape()

        numbers = "01234567890"
        if(inputType == "integer"):
            allowCharacters += numbers
        if(inputType == "float"):
            allowCharacters += numbers + ".,"
        if ignoreCase:
            allowCharacters = allowCharacters.lower() + allowCharacters.upper()

        timeStart = time.time()
        timedOut = False
        if(len(prompt) > 0):
            print(prompt, end='', flush=True)

        if not eatInput:
            print(userInput, end='', flush=True)

        while(True):
            if(timeout > -1.0 and (time.time() - timeStart) >= timeout):
                timedOut = True
                break
            if(checkStdin()):
                inputCharacter = readStdin()
                if(inputCharacter in endCharacters):
                    break
                if(inputCharacter != '\b' and inputCharacter != '\x7f'):
                    if(len(allowCharacters) and not inputCharacter in allowCharacters):
                        inputCharacter = ""
                    if(inputCharacter == "-" and inputType in ["integer", "float"]):
                        if(len(userInput) > 0):
                            inputCharacter = ""
                    if(maxLength > 0 and len(userInput) >= maxLength):
                        inputCharacter = ""
                    if(inputType == "float"):
                        if(inputCharacter == ","):
                            inputCharacter = "."
                        if(inputCharacter == "." and inputCharacter in userInput):
                            inputCharacter = ""
                    userInput = userInput + inputCharacter
                    if not eatInput:
                        print(inputCharacter, end='', flush=True)
                    if(maxLength == 1 and len(userInput) == 1 and inputType == "single"):
                        break
                else:
                    if(len(userInput)):
                        userInput = userInput[0:len(userInput) - 1]
                        print("\x1b[1D\x1b[0K", end='', flush=True)
                if(resetOnInput and timeout > -1):
                    timeStart = time.time()
            if(pollRate != 0):
                time.sleep(pollRate)
        if newline:
            print("")
        if(delayedEatInput and not eatInput):
            print("\x1b[1D\x1b[0K"*len(userInput), end='', flush=True)
        __setStdoutSettings(__savedConsoleSettings)
        if ignoreCase:
            return userInput.lower(), timedOut
        return userInput, timedOut


def __getStdoutSettings():
    if(sys.platform == "win32"):
        __savedConsoleSettings = wintypes.DWORD()
        kernel32 = ctypes.windll.kernel32
        # The Windows standard handle -11 is stdout
        kernel32.GetConsoleMode(
            kernel32.GetStdHandle(-11), ctypes.byref(__savedConsoleSettings))
    else:
        __savedConsoleSettings = termios.tcgetattr(sys.stdin)
    return __savedConsoleSettings


def __setStdoutSettings(__savedConsoleSettings):
    if(sys.platform == "win32"):
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(
            kernel32.GetStdHandle(-11), __savedConsoleSettings)
    else:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, __savedConsoleSettings)


def __enableStdoutAnsiEscape():
    if(sys.platform == "win32"):
        kernel32 = ctypes.windll.kernel32
        # Enable ANSI escape sequence parsing
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    else:
        # Should be enabled by default under Linux (and OSX?), just set cbreak-mode
        tty.setcbreak(sys.stdin.fileno(), termios.TCSADRAIN)
