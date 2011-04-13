#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a skype chat bot for logging.
The features of this bot are:
 1. automatic invitation of the friends.
 2. automatic logging and sending it to email.

the titles of chat room will be ${prefix}_${room}-${topic}.
you can define ${prefix} in config.py.

all the message and files tiffanybots received are stored into sqlite3 DB
with timestamp.

"""

import sys
# local library
from db import DBInterface
from config import DB_NAME
from skype import SkypeEventHandler
from color import verbose_print
import time

class TiffanyBot(object):
    "application class of tiffanybot."
    _skype = None
    
    def __init__(self):
        """constructor of TiffanyBot. make an instance of Skype4Py
        to register itself"""
        self._skype = SkypeEventHandler(DBInterface(DB_NAME))
        return
    
    def main(self):
        """main function of tiffanybot. it runs main-loop of
        this application."""
        while True:
            time.sleep(1.0)
            print "[%s] tick" % (time.localtime(time.time()))

if __name__ == "__main__":
    bot = TiffanyBot()
    verbose_print("connected!")
    bot.main()
