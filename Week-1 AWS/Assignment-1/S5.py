import cmd, sys
from turtle import *
import platform
import boto3

from boto3 import Session
ON_CONNECTION_SUCCESS_TEXT = "Welcome to the AWS S3 Storage Shell (S5) \nYou are now connected to your S3 storage"
ON_CONNECTION_FAIL_TEXT = "Welcome to the AWS S3 Storage Shell (S5)\nYou are could not be connected to your S3 storage\nPlease review procedures for authenticating your account on AWS S3"
running_platform = platform.system()


class S5Shell(cmd.Cmd):
    try:
        s3 = boto3.client('s3')
        # session = boto3.Session(profile_name='ymei')
        # dev_s3_client = session.client('s3')
        intro_text = ON_CONNECTION_SUCCESS_TEXT

    except:
        intro_text = ON_CONNECTION_FAIL_TEXT
        # sys.exit(0)
    intro = intro_text
    prompt = 'S5> '
    file = None

    # ----- basic turtle commands -----

    # ----- record and playback -----
    def do_record(self, arg):
        'Save future commands to filename:  RECORD rose.cmd'
        self.file = open(arg, 'w')
    def do_playback(self, arg):
        'Playback commands from a file:  PLAYBACK rose.cmd'
        self.close()
        with open(arg) as f:
            self.cmdqueue.extend(f.read().splitlines())

    def precmd(self, line):
        line = line.lower()
        if self.file and 'playback' not in line:
            print(line, file=self.file)
        return line
    def close(self):
        if self.file:
            self.file.close()
            self.file = None

    # ----- Customized S5 Functions -----
    def do_quit(self,arg):
        'Exit the S5 Shell'
        print('Thank you for using S5 Shell')
        sys.exit(0)
    def do_exit(self,arg):
        'Exit the S5 Shell'
        self.do_quit(arg)

def parse(arg):
    'Convert a series of zero or more numbers to an argument tuple'
    return tuple(map(int, arg.split()))

if __name__ == '__main__':
    S5Shell().cmdloop()