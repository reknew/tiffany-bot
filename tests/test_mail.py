#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append("../")

import mail

mail.sendMail("test_room", u'test_topicおおお', u'Hello, Worldおおお')
