"""
this file provides some classes for Tiffany bot commands.
"""

from config import COMMAND_PREFIX
from error import *
from color import debug_print, warn_print, verbose_print

class TiffanyCommand(object):
    """
    superclass of the commands which tiffanybot recognizes.
    in subclass of it, you need to override __init__ and run method.
    """
    _command = ""
    _original_string = ""
    _arguments = []             # parsed arguments
    def __init__(self, command, original, args):
        """
        subclasses of TiffanyCommand are required to override __init__ method
        with 2 arguments. it means, in subclass constructor,
        there is need to call TIffanyCommand.__init__ method.
        """
        self._command = command
        self._arguments = args
        self._original_string = original
        return

    # accessors
    def command(self):
        return self._command

    def originalString(self):
        return self._original_string

    def commandArguments(self):
        return self._arguments
    
    def run(self, chat, di):
        raise NeedOverRide("you need to override run method")
    def help(self):
        return self.__doc__
    
class TiffanyNotCommand(TiffanyCommand):
    def __init__(self, original):
        TiffanyCommand.__init__(self, "", original, [])
        return
    def run(self, chat, di):
        verbose_print("nothing to do")
        return

class TiffanyNoCommand(TiffanyCommand):
    def __init__(self, original, args):
        TiffanyCommand.__init__(self, "", original, args)
        return
    def run(self, chat, di):
        chat.sendMessage("cannot find suitable command for %s"
                         % (self.originalString()))
        return

    
class TiffanyHelpCommand(TiffanyCommand):
    """
    help:
      print help of TiffanyBot
    """
    def __init__(self, original, args):
        TiffanyCommand.__init__(self, "help", original, args)
        return
    def run(self, chat, di):
        dummy_commands = [c("", []) for c in valid_commands]
        chat.sendMessage("""
prefix of commands => %s
supported commands => %s
%s
""" % (COMMAND_PREFIX, [c.command() for c in dummy_commands],
       "\n".join([c.help() for c in dummy_commands])))
        return

    
class TiffanyExitCommand(TiffanyCommand):
    """
    exit:
      tiffanybot exits from the current chatroom.
      tiffanybot sends ML summary before exiting from there.
    """
    def __init__(self, original, args):
        TiffanyCommand.__init__(self, "exit", original, args)
        return
    def run(self, chat, di):
        return

class TiffanyHelloCommand(TiffanyCommand):
    """
    hello:
      you can say hello to tiffanybot.
    """
    def __init__(self, original, args):
        TiffanyCommand.__init__(self, "hello", original, args)
        return
    def run(self, chat, di):
        chat.sendMessage("Hi, how are you?")
        return

class TiffanyTopicCommand(TiffanyCommand):
    """
    topic:
      you can specify topic name of chat room.
    """
    def __init__(self, original, args):
        TiffanyCommand.__init__(self, "topic", original, args)
        return
    def run(self, chat, di):
        chat.changeTopic(di, " ".join(self.commandArguments()))
        return

class TiffanyRoomCommand(TiffanyCommand):
    """
    room:
      you can specify topic name of chat room.
    """
    def __init__(self, original, args):
        TiffanyCommand.__init__(self, "room", original, args)
        return
    def run(self, chat, di):
        chat.changeRoom(di, " ".join(self.commandArguments()))
        return

    
valid_commands = [TiffanyExitCommand, TiffanyHelpCommand, TiffanyHelloCommand,
                  TiffanyTopicCommand, TiffanyRoomCommand]

def commandDispatch(command):
    """
    this function returns a subclass of TiffanyCommand according to 
    command string you specified.

    caller of commandDispatch needs to call run method of the returned
    TiffanyCommand object.
    """
    if not command.startswith(COMMAND_PREFIX):
        ret_command = TiffanyNotCommand(command)
        return ret_command
    else:
        # try to find suitable command
        (prefix, split, command_string) = command.partition(COMMAND_PREFIX)
        command_name = command_string.split()[0]
        command_args = command_string.split()[1:]
        commands_objs = [c(command, command_args) for c in valid_commands]
        commands_strings = [c.command() for c in commands_objs]
        debug_print("command_string => %s" % (commands_strings))
        if command_name in commands_strings:
            verbose_print("%s is found in valid_commands" % (command_name))
            proper_command = commands_objs[commands_strings.index(command_name)]
            return proper_command
        else:
            no_command = TiffanyNoCommand(command, command_args)
            return no_command

