#!/usr/bin/env python

"""This script runs on Gatekeeper server that receives TCP requests from Client and routes requests to Trusted Host."""

import configparser
import socket
import re
import pickle
import mysql.connector
from mysql.connector import errorcode

config = configparser.ConfigParser()
config.read('config.ini')


# initialize TCP socket connection on Gatekeeper and Trusted Host server
# reference: https://www.geeksforgeeks.org/socket-programming-python/
def initialize_socket():
    listening_socket = socket.socket()
    print("Listening Socket successfully created")

    port = int(config['GatekeeperServer']['Port'])
    listening_socket.bind(('', port))
    print("listening socket binded to %s" % port)

    listening_socket.listen(1)
    print("socket is listening")

    sending_socket = socket.socket()
    print("Sending Socket successfully created")

    host = config['ProxyServer']['Host']
    port = int(config['ProxyServer']['Port'])
    sending_socket.connect((host, port))
    print("sending socket connected to %s" % host)

    return listening_socket, sending_socket


def validate_sql_cmd(cmd):
    insert_validator = r"INSERT\sINTO\s[a-zA-Z]+\sVALUES\s\([0-9]+,[0-9]+,[0-9]+,'[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,3})?'\);"
    select_validator = r"SELECT\s\*\sFROM\s[a-zA-Z]+\sWHERE\s[a-zA-Z]+_[a-zA-Z]+\s=\s[0-9]+"
    delete_validator = r"DELETE\sFROM\s[a-zA-Z]+;"
    cmd_type = cmd.split()[0].lower()
    if cmd_type == "insert":
        return re.search(insert_validator, cmd)
    elif cmd_type == "select":
        return re.search(select_validator, cmd)
    elif cmd_type == "delete":
        return re.search(delete_validator, cmd)
    else:
        return None


def main():
    listening_socket, sending_socket = initialize_socket()

    # Establish connection with client.
    c, addr = listening_socket.accept()
    print('Got connection from', addr)

    while True:
        data = c.recv(2048)
        if not data:
            break

        req = pickle.loads(data)
        cmd = req['command']

        if validate_sql_cmd(cmd):
            sending_socket.send(data)
            print('sending command ' + cmd + ' to trusted host\n')
            sending_socket.recv(2048)
            response = 'request completed'
            c.send(response.encode())
        else:
            error_message = "request invalid: " + cmd
            print(error_message)
            c.send(error_message.encode())
            break

    # Close the connection with the client
    c.close()
    listening_socket.close()
    sending_socket.close()
    print("socket is closed on gatekeeper server")


if __name__ == '__main__':
    main()
