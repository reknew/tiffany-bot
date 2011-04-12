COLORS = {
    'clear': '\033[0m',
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'purple': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m'
}

def string_with_color(string, color):
    "add escape sequence to colorize string"
    clear_key = COLORS["clear"]
    color_key = COLORS[color]
    return color_key + string + clear_key

def warn_print(string):
    "print string in yellow"
    print string_with_color("[warn] " + string, "yellow")
    return
 
def debug_print(string):
    "print string in cyan"
    print string_with_color("[debug] " + string, "cyan")
    return

def verbose_print(string):
    "print string in purple"
    print string_with_color("[verbose] " + string, "purple")
    return
