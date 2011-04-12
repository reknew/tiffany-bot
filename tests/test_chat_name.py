#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
sys.path.append("../")

import skype

room_name = "hgoe hoge"
topic_name = "fuga fuga"

full_name = skype.buildChatName(room_name, topic_name)

print "(%s, %s) => %s" % (room_name, topic_name, full_name)

full_name = u"RK_abc d er _会議中"

print u"%s => %s" % (full_name, (skype.parseChatName(full_name)))
