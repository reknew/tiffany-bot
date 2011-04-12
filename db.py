# -*- coding: utf-8 -*-
"""
this file provides DB class.
"""
# you need to install SQLAlchemy by easy_install.
#   $ sudo easy_install SQLAlchemy
# if you use mac os x, run the following command instead of the previous command
#   $ sudo easy_install-2.6 SQLAlchemy
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from mail import sendMail

from color import debug_print, warn_print, verbose_print
from config import MY_HANDLE

class DBInterface(object):
    """
    this is an interface class to database.
    """
    _engine = None
    _session = None
    
    def __init__(self, dbname, debug = False):
        self._engine = create_engine("sqlite:///" + dbname, echo = debug)
        Session = sessionmaker(bind = self.getEngine())
        self._session = Session()
        return
    
    def createTables(self):
        """
        craate the tables according to the definitions of classes
        """
        metadata = Base.metadata
        metadata.create_all(self._engine)
        return
    
    def commit(self):
        """
        commit sqls into DB.
        you need to call this commit method if you want to add objects
        into DB.
        """
        self.getSession().commit()
        
    def add(self, obj):
        """
        add an object into database
        """
        self.getSession().add(obj)
        self.commit()           # paranoially
        return obj
    
    def addAll(self, objs):
        """
        add some objects into database
        """
        self.getSession().add_all(objs)
        self.commit()           # paranoially
        return objs
    
    def query(self, klass):
        """
        query instances from DB
        """
        return self.getSession().query(klass)
    
    # utility interface
    def findChatFromName(self, chat_name):
        return list(self.query(ChatData).filter_by(room_name = chat_name))
    def findChatFromID(self, id):
        return list(self.query(ChatData).filter_by(id = id))
    def findTopicFromNameAndRoomID(self, topic_name, room_id):
        return list(self.query(TopicData).filter_by(topic_name = topic_name,
                                                    room_id = room_id))
    def findTopicFromName(self, topic_name):
        return list(self.query(TopicData).filter_by(topic_name = topic_name))
    def findTopicFromID(self, id):
        return list(self.query(TopicData).filter_by(id = id))
    def findTopicFromRoomID(self, chat_id):
        return list(self.query(TopicData).filter_by(room_id = chat_id))
    def findMessageFromID(self, id):
        return list(self.query(MessageData).filter_by(id = id))
    def findMessageFromTopicID(self, topic_id):
        return list(self.query(MessageData).filter_by(topic_id = topic_id))

    def sendMail(self, room_id, topic_id):
        # search the all messages from room_id and topic_id
        verbose_print("topic_id = %s" % (topic_id))
        messages = self.findMessageFromTopicID(topic_id)
        room = self.findChatFromID(room_id)[0]
        topic = self.findTopicFromID(topic_id)[0]
        body = u"\n".join([u'%s "%s"' % (m.getUserName(), m.getMessageText())
                          for m in messages])
        sendMail(room.getRoomName(), topic.getTopicName(), body)
        #print messages
    # accessors
    def getEngine(self):
        return self._engine
    
    def getSession(self):
        return self._session

Base = declarative_base()

# DB-serializable classes
class ChatData(Base):
    """
    ChatData is a class which is serializ-able to DB.
    """
    __tablename__ = "chats"
    id = Column(Integer, primary_key = True)
    room_name = Column(String)
    
    def __init__(self, room_name):
        self.room_name = room_name
        return
    
    def __repr__(self):
        return "<Chat (%s, %s)>" % (self.getID(), self.getRoomName())
    
    # accessors
    def getID(self):
        return self.id
    def getRoomName(self):
        return self.room_name

class TopicData(Base):
    """
    TopicData is a class which is serializ-able to DB.
    """
    __tablename__ = "topics"
    id = Column(Integer, primary_key = True)
    room_id = Column(Integer)
    topic_name = Column(String)
    
    def __init__(self, topic_name, room_id):
        self.room_id = room_id
        self.topic_name = topic_name
        return
    
    def __repr__(self):
        return "<Topic (%s, %s, %s)>" % (self.getID(),
                                         self.getTopicName(),
                                         self.getRoomID())
    # accessors
    def getID(self):
        return self.id
    def getTopicName(self):
        return self.topic_name
    def getRoomID(self):
        return self.room_id

class MessageData(Base):
    """
    MessageData is a class which is serializ-able to DB.
    """
    __tablename__ = "messages"
    id = Column(Integer, primary_key = True)
    message_text = Column(String)
    topic_id = Column(Integer)
    user_name = Column(String(128))
    
    def __init__(self, message_text, topic_id, user_name = MY_HANDLE):
        self.message_text = message_text
        self.topic_id = topic_id
        self.user_name = user_name
        return
    
    def __repr__(self):
        return "<Message (%s, %s, %s, %s)>" % (self.getID(),
                                               self.getMessageText(),
                                               self.getUserName(),
                                               self.getTopicID())
    
    # accessors
    def getID(self):
        return self.id
    
    def getMessageText(self):
        return self.message_text
    
    def getTopicID(self):
        return self.topic_id

    def getUserName(self):
        return self.user_name
