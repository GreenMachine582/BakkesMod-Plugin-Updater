from __future__ import annotations

import glob
import logging
import os
import shutil
import subprocess
import sys
import time
from threading import Thread

from tkinter import ttk
import tkinter as tk
from tkinter.messagebox import showinfo, showerror


__version__ = '2.3.2'
__date__ = '15/07/2022'


logging.basicConfig(level=logging.INFO, filename='log.txt', filemode='w',
                    format="%(asctime)s - %(levelname)s - '%(message)s' - %(funcName)s")

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
DOWNLOAD_DIR = f"{os.environ['USERPROFILE']}\\Downloads"
BAKKESMOD_DIR = f"{os.environ['APPDATA']}\\bakkesmod\\bakkesmod"

PLUGINS_URL = "https://bakkesplugins.com/plugins/download/26"


settings = {'download_dir': DOWNLOAD_DIR,
            'bakkesmod_dir': BAKKESMOD_DIR}


def close() -> None:
    """
    Closes python in a safe manner.
    :return:
        - None
    """
    logging.info("Exiting program")
    sys.exit(0)


def read(file_dir: str = '') -> list:
    """
    Reads the given file and returns the contents.
    :param file_dir: str
    :return:
        - contents - list[str]
    """
    contents = []
    if os.path.exists(file_dir):
        with open(file_dir, 'r') as file:
            contents = file.readlines()
        logging.info("Read file")
        return contents
    logging.warning(f"Path does not exist: {file_dir}")
    return contents


def checkDependencies() -> bool:
    """
    Dependency checking makes it possible to verify that all components are
    present to avoid major errors.
    :return:
        - successful - bool
    """
    logging.info('Checking dependencies')
    for _file in ["settings.txt", "unzip_file.bat"]:
        if not os.path.exists(_file):
            logging.error(f"Path does not exist: {_file}")
            return False

    for _setting in settings:
        if '_dir' in _setting:
            if not os.path.exists(settings[_setting]):
                logging.warning(f"Directory does not exist: (Default {_setting}) {settings[_setting]}")

    logging.info('Checking done')
    return True


def loadSettings() -> bool:
    """
    Loads and updates settings.
    :return:
        - error - bool
    """
    global settings
    logging.info("Loading settings")

    contents = read("settings.txt")
    if not contents:
        for setting in settings:
            if '_dir' in setting:
                if not os.path.exists(settings[setting]):
                    logging.error(f"Directory does not exist: (Default {setting}) {settings[setting]}")
                    return False
        logging.info("Using default settings")
        return True

    for line in contents:
        line = line.replace('\n', '')
        if line and line[0] != '#':
            setting, value = line.split('=', 1)
            if setting in settings:
                if '_dir' in setting:
                    if os.path.exists(value):
                        settings[setting] = value
                        logging.info(f"Using directory (Settings {setting}) {value}")
                    elif not os.path.exists(settings[setting]):
                        logging.error(f"Directory does not exist (Settings {setting}) {value}")
                        logging.error(f"Directory does not exist (Default {setting}) {settings[setting]}")
                        return False
                    else:
                        logging.warning(f"Directory does not exist (Settings {setting}) {value}")
                        logging.info(f"Using directory (Default {setting}) {settings[setting]}")

    logging.info("Loading done")
    return True


def downloadPlugins(download_dir: str) -> tuple:
    """
    Runs a batch program to download the plugins
    :param download_dir: str
    :return:
        - filename, latest_file - tuple[str, str]
    """
    logging.info("Downloading")

    subprocess.Popen(f"""start "" {PLUGINS_URL}""", shell=True)
    
    while True:
        files = glob.glob(f"{download_dir}\\*.zip")
        latest_file = max(files, key=os.path.getctime)
        if 'RocketPlugin_' in latest_file:
            filename = latest_file.replace(f"{download_dir}\\", '')
            logging.info(f"Download done")
            return filename, latest_file


def unzipPlugins(file_dir: str) -> None:
    """
    Runs a batch program to unzip file.
    :param file_dir: str
    :return:
        - None
    """
    logging.info("Unzipping")
    if os.path.exists(f"{file_dir}"):
        logging.info("Already unzipped")
        return

    process = subprocess.Popen(args=['unzip_file.bat', f"{file_dir}"], shell=True)
    process.wait()

    logging.info("Unzipping done")


def updatePlugins(bakkesmod_dir: str, file_dir: str) -> None:
    """
    Uses shutil to copy and overwrite files to perform an update.
    :param bakkesmod_dir: str
    :param file_dir: str
    :return:
        - None
    """
    logging.info("Updating plugins")
    for filename in os.listdir(f"{file_dir}\\data\\RocketPlugin\\presets"):
        shutil.copy(f"{file_dir}\\data\\RocketPlugin\\presets\\{filename}", f"{bakkesmod_dir}\\cfg\\")
    shutil.copy(f"{file_dir}\\plugins\\RocketPlugin.dll", f"{bakkesmod_dir}\\plugins\\")
    shutil.copy(f"{file_dir}\\plugins\\settings\\rocketplugin.set", f"{bakkesmod_dir}\\plugins\\settings\\")
    logging.info("Update done")


def cleanDownloads(zipped_file_dir: str, file_dir: str) -> None:
    """
    Removes the downloaded and other irrelevant files.
    :param zipped_file_dir: str
    :param file_dir: str
    :return:
        - None
    """
    logging.info("Cleaning downloads")
    os.remove(zipped_file_dir)
    shutil.rmtree(file_dir)
    logging.info("Cleanup done")


class GUI(object):
    """
    A Graphical User Interface (GUI) to display a progress bar with text.
    """
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry('300x120')
        self.root.title('BakkesMod Plugin Updator')

        self.progress = 0
        thread = Thread(target=self.main, args=("Thread-2",))

        self.progress_bar = ttk.Progressbar(self.root, orient='horizontal', mode='determinate', length=280)
        self.progress_bar.grid(column=0, row=0, columnspan=2, padx=10, pady=20)

        self.value_label = ttk.Label(self.root, text="Waiting to start")
        self.value_label.grid(column=0, row=1, columnspan=2)

        self.start_button = ttk.Button(self.root, text='Start', command=lambda: thread.start())
        self.start_button.grid(column=0, row=2, padx=10, pady=10, sticky=tk.E)

        self.root.mainloop()
        thread.join()

    def update(self, progress: int | float) -> None:
        """
        Updates the tkinter gui values for the progress bar and text.
        :param progress: int | float
        :return:
            - None
        """
        self.progress += progress
        self.progress_bar.config(value=(int(-(-self.progress // 1))))
        self.value_label.config(text=f"Current Progress: {round(self.progress, 2)}%")

    def main(self, thread_name: str) -> None:
        """
        Main program that updates BakkesMod Plugins.
        :param thread_name: str
        :return:
            - None
        """
        logging.info(f"Thread started: {thread_name}")

        error_occurred = False
        while not error_occurred:
            if not checkDependencies():
                error_occurred = True
                showerror(message="Could not resolve dependencies!")
                break
            self.root.after_idle(self.update, (100 / 6))
            if not loadSettings():
                error_occurred = True
                showerror(message="Could not resolve settings!")
                break
            self.root.after_idle(self.update, (100 / 6))

            filename, zipped_file_dir = downloadPlugins(settings['download_dir'])
            self.root.after_idle(self.update, (100 / 6))

            file_dir = zipped_file_dir.replace('.zip', '')
            unzipPlugins(file_dir)
            self.root.after_idle(self.update, (100 / 6))

            updatePlugins(settings['bakkesmod_dir'], file_dir)
            self.root.after_idle(self.update, (100 / 6))

            cleanDownloads(zipped_file_dir, file_dir)
            self.root.after_idle(self.update, (100 / 6))
            showinfo(message="Plugins were updated Successfully!")
            break

        if error_occurred:
            showerror(message="Error occurred! Please email the 'log.log' file to greenchicken1902@gmail.com")
        logging.info('Quiting root')
        self.root.quit()


if __name__ == '__main__':
    try:
        logging.info('Starting program')
        gui = GUI()
    except Exception as e:
        logging.error(e)
    raise close()
