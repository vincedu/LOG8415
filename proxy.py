#!/usr/bin/env python

"""This script runs on Proxy server that receives TCP requests from Client and routes requests to MySQL cluster."""

import configparser
import socket
import mysql.connector
from mysql.connector import errorcode
from random import randint
import pickle
import ping3

config = configparser.ConfigParser()
config.read('config.ini')

numberOfSlaves = int(config['ClusterSetting']['NumberOfSlaves'])


# initialize TCP socket connection on Proxy server to listen to incoming requests
# reference: https://www.geeksforgeeks.org/socket-programming-python/
def initialize_socket():
    s = socket.socket()
    print("Socket successfully created")

    port = int(config['ProxyServer']['Port'])
    s.bind(('', port))
    print("socket binded to %s" % (port))

    s.listen(1)
    print("socket is listening")

    return s


def execute_sql_command(server_name, cmd):
    try:
        cnx = mysql.connector.connect(user='proxy', password='1234',
                                      host=config[server_name]['Host'],
                                      database='tp3')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    cursor = cnx.cursor()
    cursor.execute(cmd)
    cmd_type = cmd.split()[0].lower()
    if cmd_type == "insert" or cmd_type == "delete":
        cnx.commit()
    elif cmd_type == "select":
        print("query result: ")
        print(cursor.fetchall())


def direct_hit(cmd):
    execute_sql_command('Master', cmd)
    print("direct hit, request handled by Master\n")


def random(cmd):
    rand_num = randint(1, numberOfSlaves)
    rand_slave = 'Slave' + str(rand_num)
    execute_sql_command(rand_slave, cmd)
    print("random, request handled by " + rand_slave + "\n")


def customized(cmd):
    server_name = find_server_with_min_ping()
    execute_sql_command(server_name, cmd)
    print("customized, request handled by " + server_name + "\n")


def find_server_with_min_ping():
    ping_times = []
    host = config['Master']['Host']
    ping_time = ping(host)
    ping_times.append(ping_time)

    for i in range(1, numberOfSlaves + 1):
        host_name = 'Slave' + str(i)
        host = config[host_name]['Host']
        ping_time = ping(host)
        ping_times.append(ping_time)

    min_ping_time = min(ping_times)
    min_index = ping_times.index(min_ping_time)
    if min_index == 0:
        return 'Master'
    return 'Slave' + str(min_index)


def ping(host):
    try:
        ping_time = ping3.ping(host)
    except ping3.errors.HostUnknown:  # Specific error is catched.
        print("Host unknown error raised.")
    except ping3.errors.PingError:  # All ping3 errors are subclasses of `PingError`.
        print("A ping error raised.")

    return ping_time


def main():
    s = initialize_socket()

    # Establish connection with client.
    c, addr = s.accept()
    print('Got connection from', addr)

    while True:
        req = pickle.loads(c.recv(2048))
        if not req:
            break

        cmd = req['command']
        cmd_type = req['type']
        print(cmd)

        if cmd_type == "insert":
            direct_hit(cmd)
        elif cmd_type == "select":
            # mode 0 for direct hit, 1 for random, 2 for customized
            mode = req['mode']
            if mode == 0:
                direct_hit(cmd)
            elif mode == 1:
                random(cmd)
            elif mode == 2:
                customized(cmd)
        elif cmd_type == 'delete':
            direct_hit(cmd)
        response = 'request completed'
        c.send(response.encode())

    # Close the connection with the client
    c.close()
    s.close()


if __name__ == '__main__':
    main()
