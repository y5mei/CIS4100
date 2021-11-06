from termcolor import colored
from colorama import init

init()

def try_catch(func):
    def wrapper(*args, **kw):
        # print('call %s():' % func.__name__)
        try:
            func(*args)
            return 0
        except Exception as e:
            print(colored(e,"red"))
            return 1
    return wrapper