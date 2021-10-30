import platform
import sys
import os
from termcolor import colored
from colorama import init
from shlex import split as shlexsplit
# use Colorama to make Termcolor work on Windows too
# ref： https://pypi.org/project/colorama/
from Automate import print_gcp_instance_list, run_automate, automate_create, list_all_gcp_instance, short_command, \
    delete_all_gcp_instance

init()


def do_quit(*args):
    endingStr = "Exiting the S5 Shell Program Now...\n"
    endingStr+= "Thank you for using S5, See you next time!"
    print(colored(endingStr,"blue"))
    sys.exit(0)



dispatch = {
    "quit": do_quit,
    "exit": do_quit,
    "q": do_quit,
    "Q": do_quit,
    "automate_print": run_automate,
    "gcreate":automate_create,
    "glist": list_all_gcp_instance,
    "gdelete":delete_all_gcp_instance,
}



if __name__ == '__main__':
    print(colored("Welcome to S5 Shell","green"))
    while True:

        user_input = input("S5> ")

        # Requirment 3 1) if the input command is not a required function,
        # call the os.sys() method to use the system shell to handle it

        if len(user_input.split(" ", 1)) > 1:  # if input contains argument
            command, arg = user_input.split(" ", 1)[0], user_input.split(" ", 1)[1]
        else:
            command, arg = user_input.split(" ", 1)[0], ""  # if input does not contains argument, argument is ""

        if command not in set(dispatch.keys()):
            # if the command is not a controlled method, pass it directly to the system shell
            try:
                if os.system(user_input) != 0:
                    raise Exception("Can not Run this Command")
            except BaseException as e:
                # print("S5 Error: Please see the error message below:")
                print(colored(e, "red"))
        # if we have a def of the command already, then dispatch it from the dict.
        else:
            if command in ["q", "quit", "exit", "Q"]:
                dispatch["q"](arg)
            # if it is available, then we dispatch the command
            try:
                arg = shlexsplit(arg) # need to use shellsplit to split the input into arguments
                status_val = dispatch[command](*arg)
            except BaseException as e:
                print(colored(e, "red"))
                print(colored("Please double check your arguments: " + arg, "red"))