from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import json
from json import JSONDecodeError
import base64
import math


class Client:
    port = 2022
    notification_port = 2028
    address = '127.0.0.1'

    def __init__(self):
        self.logged_in_user_id = -1
        self.added_photos_ids = list()
        self.created_collections = list()
        self.created_views = list()
        self.server_closed = False

    def notification(self, user_id):

        notification_socket = socket(AF_INET, SOCK_STREAM)
        notification_socket.connect((self.address, self.notification_port))
        notification_socket.send(str.encode(str(user_id)))
        notification_msg = notification_socket.recv(1024).decode('utf8')
        while True:
            if notification_msg == "":
                print('Server closed')
                self.server_closed = True
                return

            if notification_msg == "exit":
                return
            print(f'\n notification received by {user_id}: {notification_msg} \nRequest:')
            notification_msg = notification_socket.recv(1024).decode('utf8')


    def is_user_logged_in(self):
        if self.logged_in_user_id < 0:
            print("This request requires login. Please login.")
        return self.logged_in_user_id

    def connect(self):
        request_socket = socket(AF_INET, SOCK_STREAM)
        request_socket.connect((self.address, self.port))

        while True:
            is_json = False
            if self.server_closed:
                return
            request = input('\nRequest: ')
            try:
                request = json.loads(request)
                if type(request) == int:
                    request_type = request
                else:
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
                    notification_thread = Thread(target=self.notification, args=(user_id,))  # msh[0] is user_id
                    notification_thread.start()
                else:  # that means server returned -1 as user_id since given username or pswd is incorrect.
                    print("You have entered the wrong username or password.")

            elif request_type == "UPLOAD_PHOTO" or request_type == "2":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        path = params[1]
                        request = {'command': '2.1', 'path': path}

                    with open(path, 'rb') as img_file:
                        image_read = img_file.read()
                        image_64_encode = base64.b64encode(image_read)

                    image_size = len(image_64_encode)
                    i = 0

                    # with this number server will now when receiving image will end
                    image_part_number = math.ceil(image_size/1024)

                    # command 2.1 says that user is uploading a photo and next request will include
                    # a part of encoded message
                    request['image_part_number'] =image_part_number

                    request_socket.send(str.encode(json.dumps(request)))

                    path = request['path']

                    while i < image_size:
                        image_part = image_64_encode[i:i+1024]
                        if len(image_part) % 4:
                            m = len(image_part) % 4
                            image_part += b'='*m
                        request_socket.send(image_part)
                        i += 1024

                    image_sent = request_socket.recv(1024).decode('utf8')

                    # encoded image is sent now it is time to notify server that image is done
                    # 2.2 will notify server and encoded image, assembled by parts of encoded image,
                    # will be uploaded to library in the server side

                    if image_sent:
                        request = {'command': '2.3'}
                        request_socket.send(str.encode(json.dumps(request)))

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

            elif request_type == "SHARE_COLLECTION" or request_type == "10":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        col_id = params[1]
                        shared_user_id = params[2]
                        request = {'command': '10', 'col_id': col_id, 'shared_user_id': shared_user_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "UNSHARE_COLLECTION" or request_type == "11":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        col_id = params[1]
                        unshared_user_id = params[2]
                        request = {'command': '11', 'col_id': col_id, 'unshared_user_id': unshared_user_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "ADD_PHOTO_TO_COLLECTION" or request_type == "12":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        col_id = params[1]
                        ph_id = params[2]
                        request = {'command': '12', 'col_id': col_id, 'ph_id': ph_id}
                        request_socket.send(str.encode(json.dumps(request)))
                        msg = request_socket.recv(1024).decode('utf8')
                        print(msg)

            elif request_type == "REMOVE_PHOTO_FROM_COLLECTION" or request_type == "13":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        col_id = params[1]
                        ph_id = params[2]
                        request = {'command': '13', 'col_id': col_id, 'ph_id': ph_id}
                        request_socket.send(str.encode(json.dumps(request)))
                        msg = request_socket.recv(1024).decode('utf8')
                        print(msg)

            elif request_type == "SET_TAG_FILTER_TO_VIEW" or request_type == "14":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        view_id = params[1]
                        tag_list = params[2]
                        conj = params[3]
                        request = {'command': '14', 'view_id': view_id, 'tag_list': tag_list, 'conj': conj}
                        request_socket.send(str.encode(json.dumps(request)))
                        msg = request_socket.recv(1024).decode('utf8')
                        print(msg)

            elif request_type == "SET_LOC_REC_TO_VIEW" or request_type == "15":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        view_id = params[1]
                        start_long = params[2]
                        end_long = params[3]
                        start_lat = params[4]
                        end_lat = params[5]
                        rec = (eval(start_long), eval(end_long), eval(start_lat), eval(end_lat))
                        request = {'command': '15', 'view_id': view_id, 'rec': str(rec)}
                        request_socket.send(str.encode(json.dumps(request)))
                        msg = request_socket.recv(1024).decode('utf8')
                        print(msg)

            elif request_type == "SET_TIME_INTERVAL_TO_VIEW" or request_type == "16":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        view_id = params[1]
                        start_yymmdd = params[2]
                        start_saat = params[3]
                        end_yymmdd = params[4]
                        end_saat = params[5]
                        request = {'command': '16', 'view_id': view_id, 'start_yymmdd': start_yymmdd,
                                   'start_saat': start_saat, 'end_yymmdd': end_yymmdd, 'end_saat': end_saat}
                        request_socket.send(str.encode(json.dumps(request)))
                        msg = request_socket.recv(1024).decode('utf8')
                        print(msg)

            elif request_type == "SHARE_VIEW" or request_type == "17":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        view_id = params[1]
                        shared_user_id = params[2]
                        request = {'command': '17', 'view_id': view_id, 'shared_user_id': shared_user_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "UNSHARE_VIEW" or request_type == "18":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        view_id = params[1]
                        unshared_user_id = params[2]
                        request = {'command': '18', 'view_id': view_id, 'unshared_user_id': unshared_user_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "ADD_VIEW_TO_COLLECTION" or request_type == "19":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        col_id = params[1]
                        view_id = params[2]
                        request = {'command': '19', 'col_id': col_id, 'view_id': view_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "REMOVE_TAG_FILTER_FROM_VIEW" or request_type == "20":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        view_id = params[1]
                        request = {'command': '20', 'view_id': view_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "REMOVE_LOC_FILTER_FROM_VIEW" or request_type == "21":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        view_id = params[1]
                        request = {'command': '21', 'view_id': view_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "REMOVE_TIME_FILTER_FROM_VIEW" or request_type == "22":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        view_id = params[1]
                        request = {'command': '22', 'view_id': view_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "DELETE_VIEW" or request_type == "23":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        view_id = params[1]
                        request = {'command': '23', 'view_id': view_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request_type == "LIST" or request_type == "24":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        object_name = params[1]
                        request = {'command': '24', 'object_name': object_name}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(json.loads(msg))

            elif request_type == "FETCH" or request_type == "26":
                user_id = self.is_user_logged_in()
                if user_id >= 0:
                    if not is_json:
                        params = request.split(" ")
                        col_id = params[1]
                        ph_id = params[2]
                        request = {'command': '26', 'col_id': col_id, 'ph_id': ph_id}
                    request_socket.send(str.encode(json.dumps(request)))
                    msg = request_socket.recv(1024).decode('utf8')
                    print(msg)

            elif request == 'exit':
                user_id = self.is_user_logged_in()
                request = {'command': '25'}
                request_socket.send(str.encode(json.dumps(request)))
                print('Bye')
                return


if __name__ == "__main__":
    client = Client()
    client.connect()
