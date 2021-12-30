import sqlite3
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock

import json
from json import JSONDecodeError
from Database import Database
from User import User
import datetime
from SharedPhotoLibrary import *

# { "command": "CREATE_USER", "id": 12345, "description": "Just a sample item"}

# CREATE_USER ipek 1234


class Server:
    port = 2022
    mutex = Lock()

    def __init__(self):
        self.connected_clients = 0
        sql_db = sqlite3.connect('database.db', check_same_thread=False)
        self.db = Database(sql_db, sql_db.cursor())

    def user_does_request(self, request, **kwargs):
        user_id = int(kwargs['user_id'])
        user = User.users_dict[user_id]

        if request == 2:  # Upload Photo
            print("I am here")
            photo_data = user.uploadPhoto(kwargs['path'], kwargs['encoded_img'])
            self.db.insert("Photos", ('ph_id', 'tags', 'location', 'datetime', 'encoded_img', 'user_id'), *photo_data)

            return photo_data[0]

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

        elif request == 8:  # Create Collection
            col_id = user.createCollection(kwargs['collection_name'])
            self.db.insert("Collections", ('col_id', 'col_name', 'owner_id'), col_id, kwargs['collection_name'], user.id)
            return str(col_id)

        elif request == 9:  # Create View
            view_id = user.createView(kwargs['view_name'])
            return str(view_id)

    def create_library_objects(self):

        # create users from database
        users_list = list(self.db.curs.execute(f'SELECT user_id, username, password from Users'))
        users_dict = {}
        user_counter = 0
        for user_tuple in users_list:
            u = User(user_tuple[1], user_tuple[2])
            u.id = user_tuple[0]
            if u.id > user_counter:
                user_counter = u.id
            users_dict[u.id] = u

        User.users_dict = users_dict
        User.counter = user_counter + 1

        # create collections from database
        col_list = list(self.db.curs.execute(f'SELECT col_id, col_name, owner_id from Collections'))
        collections_dict = {}
        col_counter = 0

        for col_tuple in col_list:
            owner = User.users_dict[col_tuple[2]]
            col = Collection(col_tuple[1], owner)
            col.id = col_tuple[0]
            if col.id > col_counter:
                col_counter = col.id
            collections_dict[col.id] = col

        Collection.collections_dict = collections_dict
        Collection.counter = col_counter+1

    def request_handler(self, request_handler_socket):
        client_user_id = -1
        request = json.loads(request_handler_socket.recv(1024).decode('utf8'))
        while True:
            request_type = request['command']
            request['user_id'] = client_user_id

            if request_type == '0':  # CREATE_USER
                user = User(request['username'], request['password'])
                user_id = str(user.id)
                self.db.insert("Users", ('user_id', 'username', 'password'), user.id, user.username, user.password)

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
                        client_user_id = user_id
                        # client will be informed with the correct user_id
                        # if not user_id will be sent as -1 which means password or username is incorrect.

                request_handler_socket.send(str.encode(user_id))

            else:
                req_type = int(request_type)
                message = self.user_does_request(req_type, **request)
                request_handler_socket.send(str.encode(message))

            # elif request_type == '2':  # UPLOAD_PHOTO
            #     ph_id = str(self.user_does_request(2, **request))
            #     request_handler_socket.send(str.encode(ph_id))
            #
            # elif request_type == '3':  # ADD_TAG_TO_PHOTO
            #     msg = self.user_does_request(3, **request)
            #     request_handler_socket.send(str.encode(msg))
            #
            # elif request_type == '4':  # REMOVE_TAG_FROM_PHOTO
            #     msg = self.user_does_request(4, **request)
            #     request_handler_socket.send(str.encode(msg))
            #
            # elif request_type == '5':  # SET_LOC_OF_PHOTO
            #     msg = self.user_does_request(5, **request)
            #     request_handler_socket.send(str.encode(msg))
            #
            # elif request_type == '6':  # REMOVE_LOC_FROM_PHOTO
            #     msg = self.user_does_request(6, **request)
            #     request_handler_socket.send(str.encode(msg))
            #
            # elif request_type == '7':  # SET_DATETIME_OF_PHOTO
            #     msg = self.user_does_request(7, **request)
            #     request_handler_socket.send(str.encode(msg))
            #
            # elif request_type == '8':  # CREATE_COLLECTION
            #     col_id = str(self.user_does_request(8, **request))
            #     request_handler_socket.send(str.encode(col_id))
            #
            # elif request_type == '9':  # CREATE_VIEW
            #     view_id = str(self.user_does_request(9, **request))
            #     request_handler_socket.send(str.encode(view_id))

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
    server.create_library_objects()
    server.start()
