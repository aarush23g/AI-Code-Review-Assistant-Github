import os


def ping_host(host):
    return os.system("ping " + host)