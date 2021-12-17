#!/usr/bin/env python

"""This script runs on local machine that send TCP requests to AWS instances."""

import configparser
import socket
import time

config = configparser.ConfigParser()
config.read('config.ini')

insert_cmd = 'INSERT INTO inventory VALUES '
select_cmd = 'SELECT * FROM inventory WHERE inventory_id = '

# establish socket connection with Proxy server to send TCP requests
# reference: https://www.geeksforgeeks.org/socket-programming-python/
def initialize_socket():
    s = socket.socket()
    print("Socket successfully created")

    host = config['ProxyServer']['Host']
    port = int(config['ProxyServer']['Port'])
    s.connect((host, port))
    print ("socket connected to %s" %(host))

    return s

def send_write_requests(socket):
    f = open('sakila-data-inventory.txt', 'r')
    for line in f:
        cmd = insert_cmd + line
        socket.send(cmd.encode())
    f.close()

# def send_read_requests():


def main():
    socket = initialize_socket()
    send_write_requests(socket)
    time.sleep(0.5)


if __name__ == '__main__':
    main()
