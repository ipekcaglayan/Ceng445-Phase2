import sqlite3
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock

import json
from json import JSONDecodeError
from Database import Database
from User import User
import datetime

# { "command": "CREATE_USER", "id": 12345, "description": "Just a sample item"}

# CREATE_USER ipek 1234


class Server:
    port = 2022
    mutex = Lock()

    def __init__(self):
        self.connected_clients = 0
        sql_db = sqlite3.connect('new_database.db', check_same_thread=False)
        self.db = Database(sql_db, sql_db.cursor())

    def user_does_request(self, request, **kwargs):
        user_id = int(kwargs['user_id'])
        user = User.users_dict[user_id]

        if request == 2:  # Upload Photo
            photo_id = user.uploadPhoto(kwargs['path'])
            return photo_id

        elif request == 3:  # Add Tag to Photo
            ph_id = int(kwargs['ph_id'])
            tag = kwargs['tag']
            success = user.addTagToPhoto(ph_id, tag)
            if success:
                return f"Tag: {tag} is added to Photo(id={ph_id})"

        elif request == 4:  # Remove Tag from Photo
            ph_id = int(kwargs['ph_id'])
            tag = kwargs['tag']
            msg = user.removeTagFromPhoto(ph_id, tag)
            return msg

        elif request == 5:  # Set Loc of Photo
            ph_id = int(kwargs['ph_id'])
            long = eval(kwargs['long'])
            latt = eval(kwargs['latt'])
            msg = user.setLocationOfPhoto(ph_id, long, latt)
            return msg

        elif request == 6:  # Remove Loc from Photo
            ph_id = int(kwargs['ph_id'])
            msg = user.removeLocationFromPhoto(ph_id)
            return msg
        elif request == 7:  # Set Datetime of Photo
            ph_id = int(kwargs['ph_id'])
            yymmdd = kwargs['yymmdd']
            saat = kwargs['saat']
            yymmdd_list = [int(x) for x in yymmdd.split(":")]
            saat_list = [int(x) for x in saat.split(":")]
            mydatetime = datetime.datetime(*(yymmdd_list + saat_list))

            success = user.setDatetimeOfPhoto(ph_id, mydatetime)
            if success:
                return f'Datetime of Photo(id={ph_id}) is set to {yymmdd} {saat}'


    def request_handler(self, request_handler_socket):

        request = json.loads(request_handler_socket.recv(1024).decode('utf8'))
        while request:
            request_type = request['command']
            if request_type == '0':  # CREATE_USER
                user = User(request['username'], request['password'], self.db)
                user_id = str(user.id)
                request_handler_socket.send(str.encode(user_id))

            elif request_type == '1':  # LOGIN
                username = request['username']
                password = request['password']
                user_list = list(self.db.curs.execute(
                    f'SELECT user_id, password FROM Users where username="{username}"'))

                user_id = str(-1)  # assume credentials are wrong before checking

                if len(user_list) > 0:  # there exists user with the given username
                    correct_password = user_list[0][1]
                    if correct_password == password:
                        user_id = str(user_list[0][0])  # if given password matches with the correct password
                        # client will be informed with the correct user_id
                        # if not user_id will be sent as -1 which means password or username is incorrect.

                request_handler_socket.send(str.encode(user_id))

            elif request_type == '2':  # UPLOAD_PHOTO
                ph_id = str(self.user_does_request(2, **request))
                request_handler_socket.send(str.encode(ph_id))

            elif request_type == '3':  # ADD_TAG_TO_PHOTO
                msg = self.user_does_request(3, **request)
                request_handler_socket.send(str.encode(msg))

            elif request_type == '4':  # REMOVE_TAG_FROM_PHOTO
                msg = self.user_does_request(4, **request)
                request_handler_socket.send(str.encode(msg))

            elif request_type == '5':  # SET_LOC_OF_PHOTO
                msg = self.user_does_request(5, **request)
                request_handler_socket.send(str.encode(msg))

            elif request_type == '6':  # REMOVE_LOC_FROM_PHOTO
                msg = self.user_does_request(6, **request)
                request_handler_socket.send(str.encode(msg))

            elif request_type == '7':  # SET_DATETIME_OF_PHOTO
                msg = self.user_does_request(7, **request)
                request_handler_socket.send(str.encode(msg))

            request = json.loads(request_handler_socket.recv(1024).decode('utf8'))

    def start_server(self):
        try:
            request_handler_socket = socket(AF_INET, SOCK_STREAM)
            request_handler_socket.bind(('', self.port))
            request_handler_socket.listen()
        except Exception as e:
            print(f"Unable to start to server. An error occurred:{e}")
            return
        while True:
            conn, peer = request_handler_socket.accept()
            self.connected_clients += 1
            req_handler = Thread(target=self.request_handler, args=(conn,))
            req_handler.start()
            print("New client -> thread : ", req_handler.ident)

    def start(self):

        start_server = Thread(target=self.start_server)
        start_server.start()


if __name__ == "__main__":
    server = Server()
    server.start()
