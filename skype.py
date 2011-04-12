"""
this file provides some interface classes to skype.

these classes are depending on the db classes defined in db.py.
"""

# you need to install skype4py using subversion:
#   $ svn co https://skype4py.svn.sourceforge.net/svnroot/skype4py
#   $ (cd skype4py; python setup.py build && sudo python setup.py install)
import Skype4Py

from color import debug_print, warn_print, verbose_print
from db import ChatData, TopicData, MessageData
from command import commandDispatch
from error import ChatMissed

from config import CHAT_TOPIC_PREFIX, CHAT_TOPIC_IFS, USERS

# util function
def parseChatName(chat_name):
    """
    parse the full chat name into room name and topic name.
    this function will return a list of 2 length, that is (room, topic).

    this function expect chat_name follows
    ${CHAT_TOPIC_PREFIX}${CHAT_TOPIC_IFS}${topic}${CHAT_TOPIC_IFS}${room}
    """
    splitted_text = chat_name.split(CHAT_TOPIC_IFS)
    if len(splitted_text) == 1:
        return ("", "")
    elif len(splitted_text) == 2:
        return (splitted_text[1], "")
    elif len(splitted_text) == 3:
        return (splitted_text[1], splitted_text[2])
    else:
        return (splitted_text[1], " ".join(splitted_text[2:]))

def buildChatName(room_name, topic_name):
    """
    build a full chat name from room name and topic name
    """
    return CHAT_TOPIC_PREFIX + CHAT_TOPIC_IFS + room_name + CHAT_TOPIC_IFS \
        + topic_name

def findChatFromSkype(skype, chat_name):
    """
    return a list of SkypeChat which matches chat_name specified.
    """
    return [c for c in skype.Chats if c.FriendlyName == chat_name]

class SkypeEventHandler(object):
    """
    a wrapper class of Skype4Py.Skype. the skype event handlers are
    implemented as the methods of this class.
    """
    _skype = None               # Skype4Py.Skype instance
    _chats = []                 # list of SkypeChats
    _di = None                  # DBInterface instance
    def __init__(self, di):
        """
        di = an instance of DBInterface.
        """
        self._skype = Skype4Py.Skype(Events=self)
        while True:
            try:
                self.skype().Attach()
                break
            except Skype4Py.errors.ISkypeAPIError:
                pass
        self._di = di
        di.createTables()
        return
    
    # event handlers
    def AttachmentStatus(self, status): # ??
        "callback method for attachment event"
        verbose_print("AttachmentStatus")
        return
    
    def ChatMembersChanged(self, chat, member):
        """
        callback method if a member has joined or left from chat room.
        
        this method is used to create a TiffanyChat instance and
        add it into self._chats.
        """
        verbose_print("ChatMembersChanged, chat=%s, member=%s"
                      % (chat, member))
        if chat not in self.chats():
            # need to create TiffanyChatRoom
            debug_print("adding new chat: %s" % (chat))
            self.addChat(chat)
        else:                   # already there
            verbose_print("%s is already there" % (chat))
        return
    
    def ChatMemberRoleChanged(self, member, role):
        """
        callback method called when  a role of memberis changed.
        this method is used to create a TiffanyChat instance and
        add it into self._chats
        """
        verbose_print("ChatMemberRoleChanged, member=%s, role=%s" %
                      (member.Handle, role))
        return
    
    def storeMessage(self, di, msg, chat):
        """
        store a msg into DB.
        """
        if chat.currentTopic():
            msg_data = MessageData(msg.Body,
                                   chat.currentTopic().DBInstance().getID(),
                                   msg.FromHandle)
            verbose_print("msg => %s" % (msg_data))
            di.add(msg_data)
            return msg_data
        else:
            return chat.invokeTopicHelp()
    
    def MessageStatus(self, msg, status):
        """callback method when a message is received."""
        verbose_print("MessageStatus, status=%s" % (status))
        if status == "RECEIVED": # only process if status is RECEIVED
            # check if TiffanySkype has the chat of msg in self._chats
            if msg.Chat not in [c.chat() for c in self.chats()]:
                self.addChat(msg.Chat)
            command = commandDispatch(msg.Body)
            debug_print("command = %s" % (command.command()))
            target_chat = self.findChat(msg.Chat)
            # check the chat have topic
            if command:
                command.run(target_chat, self.DBInterface())
            if not target_chat.currentTopic():
                target_chat.invokeTopicHelp()
            else:
                self.storeMessage(self.DBInterface(), msg, target_chat)
            # print "[%s: %s] %s" % (msg.Chat.FriendlyName,
            #                        msg.FromHandle,
            #                        msg.Body)
            #print msg
        return

    # utility methods
    def addChat(self, chat):
        """
        chat is a SkypeChat instance.
        """
        verbose_print("try to add chat")
        # here, we need to check the chat has been created on DB or not?
        (room_name, topic_name) = parseChatName(chat.FriendlyName)
        verbose_print("%s/room_name, topic_name => %s, %s"
                      % (chat.FriendlyName, room_name, topic_name))
        chat_candidates = self.DBInterface().findChatFromName(room_name)
        verbose_print("chat_candidates => %s" % (chat_candidates))
        new = None
        if len(chat_candidates) == 0: # no candidates, we need to create it
            new = TiffanyChatRoom(self.DBInterface(), chat)
        else:                   # we already have it, create it from DB
            if len(chat_candidates) != 1:
                warn_print("more than one candidates... it may be a bug")
            chat_data = chat_candidates[0]
            new = buildChatRoomFromDBInstance(self.DBInterface(),
                                              self.skype(),
                                              chat_data,
                                              topic = topic_name)
        self._chats.append(new)
        new.inviteFriends(self.skype())
        return new
    
    # accessors
    def chats(self):
        return self._chats

    def skype(self):
        return self._skype

    def DBInterface(self):
        return self._di
    
    def findChat(self, chat):
        """
        find TiffanyChatRoom matching chat.
        chat is an object of skype.chat.Chat.
        """
        return self.chats()[[c.chat() for c in self.chats()].index(chat)]
    
    
class TiffanyChatRoom(object):
    """
    TiffanyChatRoom is a class to represent a chat room.
    In tiffany model, chat is composed of only-one topic and topic is
    composed of messages.
    
    This class can be serialized into DB.
    """
    _chat = None                # SkypeChat instance
    _current_topic = None
    _db_instance = None         # db.ChatData instance
    
    def __init__(self, di, chat, db_instance = None, current_topic = None):
        """
        skype is an instance of TiffanySkype and chat
        is an instance of SkypeChat.
        """
        verbose_print("creating TiffanyChatRoom/%s" % (chat))
        self._chat = chat
        self._current_topic = current_topic
        (room_name, topic_name) = parseChatName(chat.FriendlyName)
        if not db_instance:
            # if no db_instance is specified,
            # create db_instance and add it into DB.
            self._db_instance = ChatData(room_name)
            di.add(self.DBInstance())
        else:
            self._db_instance = db_instance
        
        if self.DBInstance().room_name == "":
            self.invokeChatHelp()
        if topic_name == "":
            self.invokeTopicHelp()
        else:
            # create topic
            topic_datum = di.findTopicFromNameAndRoomID(topic_name,
                                                        self.DBInstance().getID())
            if topic_datum:
                self._current_topic = buildChatTopicFromDBInstance(di,
                                                                   topic_datum[0])
            else:
                self._current_topic = TiffanyChatTopic(di, topic_name,
                                                       chat = self)
        # here we need to create topic?
        self.verifyTopic()
        return

    def changeRoom(self, di, room_name):
        """
        change the name of room.
        if chat room has a topic already, send an email to ML.
        """
        verbose_print("change room!")
        if self.currentTopic() and self.DBInstance():
            room_id = self.DBInstance().id
            topic_id = self.currentTopic().DBInstance().id
            di.sendMail(room_id, topic_id)
        # change FriendlyName
        friendly_name = ""
        if self.currentTopic():
            friendly_name = buildChatName(room_name,
                                          self.currentTopic().DBInstance().topic_name)
        else:
            friendly_name = buildChatName(room_name, "")
        self._chat.Topic = friendly_name
        self._db_instance = None
        self.__init__(di, self._chat, current_topic = self.currentTopic())
        return
    
    def changeTopic(self, di, topic_name):
        """
        change the current topic.
        if chat room has a topic already, send an email to ML and
        create new one.
        """
        verbose_print("change topic!")
        if self.currentTopic():
            room_id = self.DBInstance().id
            topic_id = self.currentTopic().DBInstance().id
            di.sendMail(room_id, topic_id)
        self._current_topic = TiffanyChatTopic(di, topic = topic_name,
                                               chat = self)
        # change room name
        room_name = buildChatName(self.DBInstance().room_name,
                                  self.currentTopic().DBInstance().topic_name)
        #verbose_print("topic => %s" % (self._chat.Topic))
        self._chat.Topic = room_name
        return
    
    def verifyTopic(self):
        """
        if you have not speciied topic, it invoke help message
        """
        if not self.currentTopic():
            self.invokeTopicHelp()
            return False
        return True
    def invokeChatHelp(self):
        msg = u"""
please specify chat room name by @@@room command like:
@@@room tech
"""
        self.sendMessage(msg)
        return
    def invokeTopicHelp(self):
        msg = u"""
please specify topic name by @@@topic command like:
@@@topic DB design
"""
        self.sendMessage(msg)
        return

    def closeTopic(self):
        "close the curent topic."
        if self.currentTopic():
            self.currentTopic().close()
            # prompt message
            self.sendMessage("""closed the topic [%s],
please continue the new topic!""" % (self.currentTopic().topicName()))
            return
        else:
            self.invokeTopicHelp()
            return
    # wrapper functions of SkypeChat
    def sendMessage(self, msg):
        """
        post a message to this chat room.
        msg is a unicode string.
        """
        self.chat().SendMessage(msg)
        return msg
    
    def addMembers(self, skype, members):
        "invite some members to this chat room"
        self.chat().AddMembers(*[skype.User(m)
                                 for m in members])
        return
    
    def inviteFriends(self, skype):
        """
        invite the friends not joined this chatroom.
        """
        debug_print("inviting friends in %s" % (USERS))
        current_members = [m.Handle for m in self.chat().Members]
        debug_print("current members => %s" % (current_members))
        invite_friends = set(USERS).difference(set(current_members))
        debug_print("iviting %s" % (invite_friends))
        if not len(invite_friends) == 0:
            self.addMembers(skype, invite_friends)
            self.sendMessage(u"%s are automatically invited"
                             % (list(invite_friends)))
        return
    
    def __eq__(self, other):
        "compare self and other using SkypeChat object"
        if isinstance(other, TiffanyChatRoom):
            return self.chat() == other.chat()
        else:
            return False
        
    def estimateTopicFromTitle(self):
        """
        estimate topic from the title of the chat room.
        the title is expected to satisfy config.CHAT_TITLE_FORMAT.
        if the estimation is failed, warning message is posted.
        
        ${topic} and ${room} are supported in CHAT_TITLE_FORMAT.
        """
        warn_print("estimateTopicFromTitle is not implemented")
        # ${topic} and ${room} is supported
        return
    
    # accessors
    def chat(self):
        return self._chat
    
    def DBInstance(self):
        return self._db_instance
    
    def currentTopic(self):
        return self._current_topic

# DB interface
def buildChatRoomFromDBInstance(di, skype, chat_data, topic = ""):
    """
    create an instance of TiffanyChatRoom from DB object, that is an instance
    of ChatData.
    """
    verbose_print("create TiffanyChatRoom from DBInstance")
    current_topic = None
    # try to find topic
    if not topic == "":
        # if topic is not an empty string,
        # we try to look it up from DB
        topic_datum = di.findTopicFromNameAndRoomID(topic, chat_data.getID())
        if topic_datum:
            # error check
            if len(topic_datum) > 1:
                warn_print("one more topics are finds! it may be a bug")
            current_topic = buildChatTopicFromDBInstance(di, topic_datum[0])
    chat_room_name = buildChatName(chat_data.room_name, topic)
    verbose_print("room_name => %s" % (chat_room_name))
    verbose_print("chats => %s" % [c.FriendlyName for c in skype.Chats])
    return TiffanyChatRoom(di, findChatFromSkype(skype, chat_room_name)[0],
                           db_instance = chat_data,
                           current_topic = current_topic)

class TiffanyChatTopic(object):
    """
    TiffanyChatTopic is just a container of string to represent the topic
    of the chat room.

    This class can be serialized into DB.
    """
    _topic_name = ""
    _db_instance = None         # instance of db.TopicData
    
    def __init__(self, di, topic, chat = None,
                 db_instance = None, chat_id = None):
        self._topic_name = topic
        if not db_instance:
            # if no db_instance is specified,
            # create db_instance and add it into DB.
            # need room_id.
            if chat_id:
                self._db_instance = TopicData(topic, chat_id)
            elif chat:
                self._db_instance = TopicData(topic, chat.DBInstance().id)
            else:
                raise ChatMissed("you need to specify chat or chat_id")
            di.add(self._db_instance)
        else:
            self._db_instance = db_instance
        return
    
    def close(self):
        """
        close a topic and send the messages to ML
        """
        warn_print("close method is not implemented")
        return

    # accessors
    def topicName(self):
        return self._topic_name

    def DBInstance(self):
        return self._db_instance
    
def buildChatTopicFromDBInstance(di, topic_data):
    """
    create an instance of TiffanyChatTopic from a db.TopicData instance.
    """
    room_id = topic_data.getRoomID()
    topic_name = topic_data.getTopicName()
    return TiffanyChatTopic(di, topic_name,
                            db_instance = topic_data,
                            chat_id = room_id)
