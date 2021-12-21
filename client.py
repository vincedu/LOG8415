#!/usr/bin/env python

"""This script runs on local machine that send TCP requests to AWS instances."""

import configparser
import socket
import pickle
import time

config = configparser.ConfigParser()
config.read('config.ini')

insert_cmd = 'INSERT INTO inventory VALUES '
select_cmd = 'SELECT * FROM inventory WHERE inventory_id = '


# establish socket connection with Proxy server to send TCP requests
# reference: https://www.geeksforgeeks.org/socket-programming-python/
def initialize_socket(host, port):
    s = socket.socket()
    print("Socket successfully created")

    s.connect((host, port))
    print("socket connected to %s" % (host))

    return s


def send_write_requests(socket):
    f = open('sakila-data-inventory-300.txt', 'r')
    for line in f:
        line = line.strip('\n')
        cmd = insert_cmd + line
        req = {'type': 'insert', 'command': cmd}
        socket.send(pickle.dumps(req))
        socket.recv(2048)
    f.close()


def send_read_requests(socket, mode):
    nb_rows = 300
    for i in range(1, nb_rows + 1):
        cmd = select_cmd + str(i)
        req = {'type': 'select', 'command': cmd, 'mode': mode}
        socket.send(pickle.dumps(req))
        socket.recv(2048)

def clean_database(socket):
    cmd = 'DELETE FROM inventory;'
    req = {'type': 'delete', 'command': cmd}
    socket.send(pickle.dumps(req))
    socket.recv(2048)

def main():
    # performance measurement for proxy server
    host = config['ProxyServer']['Host']
    port = int(config['ProxyServer']['Port'])
    proxy_socket = initialize_socket(host, port)

    # mode 0 for direct hit, 1 for random, 2 for customized
    for mode in range(3):
        print("Requests to proxy server with mode " + str(mode) + " started")
        start = time.time()
        send_write_requests(proxy_socket)
        send_read_requests(proxy_socket, mode)
        request_time = time.time() - start
        print("Requests to proxy server with mode " + str(mode) + " completed in {:0.2f}ms".format(request_time))

        time.sleep(1)
        clean_database(proxy_socket)

    proxy_socket.close()
    print("proxy socket is closed on client")

    # performance measurement for gatekeeper server
    # host = config['GatekeeperServer']['Host']
    # port = int(config['GatekeeperServer']['Port'])
    # gatekeeper_socket = initialize_socket(host, port)
    #
    # for mode in range(3):
    #     print("Requests to gatekeeper server with mode " + str(mode) + " started")
    #     start = time.time()
    #     send_write_requests(gatekeeper_socket)
    #     send_read_requests(gatekeeper_socket, mode)
    #     request_time = time.time() - start
    #     print("Requests to gatekeeper server with mode " + str(mode) + " completed in {:0.2f}ms".format(request_time))
    #
    #     time.sleep(1)
    #     clean_database(gatekeeper_socket)
    #
    # gatekeeper_socket.close()
    # print("gatekeeper socket is closed on client")


if __name__ == '__main__':
    main()
