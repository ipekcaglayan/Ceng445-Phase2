from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import json
from json import JSONDecodeError
import base64


class Client:
    port = 2022
    address = '127.0.0.1'

    def __init__(self):
        self.logged_in_user_id = -1
        self.added_photos_ids = list()
        self.created_collections = list()
        self.created_views = list()

    def is_user_logged_in(self):
        if self.logged_in_user_id < 0:
            print("This request requires login. Please login.")
        return self.logged_in_user_id

    def connect(self):
        request_socket = socket(AF_INET, SOCK_STREAM)
        request_socket.connect((self.address, self.port))

        while True:
            is_json = False
            request = input('\nRequest: ')
            try:
                request = json.loads(request)
                request_type = request['command']
                is_json = True
            except JSONDecodeError:
                request_type = request.split(" ")[0]

            if request_type == "CREATE_USER" or request_type == "0":
                if not is_json:
                    params = request.split(" ")
                    username = params[1]
                    password = params[2]
                    request = {'command': '0', 'username': username, 'password': password}

                request_socket.send(str.encode(json.dumps(request)))
                user_id = int(request_socket.recv(1024).decode('utf8'))
                if user_id >= 0:  # Server returned id of created user which means user creation is successful.
                    print(f"User({request['username']}) created successfully.")

            elif request_type == "LOGIN" or request_type == "1":
                if not is_json:
                    params = request.split(" ")
                    username = params[1]
                    password = params[2]
                    request = {'command': '1', 'username': username, 'password': password}

                request_socket.send(str.encode(json.dumps(request)))
                user_id = int(request_socket.recv(1024).decode('utf8'))
                if user_id >= 0:  # Server returned id of logged in user which means user login is successful.
                    self.logged_in_user_id = user_id
                    print(f"User({request['username']}) is logged in.")
                else:  # that means server returned -1 as user_id since given username or pswd is incorrect.
                    print("You have entered the wrong username or password.")

            elif request_type == "UPLOAD_PHOTO" or request_type == "2":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        path = params[1]
                        request = {'command': '2', 'path': path}
                    path = request['path']
                    with open(path, 'rb') as img_file:
                        image_read = img_file.read()
                        image_64_encode = base64.encodebytes(image_read)

                    # request_socket.send(str.encode(json.dumps(request)))
                    request_socket.send(image_64_encode)

                    ph_id = int(request_socket.recv(1024).decode('utf8'))
                    print(f"Photo(id={ph_id}) is uploaded.")
                    self.added_photos_ids.append(ph_id)

            elif request_type == "ADD_TAG_TO_PHOTO" or request_type == "3":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        ph_id = params[1]
                        tag = params[2]
                        if int(ph_id) not in self.added_photos_ids:
                            print("Photo with given id does not exist")
                            continue
                        request = {'command': '3', 'ph_id': ph_id, 'tag': tag}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "REMOVE_TAG_FROM_PHOTO" or request_type == "4":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        ph_id = params[1]
                        tag = params[2]
                        if int(ph_id) not in self.added_photos_ids:
                            print("Photo with given id does not exist")
                            continue
                        request = {'command': '4', 'ph_id': ph_id, 'tag': tag}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "SET_LOC_OF_PHOTO" or request_type == "5":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        ph_id = params[1]
                        long = params[2]
                        latt = params[3]
                        if int(ph_id) not in self.added_photos_ids:
                            print("Photo with given id does not exist")
                            continue
                        request = {'command': '5', 'ph_id': ph_id, 'long': long, 'latt': latt}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "REMOVE_LOC_FROM_PHOTO" or request_type == "6":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        ph_id = params[1]
                        if int(ph_id) not in self.added_photos_ids:
                            print("Photo with given id does not exist")
                            continue
                        request = {'command': '6', 'ph_id': ph_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "SET_DATETIME_OF_PHOTO" or request_type == "7":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        ph_id = params[1]
                        yymmdd = params[2]
                        saat = params[3]
                        if int(ph_id) not in self.added_photos_ids:
                            print("Photo with given id does not exist")
                            continue
                        request = {'command': '7', 'ph_id': ph_id, 'yymmdd': yymmdd, 'saat': saat}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "CREATE_COLLECTION" or request_type == "8":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        collection_name = params[1]
                        request = {'command': '8', 'collection_name': collection_name}
                    request_socket.send(str.encode(json.dumps(request)))
                    col_id = int(request_socket.recv(1024).decode('utf8'))
                    self.created_collections.append(col_id)
                    print(f"Collection(name={request['collection_name']}) created successfully.")

            elif request_type == "CREATE_VIEW" or request_type == "9":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        view_name = params[1]
                        request = {'command': '9', 'view_name': view_name}
                    request_socket.send(str.encode(json.dumps(request)))
                    view_id = int(request_socket.recv(1024).decode('utf8'))
                    self.created_views.append(view_id)
                    print(f"View(name={request['view_name']}) created successfully.")

            if request_type == "LOGOUT":
                self.logged_in_user_id = -1

            if request == 'exit':
                print('Bye')
                return


if __name__ == "__main__":
    client = Client()
    client.connect()
