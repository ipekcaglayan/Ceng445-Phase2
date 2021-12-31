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
    notification_port = 2028
    logged_in_clients = {}

    def __init__(self):
        self.connected_clients = 0
        sql_db = sqlite3.connect('database.db', check_same_thread=False)
        self.db = Database(sql_db, sql_db.cursor())

    def create_library_objects(self):

        # create users from database
        users_list = list(self.db.curs.execute(f'SELECT user_id, username, password from Users'))
        users_dict = {}
        user_counter = 0
        for user_tuple in users_list:
            u = User(user_tuple[1], user_tuple[2])
            u.id = int(user_tuple[0])
            if u.id > user_counter:
                user_counter = u.id
            users_dict[u.id] = u

        User.users_dict = users_dict
        User.counter = user_counter + 1

        # create photos from database

        photo_list = list(self.db.curs.execute(f'SELECT ph_id, tags, location, datetime, path, encoded_img, '
                                               f'user_id from Photos'))
        photos_dict = {}
        ph_counter = 0

        for ph_tuple in photo_list:
            ph_id = int(ph_tuple[0])
            tags = ph_tuple[1]
            location = ph_tuple[2]
            ph_datetime = ph_tuple[3]
            path = ph_tuple[4]
            encoded_img = ph_tuple[5]
            user_id = int(ph_tuple[6])
            photo = Photo(path, encoded_img)
            photo.id = ph_id
            photo.tags = set()
            photo.location = None
            photo.datetime = None
            if photo.id > ph_counter:
                ph_counter = photo.id
            if tags:
                photo.tags = eval(tags)
            if location:
                photo.location = eval(location)
            if ph_datetime:
                dates = ph_datetime.split(" ")
                yymmdd = [int(x) for x in dates[0].split("-")]
                saat = [int(x) for x in dates[1].split(":")]
                photo.datetime = datetime.datetime(*(yymmdd+saat))
            u = User.users_dict[user_id]
            u.photos[photo.id] = photo
            photos_dict[photo.id] = photo

        Photo.photos_dict = photos_dict
        Photo.counter = ph_counter+1

        # create collections from database
        col_list = list(self.db.curs.execute(f'SELECT col_id, col_name, owner_id, shared_users, collection_photos'
                                             f' from Collections'))
        collections_dict = {}
        col_counter = 0

        for col_tuple in col_list:
            owner = User.users_dict[col_tuple[2]]
            col = Collection(col_tuple[1], owner)
            col.id = int(col_tuple[0])
            if col.id > col_counter:
                col_counter = col.id

            owner.collections.append(col)
            owner.collections_dict[col.id] = col
            if col_tuple[3]:
                col.shared_users = eval(col_tuple[3])
                shared_users = [int(u_id) for u_id in eval(col_tuple[3])]
                for u_id in shared_users:
                    u = User.users_dict[u_id]
                    u.sharedCollectionsWithMe.add(col)

            print(col_tuple[4])
            if col_tuple[4]:  # collection_photos
                col.collection_photos = eval(col_tuple[4])
                for ph_id in col.collection_photos:
                    col.photos[ph_id] = Photo.photos_dict[ph_id]

            collections_dict[col.id] = col

        Collection.collections_dict = collections_dict
        Collection.counter = col_counter + 1

        # create view from database

        views_list = list(self.db.curs.execute(f'SELECT view_id, view_name, location_filter, time_filter_start, '
                                               f'time_filter_end, col_id, owner_id, login_required, '
                                               f'filtered_photos_ids, tag_list, shared_users, conjunctive from Views'))
        views_dict = {}
        view_counter = 0

        for view_tuple in views_list:
            view_id = int(view_tuple[0])
            view_name = view_tuple[1]
            location_filter = view_tuple[2]
            time_filter_start = view_tuple[3]  # string: 'yy-mm-dd hh:mm:ss'
            time_filter_end = view_tuple[4]  # string: 'yy-mm-dd hh:mm:ss'
            col_id = view_tuple[5]
            owner_id = int(view_tuple[6])
            login_required = view_tuple[7]
            filtered_photos_ids = eval(view_tuple[8])
            tag_list = eval(view_tuple[9])
            shared_users = eval(view_tuple[10])
            conj = view_tuple[11]
            if conj == 1 or conj == '1' or conj == True or conj == 'True':
                conj = True
            else:
                conj = False

            view = View(view_name)
            view.id = view_id
            view.login_required = login_required
            view.filtered_photos_ids = filtered_photos_ids
            view.tag_list = tag_list
            view.conjunctive = conj

            if view.id > view_counter:
                view_counter = view.id

            if time_filter_start:
                dates_start = time_filter_start.split(" ")
                yymmdd_start = [int(x) for x in dates_start[0].split("-")]
                saat_start = [int(x) for x in dates_start[1].split(":")]
                start_datetime = datetime.datetime(*(yymmdd_start + saat_start))

                dates_end = time_filter_end.split(" ")
                yymmdd_end = [int(x) for x in dates_end[0].split("-")]
                saat_end = [int(x) for x in dates_end[1].split(":")]
                end_datetime = datetime.datetime(*(yymmdd_end + saat_end))

                view.time_interval = (start_datetime, end_datetime)

            if location_filter:
                view.location_rect = eval(location_filter)

            print("Col id: ", col_id)
            if col_id is not None:
                print("Ife girdi")
                col = Collection.collections_dict[int(col_id)]
                view.collection = col
                col.views.add(view)

            u = User.users_dict[owner_id]
            view.owner = u
            u.views.add(view)

            for shared_u_id in shared_users:
                shared_user = User.users_dict[shared_u_id]
                shared_user.sharedViewsWithMe.add(view)

            views_dict[view.id] = view

        View.views_dict = views_dict
        View.counter = col_counter + 1

    def photo_update_notification_list(self, ph_id):
        users_list = set()
        for col_id, col in Collection.collections_dict.items():
            if ph_id in col.photos:
                users_list.add(col.owner.id)
                users_list = users_list.union(col.shared_users)
        for view_id, view in View.views_dict.items():
            if ph_id in view.filtered_photos_ids:
                users_list = users_list.union(view.shared_users)

        return users_list

    def collection_update_notification_list(self, col_id):
        col = Collection.collections_dict[col_id]
        users_list = col.shared_users
        users_list.add(col.owner.id)
        for view_id, view in View.views_dict.items():
            if col == view.collection:
                users_list = users_list.union(view.shared_users)

        return users_list

    def view_update_notification_list(self, view_id):
        view = View.views_dict[view_id]
        users_list = view.shared_users
        for col_id, col in Collection.collections_dict.items():
            if view in col.views:
                users_list = users_list.union(col.shared_users)

        return users_list



    def user_does_request(self, request, **kwargs):
        user_id = int(kwargs['user_id'])
        user = User.users_dict[user_id]

        if request == 2:  # Upload Photo
            # photo_data = user.uploadPhoto(kwargs['path'], kwargs['encoded_img'])
            photo_data = user.uploadPhoto(kwargs['path'], kwargs['encoded_img'])
            print(photo_data)
            self.db.insert("Photos", ('ph_id', 'tags', 'location', 'datetime', 'path', 'encoded_img', 'user_id'),
                           *photo_data)

            return str(photo_data[0])

        elif request == 3:  # Add Tag to Photo
            ph_id = int(kwargs['ph_id'])
            tag = kwargs['tag']
            success, new_tags = user.addTagToPhoto(ph_id, tag)
            if success:
                self.db.update("Photos", "tags", "ph_id", *[str(new_tags), ph_id])
                msg = f"Tag: {tag} is added to Photo(id={ph_id})"
                notification_list = self.photo_update_notification_list(ph_id)
                self.send_notification(msg, notification_list)
                return msg
            return new_tags

        elif request == 4:  # Remove Tag from Photo
            ph_id = int(kwargs['ph_id'])
            if ph_id not in Photo.photos_dict:
                return f"Photo with given id does not exist"
            tag = kwargs['tag']
            msg, update_required, new_tags = user.removeTagFromPhoto(ph_id, tag)
            if update_required:
                if new_tags:
                    new_tags = str(new_tags)
                self.db.update("Photos", "tags", "ph_id", *[new_tags, ph_id])
                notification_list = self.photo_update_notification_list(ph_id)
                self.send_notification(msg, notification_list)
            return msg

        elif request == 5:  # Set Loc of Photo
            ph_id = int(kwargs['ph_id'])
            long = eval(kwargs['long'])
            latt = eval(kwargs['latt'])
            success, msg = user.setLocationOfPhoto(ph_id, long, latt)
            loc = (long, latt)
            if success:
                self.db.update("Photos", "location", "ph_id", *[str(loc), ph_id])
                notification_list = self.photo_update_notification_list(ph_id)
                self.send_notification(msg, notification_list)
            return msg

        elif request == 6:  # Remove Loc from Photo
            ph_id = int(kwargs['ph_id'])
            success, msg = user.removeLocationFromPhoto(ph_id)
            if success:
                self.db.update("Photos", "location", "ph_id", *[None, ph_id])
                notification_list = self.photo_update_notification_list(ph_id)
                self.send_notification(msg, notification_list)
            return msg

        elif request == 7:  # Set Datetime of Photo
            ph_id = int(kwargs['ph_id'])
            yymmdd = kwargs['yymmdd']
            saat = kwargs['saat']
            yymmdd_list = [int(x) for x in yymmdd.split("-")]
            saat_list = [int(x) for x in saat.split(":")]
            mydatetime = datetime.datetime(*(yymmdd_list + saat_list))

            success, msg = user.setDatetimeOfPhoto(ph_id, mydatetime)
            if success:
                msg = f'Datetime of Photo(id={ph_id}) is set to {yymmdd} {saat}'
                self.db.update("Photos", "datetime", "ph_id", *[" ".join([yymmdd, saat]), ph_id])
                notification_list = self.photo_update_notification_list(ph_id)
                self.send_notification(msg, notification_list)
            return msg

        elif request == 8:  # Create Collection
            col_id = user.createCollection(kwargs['collection_name'])
            self.db.insert("Collections", ('col_id', 'col_name', 'owner_id', 'shared_users'), col_id,
                           kwargs['collection_name'], user.id, None)
            return str(col_id)

        elif request == 9:  # Create View
            view_id = user.createView(kwargs['view_name'])
            self.db.insert("Views", ('view_id', 'view_name', 'location_filter', 'time_filter_start',
                                     'time_filter_end', 'col_id', 'owner_id', 'login_required', 'filtered_photos_ids', 'tag_list',
                                     'shared_users', 'conjunctive'),
                           *[view_id, kwargs['view_name'], None, None, None, None, user_id, True, str(set()),
                             str(set()), str(set()), False])
            return str(view_id)

        elif request == 10:  # Share Collection
            col = Collection.collections_dict[int(kwargs['col_id'])]
            shared_user = User.users_dict[int(kwargs['shared_user_id'])]
            success, msg, shared_users = user.shareCollection(col, shared_user)
            if success:
                self.db.update("Collections", "shared_users", "col_id", *[str(shared_users), int(kwargs['col_id'])])
            return msg

        elif request == 11:  # Unshare Collection
            col = Collection.collections_dict[int(kwargs['col_id'])]
            unshared_user = User.users_dict[int(kwargs['unshared_user_id'])]
            success, msg, shared_users = user.unshareCollection(col, unshared_user)
            if success:
                self.db.update("Collections", "shared_users", "col_id", *[str(shared_users), int(kwargs['col_id'])])
            return msg

        elif request == 12:  # Add photo to collection
            col = Collection.collections_dict[int(kwargs['col_id'])]
            photo = Photo.photos_dict[int(kwargs['ph_id'])]
            success, msg, collection_photos, view_changes = user.addPhotoToCollection(col, photo)
            if success:
                self.db.update("Collections", "collection_photos", "col_id", *[str(collection_photos), int(kwargs['col_id'])])
                for v_tuple in view_changes:
                    self.db.update("Views", "filtered_photos_ids", "view_id", *[str(v_tuple[0]), int(v_tuple[1])])
                notification_list = self.collection_update_notification_list(int(kwargs['col_id']))
                self.send_notification(msg, notification_list)

            return msg

        elif request == 13:  # Remove photo from collection
            col = Collection.collections_dict[int(kwargs['col_id'])]
            photo = Photo.photos_dict[int(kwargs['ph_id'])]
            success, msg, collection_photos, view_changes = user.removePhotoFromCollection(col, photo)
            if success:
                self.db.update("Collections", "collection_photos", "col_id", *[str(collection_photos), int(kwargs['col_id'])])
                for v_tuple in view_changes:
                    self.db.update("Views", "filtered_photos_ids", "view_id", *[str(v_tuple[0]), int(v_tuple[1])])
                notification_list = self.collection_update_notification_list(int(kwargs['col_id']))
                self.send_notification(msg, notification_list)
            return msg

        elif request == 14:  # Set tag filter to view
            view = View.views_dict[int(kwargs['view_id'])]
            tag_list = eval(kwargs['tag_list'])
            conj = eval(kwargs['conj'])
            success, msg, new_photos_ids = user.setTagFilterToView(view, tag_list, conj)
            if success:
                self.db.update("Views", "filtered_photos_ids", "view_id", *[str(new_photos_ids), int(kwargs['view_id'])])
                self.db.update("Views", "tag_list", "view_id", *[str(tag_list), int(kwargs['view_id'])])
                self.db.update("Views", "conjunctive", "view_id", *[conj, int(kwargs['view_id'])])
                notification_list = self.view_update_notification_list(int(kwargs['view_id']))
                self.send_notification(msg, notification_list)
            return msg

        elif request == 15:  # Set loc rec to view
            view = View.views_dict[int(kwargs['view_id'])]
            rec = eval(kwargs['rec'])
            success, msg, new_photos_ids = user.setLocationRectToView(view, rec)
            if success:
                self.db.update("Views", "filtered_photos_ids", "view_id", *[str(new_photos_ids), int(kwargs['view_id'])])
                self.db.update("Views", "location_filter", "view_id", *[str(rec), int(kwargs['view_id'])])
                notification_list = self.view_update_notification_list(int(kwargs['view_id']))
                self.send_notification(msg, notification_list)
            return msg

        elif request == 16:  # Set time interval to view
            view = View.views_dict[int(kwargs['view_id'])]
            start_yymmdd = kwargs['start_yymmdd']
            start_saat = kwargs['start_saat']
            end_yymmdd = kwargs['end_yymmdd']
            end_saat = kwargs['end_saat']

            yymmdd_list_start = [int(x) for x in start_yymmdd.split("-")]
            saat_list_start = [int(x) for x in start_saat.split(":")]
            start_datetime = datetime.datetime(*(yymmdd_list_start + saat_list_start))

            yymmdd_list_end = [int(x) for x in end_yymmdd.split("-")]
            saat_list_end = [int(x) for x in end_saat.split(":")]
            end_datetime = datetime.datetime(*(yymmdd_list_end + saat_list_end))

            success, msg, new_photos_ids = user.setTimeIntervalToView(view, start_datetime, end_datetime)

            if success:
                self.db.update("Views", "filtered_photos_ids", "view_id", *[str(new_photos_ids), int(kwargs['view_id'])])
                self.db.update("Views", "time_filter_start", "view_id", *[str(start_datetime), int(kwargs['view_id'])])
                self.db.update("Views", "time_filter_end", "view_id", *[str(end_datetime), int(kwargs['view_id'])])
                notification_list = self.view_update_notification_list(int(kwargs['view_id']))
                self.send_notification(msg, notification_list)
            return msg

        elif request == 17:  # Share View
            view = View.views_dict[int(kwargs['view_id'])]
            shared_user = User.users_dict[int(kwargs['shared_user_id'])]
            success, msg, login_required, shared_users = user.shareView(view, shared_user)
            if success:
                self.db.update("Views", "shared_users", "view_id", *[str(shared_users), int(kwargs['view_id'])])
                self.db.update("Views", "login_required", "view_id", *[login_required, int(kwargs['view_id'])])
            return msg

        elif request == 18:  # Unshare View
            view = View.views_dict[int(kwargs['view_id'])]
            unshared_user = User.users_dict[int(kwargs['unshared_user_id'])]
            success, msg, shared_users = user.unshareView(view, unshared_user)
            if success:
                self.db.update("Views", "shared_users", "view_id", *[str(shared_users), int(kwargs['view_id'])])
            return msg

        elif request == 19:  # Add View to Collection
            col = Collection.collections_dict[int(kwargs['col_id'])]
            view = View.views_dict[int(kwargs['view_id'])]
            success, msg, filtered_photos_ids = user.addViewToCollection(col, view)
            if success:
                self.db.update("Views", "filtered_photos_ids", "view_id", *[str(filtered_photos_ids), int(kwargs['view_id'])])
                self.db.update("Views", "col_id", "view_id", *[int(kwargs['col_id']), int(kwargs['view_id'])])
                view_list = self.view_update_notification_list(int(kwargs['view_id']))
                col_list = self.collection_update_notification_list(int(kwargs['col_id']))
                notification_list = set.union(view_list, col_list)
                self.send_notification(msg, notification_list)
            return msg

        elif request == 20:  # Remove tag filter from view
            view = View.views_dict[int(kwargs['view_id'])]
            success, msg, new_photos_ids = user.removeTagFilterFromView(view)
            if success:
                self.db.update("Views", "filtered_photos_ids", "view_id", *[str(new_photos_ids), int(kwargs['view_id'])])
                self.db.update("Views", "tag_list", "view_id", *[str(set()), int(kwargs['view_id'])])
                notification_list = self.view_update_notification_list(int(kwargs['view_id']))
                self.send_notification(msg, notification_list)
            return msg

        elif request == 21:  # Remove loc filter from view
            view = View.views_dict[int(kwargs['view_id'])]
            success, msg, new_photos_ids = user.removeLocRecFromView(view)
            if success:
                self.db.update("Views", "filtered_photos_ids", "view_id", *[str(new_photos_ids), int(kwargs['view_id'])])
                self.db.update("Views", "location_filter", "view_id", *[None, int(kwargs['view_id'])])
                notification_list = self.view_update_notification_list(int(kwargs['view_id']))
                self.send_notification(msg, notification_list)
            return msg

        elif request == 22:  # Remove time filter from view
            view = View.views_dict[int(kwargs['view_id'])]
            success, msg, new_photos_ids = user.removeTimeIntervalFromView(view)

            if success:
                self.db.update("Views", "filtered_photos_ids", "view_id", *[str(new_photos_ids), int(kwargs['view_id'])])
                self.db.update("Views", "time_filter_start", "view_id", *[None, int(kwargs['view_id'])])
                self.db.update("Views", "time_filter_end", "view_id", *[None, int(kwargs['view_id'])])
                notification_list = self.view_update_notification_list(int(kwargs['view_id']))
                self.send_notification(msg, notification_list)
            return msg

        elif request == 23:  # Delete view
            view = View.views_dict[int(kwargs['view_id'])]
            notification_list = self.view_update_notification_list(int(kwargs['view_id']))

            col = view.collection
            col.views.remove(view)

            for u_id in view.shared_users:
                u = User.users_dict[u_id]
                u.unsharedView(view)
            view.owner.views.remove(view)

            self.db.delete("Views", "view_id", *[int(kwargs['view_id'])])
            msg = f"View(id={kwargs['view_id']} is deleted.)"
            self.send_notification(msg, notification_list)
            return msg

        elif request == 24:
            object_name = kwargs['object_name']
            response = {}
            if object_name == "C":
                for c_id, c in Collection.collections_dict.items():
                    response[c_id] = c.name

            return json.dumps(response)

        elif request == 26:
            col_id = int(kwargs['col_id'])
            ph_id = int(kwargs['ph_id'])
            col = Collection.collections_dict[col_id]
            success, msg, encoded_img = user.fetchPhotoFromCollection(col, ph_id)
            return msg

    def request_handler(self, request_handler_socket):
        client_user_id = -1
        encoded_img = b''
        path = ""
        image_part_number = 0
        while True:
            received_msg = request_handler_socket.recv(1024)
            decode8 = received_msg.decode('utf8')
            try:
                request = json.loads(decode8)
            except JSONDecodeError:
                # that means received msg is not in json form which happens only when client send image
                # client send image in reqq type 2 = UPLOAD_PHOTO
                # client is sending parts of encoded image
                encoded_img += received_msg
                request = {'command': '2.2'}

            request_type = request['command']
            request['user_id'] = client_user_id

            if request_type == '0':  # CREATE_USER
                with Server.mutex:
                    user = User(request['username'], request['password'])
                    user_id = str(user.id)
                    self.db.insert("Users", ('user_id', 'username', 'password'), user.id, user.username, user.password)

                    request_handler_socket.send(str.encode(user_id))

            elif request_type == '1':  # LOGIN
                with Server.mutex:
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

            elif request_type == '2.1':
                with Server.mutex:
                    encoded_img = b''
                    path = request['path']
                    image_part_number = request['image_part_number']

            elif request_type == '2.2':
                image_part_number -= 1
                # received_msg = request_handler_socket.recv(1024)
                if image_part_number == 0:
                    # sent receiving image is done message to client side
                    request_handler_socket.send(str.encode("DONE"))

                continue

            elif request_type == '2.3':
                with Server.mutex:
                    request['encoded_img'] = encoded_img
                    request['path'] = path
                    message = self.user_does_request(2, **request)
                    request_handler_socket.send(str.encode(message))

            elif request_type == '25':  # Client closing
                with Server.mutex:
                    user_id = int(request['user_id'])
                    self.send_notification("exit", [user_id])
                    if user_id in self.logged_in_clients:
                        del self.logged_in_clients[user_id]
                        return

            else:
                with Server.mutex:
                    req_type = int(request_type)
                    message = self.user_does_request(req_type, **request)
                    request_handler_socket.send(str.encode(message))


    def send_notification(self, notification_msg, user_ids):
        for user_id in user_ids:
            # Check if user needed to be notified is logged in.
            if user_id in self.logged_in_clients:
                try:
                    self.logged_in_clients[user_id].send(str.encode(notification_msg))
                except:
                    continue

    def notification_handler(self, notification_handler_socket):
        user_id = int(notification_handler_socket.recv(1024).decode('utf8'))
        print(f'A Client is logged in to be notified with user id : {user_id}')
        self.logged_in_clients[user_id] = notification_handler_socket

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
            print("New client thread -> ", req_handler.ident)

    def start_notification(self):
        try:
            notification_handler_socket = socket(AF_INET, SOCK_STREAM)
            notification_handler_socket.bind(('', self.notification_port))
            notification_handler_socket.listen()
        except Exception as e:
            print(f"Unable to start to notification. An error occurred:{e}")
            return

        while True:
            conn, peer = notification_handler_socket.accept()
            not_handler = Thread(target=self.notification_handler, args=(conn,))
            not_handler.start()
            print("Notification thread -> ", not_handler.ident)

    def start(self):

        start_server = Thread(target=self.start_server)
        start_server.start()
        start_notification = Thread(target=self.start_notification)
        start_notification.start()


if __name__ == "__main__":
    server = Server()
    server.create_library_objects()
    server.start()
