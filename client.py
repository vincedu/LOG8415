#!/usr/bin/env python

"""This script runs on local machine that send TCP requests to AWS instances."""

import configparser
import socket
import pickle
import time
import subprocess
import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

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
    f = open('data/sakila-data-inventory-300.txt', 'r')
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


def get_powerapi_results(mode):
    # get power API results from master node
    subprocess.run(['scp', '-i', 'cloud.pem',
                    'ubuntu@ec2-54-86-214-63.compute-1.amazonaws.com:/home/ubuntu/powerapi-cli-4.2.1/powerapi_results.txt',
                    '/Users/vincedu/Downloads/cloud/final_project/powerapi_results/master_' + mode + '.txt'])

    # get power API results from slave nodes
    subprocess.run(['scp', '-i', 'cloud.pem',
                    'ubuntu@ec2-3-95-189-238.compute-1.amazonaws.com:/home/ubuntu/powerapi-cli-4.2.1/powerapi_results.txt',
                    '/Users/vincedu/Downloads/cloud/final_project/powerapi_results/slave1_' + mode + '.txt'])

    subprocess.run(['scp', '-i', 'cloud.pem',
                    'ubuntu@ec2-184-72-112-215.compute-1.amazonaws.com:/home/ubuntu/powerapi-cli-4.2.1/powerapi_results.txt',
                    '/Users/vincedu/Downloads/cloud/final_project/powerapi_results/slave2_' + mode + '.txt'])

    subprocess.run(['scp', '-i', 'cloud.pem',
                    'ubuntu@ec2-44-201-114-61.compute-1.amazonaws.com:/home/ubuntu/powerapi-cli-4.2.1/powerapi_results.txt',
                    '/Users/vincedu/Downloads/cloud/final_project/powerapi_results/slave3_' + mode + '.txt'])


def plot_energy_consumption():
    directory = '/Users/vincedu/Downloads/cloud/final_project/powerapi_results/'
    modes = {
        "0": "direct",
        "1": "random",
        "2": "customized"
    }
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        # checking if it is a file
        if filename.endswith('.txt') and os.path.isfile(f):
            file = open(f, "r")
            timestamps, powers = [], []
            for line in file:
                timestamp = int(line.split(';')[1].split('=')[1][-6:])
                timestamps.append(timestamp)
                power = int(float((line.split(';')[4].split('=')[1].split(' ')[0])))
                powers.append(power)

            xpoints = np.array(timestamps)
            ypoints = np.array(powers)
            plt.plot(xpoints, ypoints)

            node = filename.split('_')[0]
            pattern = filename.split('_')[1]
            mode_code = filename.split('_')[2].split('.')[0]
            mode = modes[mode_code]
            title = 'Energy consumption of ' + node + ' using ' + pattern + ' pattern with mode ' + mode

            plt.title(title)
            plt.xlabel('time')
            plt.ylabel('energy consumption')
            plt.savefig(directory + 'plots/' + filename.split('.')[0] + '.png')


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
        time.sleep(0.1)
        send_read_requests(proxy_socket, mode)
        request_time = time.time() - start
        print("Requests to proxy server with mode " + str(mode) + " completed in {:0.2f}ms".format(request_time))
        time.sleep(0.1)

        clean_database(proxy_socket)
        proxy_mode = 'proxy_' + str(mode)
        get_powerapi_results(proxy_mode)

    proxy_socket.close()
    print("proxy socket is closed on client")

    # performance measurement for gatekeeper server

    host = config['GatekeeperServer']['Host']
    port = int(config['GatekeeperServer']['Port'])
    gatekeeper_socket = initialize_socket(host, port)

    for mode in range(3):
        print("Requests to gatekeeper server with mode " + str(mode) + " started")
        start = time.time()
        send_write_requests(gatekeeper_socket)
        time.sleep(0.1)
        send_read_requests(gatekeeper_socket, mode)
        request_time = time.time() - start
        print("Requests to gatekeeper server with mode " + str(mode) + " completed in {:0.2f}ms".format(request_time))
        time.sleep(0.1)

        clean_database(gatekeeper_socket)
        proxy_mode = 'gatekeeper_' + str(mode)
        get_powerapi_results(proxy_mode)

    gatekeeper_socket.close()
    print("gatekeeper socket is closed on client")

    plot_energy_consumption()


if __name__ == '__main__':
    main()
