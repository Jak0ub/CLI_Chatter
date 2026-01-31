import sys, subprocess
import os, platform, time


def cli_clear():
    os.system("clear")

def check():
    if platform.system() == "Windows":
        print("Only for Unix")
        sys.exit()
def init():
    os.system("mkdir hosting")
    os.chdir("hosting")
    server = subprocess.Popen(["python3", "-m", "http.server"], stderr=open("log.txt", "w")) #Start server and redirect stderr stream to log file
    return server

def clean(server):
    server.kill()
    os.chdir("..")
    os.system("rm -rf hosting") #No logs!
    return 1


if __name__ == "__main__":
    check()
    server = init()
    cli_clear()
    time.sleep(5)
    if clean(server) == 1:
        print("server stopped successfully")
    else:
        print("error occured")

