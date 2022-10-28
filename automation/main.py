import os

from datetime import datetime

from ahk import AHK

from rucoy_online import RucoyOnline
import geometry

s = 'C:\\Program Files\\AutoHotkey\\AutoHotKey.exe'
ahk = AHK(executable_path=s)


def shutdown():
    fin = open("data.txt", "a")
    # current date and time
    fin.write(f'\nFinished at: {datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}')
    fin.close()
    window.close()
    os.system("shutdown /s /t 1")


if __name__ == '__main__':
    window = ahk.win_get(title='BlueStacks')
    if not window.exist:
        raise Exception("Bluestacks window not active")
    window.move(x=0, y=0, width=900, height=0)  # height=0 is needed, but just change width
    window.activate()
    bluestacks_window_rectangle = geometry.create_rectangle_from_ahk_window(window)
    rucoy = RucoyOnline(bluestacks_window_rectangle)
    rucoy.automate_training()

    shutdown()
