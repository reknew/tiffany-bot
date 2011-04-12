#!/usr/bin/env python

import sys
sys.path.append("../")

import db

print "create db on memory"
di = db.DBInterface(":memory:", debug = False)

print "create tables"
di.createTables()

print "add a chat"
chat = db.ChatData("room A")
di.add(chat)
print "chat = %s" % (chat)      # have id

print "add a topic"
topic = db.TopicData("topic A", chat.getID())
di.add(topic)
print "topic = %s" % (topic)

print "add a message"
message = db.MessageData("Hello World", topic.getID())
di.add(message)
print "message = %s" % (message)

print "add a message"
message = db.MessageData("GoodBye World", topic.getID())
di.add(message)
print "message = %s" % (message)


print "query messages of the topic"
#chat = di.query(db.ChatData).filter_by(room_name = "room A").first()
messages = di.query(db.MessageData).filter_by(topic_id = topic.getID())
print list(messages)

