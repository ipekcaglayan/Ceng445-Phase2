import datetime
from exif import Image
import PIL.Image
import base64


class Photo:
    # Counter is a class attribute, whenever a photo object is created, current value of counter is used as photo id
    # and, counter is incremented by 1.

    counter = 0
    photos_dict = {}
    def __init__(self, path, encoded_image):

        self.tags = set()
        self.id = Photo.counter
        Photo.counter += 1
        # open the photo in given path
        photo = PIL.Image.open(path)
        # set thumbnail of photo in given max size
        MAX_SIZE = (100, 100)  # max thumbnail size
        self.thumbnail = photo.thumbnail(MAX_SIZE)

        # open photo in binary format to read metadata
        with open(path, 'rb') as img_file:
            img = Image(img_file)

        self.encoded_image = encoded_image

        self.location = None
        # get gps info of the photo from metadata. latitude and longtitude is assigned None if gps info does not exist
        latitude = img.get('gps_latitude')
        longitude = img.get('gps_longitude')

        # if gps info exists, set location attribute of object
        if longitude and latitude:
            self.location = (longitude, latitude)

        self.datetime = None
        date = img.get('datetime')
        # if datetime info exists, set datetime attribute

        if date:
            dates = date.split(" ")

            yymmdd = [int(x) for x in dates[0].split(":")]
            saat = [int(x) for x in dates[1].split(":")]

            self.datetime = datetime.datetime(*(yymmdd+saat))

        Photo.photos_dict[self.id] = self
        photo.close()

    def __str__(self):
        return f"Photo({self.id}, {self.location},{self.datetime}, {self.tags})"

    __repr__ = __str__

    def addTag(self, tag):
        self.tags.add(tag)

    def removeTag(self, tag):
        if tag in self.tags:  # if given tag does not exist, do nothing
            self.tags.remove(tag)
            return True
        return False

    def setLocation(self, long, latitude):
        self.location = (long, latitude)
        # change metadata of the actual photo file in phase2

    def removeLocation(self):
        self.location = None
        # change metadata of the actual photo file in phase2

    def setDateTime(self, date):
        self.datetime = date
        # change metadata of the actual photo file in phase2


class Collection:

    counter = 0
    collections_dict = {}

    def __init__(self, name, user):
        self.id = Collection.counter
        Collection.counter += 1
        self.name = name
        self.photos = {}  # photos are kept in dictionary object for more efficient fetch operation
        self.views = set()
        self.owner = user
        self.shared_users = set()
        self.collection_photos = set()
        Collection.collections_dict[self.id] = self


    def __str__(self):
        return f'Collection({self.name},{self.photos}, views: {self.views})'

    __repr__ = __str__

    def addPhoto(self, photo):
        self.photos[photo.id] = photo
        self.collection_photos.add(photo.id)

        # for all views attached to this collection, update the views since they might add the newly added photo
        msg = f""
        view_changes = []
        for v in self.views:
            old_photos_ids = v.filtered_photos_ids
            new_photos_ids = v.update()
            if old_photos_ids != new_photos_ids:
                view_changes.append((new_photos_ids, v.id))
                msg += f"Photos ids list is changed from {old_photos_ids} to {new_photos_ids} for View(id={v.id}) " \
                      f"which contains filtering for Collection({self.name})\n"

        return self.collection_photos, msg, view_changes

    def removePhoto(self, photo):
        if photo.id in self.photos:  # if photo in collection, remove
            del self.photos[photo.id]
            self.collection_photos.remove(photo.id)

        # for all views attached to this collection, update the views since they might contain the removed photo
        msg = f""
        view_changes = []
        for v in self.views:
            old_photos_ids = v.filtered_photos_ids
            new_photos_ids = v.update()
            if old_photos_ids != new_photos_ids:
                view_changes.append((new_photos_ids, v.id))
                msg += f"Photos ids list is changed from {old_photos_ids} to {new_photos_ids} for View(id={v.id}) " \
                      f"which contains filtering for Collection({self.name})\n"

        return self.collection_photos, msg, view_changes

    def fetchPhoto(self, ph_id):
        photo = self.photos[ph_id]
        tags = ", ".join(photo.tags)
        print(f"tags: {tags} \nlocation: {photo.location} \ndatetime : {photo.datetime}")
        return photo

    def addView(self, view):
        self.views.add(view)
        view.attachedToCollection(self)
        return view.update()

    def share(self, user):
        user.sharedCollection(self)
        self.shared_users.add(user.id)
        return self.shared_users

    def unshare(self, user):
        user.unsharedCollection(self)
        if user.id in self.shared_users:
            self.shared_users.remove(user.id)
        return self.shared_users


class View:

    counter = 0
    views_dict = {}

    def __init__(self, name):
        self.id = View.counter
        self.name = name
        View.counter += 1
        self.tag_list = set()
        self.filtered_photos_ids = set()
        self.conjunctive = False
        self.location_rect = None
        self.shared_users = set()
        # will be in the form (start_longitude tuple(3), end_longitude, start_latitude, end_latitude)
        # self.location_rect = ()
        # self.time_interval = ()
        self.time_interval = None
        self.collection = None
        self.login_required = True  # This attribute will be set to False when view is publicly shared to users
        # that are not logged-in as well
        View.views_dict[self.id] = self

    def __str__(self):
        return f"View({self.name}, {self.location_rect}, {self.time_interval},{self.tag_list})"

    __repr__ = __str__

    def filterByView(self):
        self.filtered_photos_ids = set()
        # print(self.location_rect, self.tag_list, self.conjunctive)
        # print(self.collection.photos)
        if self.collection:
            for key, ph in self.collection.photos.items():
                flag = 1
                if self.time_interval and ph.datetime and ph.datetime is not None:
                    if (ph.datetime < self.time_interval[0]) or (ph.datetime > self.time_interval[1]):
                        flag = 0
                if self.location_rect and ph.location is not None:
                  
                    if ((self.location_rect[0] > ph.location[0]) or (self.location_rect[1] < ph.location[0]) or
                            (self.location_rect[2] > ph.location[1]) or (self.location_rect[3] < ph.location[1])):
                           
                        flag = 0
                if self.tag_list:
                    if self.conjunctive:

                        break_from_all_loops = False
                        for view_tag in self.tag_list:
                            for foto_tag in ph.tags:
                                if view_tag == foto_tag:
                                    break_from_all_loops = True  # there is a matching tag in photo and view

                                    break

                            if break_from_all_loops:
                                break
                        if not break_from_all_loops:
                            flag = 0
                    else:
                        for view_tag in self.tag_list:
                            tag_found = False

                            for foto_tag in ph.tags:

                                if view_tag == foto_tag:
                                    tag_found = True
                                    break
                            if not tag_found:
                                flag = 0
                if flag == 1:
                    self.filtered_photos_ids.add(ph.id)

        return self.filtered_photos_ids

    def setTagFilter(self, tag_list, conj=False):
        self.tag_list = tag_list
        self.conjunctive = conj
        return self.update()

    def removeTagFilter(self):
        self.tag_list = set()
        return self.update()

    def setLocationRect(self, rectangle):
        self.location_rect = rectangle
        return self.update()

    def removeLocationRect(self):
        self.location_rect = None
        return self.update()

    def setTimeInterval(self, start, end):
        self.time_interval = (start, end)
        return self.update()

    def removeTimeInterval(self):
        self.time_interval = None
        return self.update()

    def getTagFilter(self):
        return self.tag_list

    def getLocationRect(self):
        return self.location_rect

    def getTimeInterval(self):
        return self.time_interval

    def share(self, user):
        if user.username == "*":
            self.login_required = False
        else:
            user.sharedView(self)
            self.shared_users.add(user.id)
        return self.login_required, self.shared_users

    def unshare(self, user):
        user.unsharedView(self)
        if user.id in self.shared_users:
            self.shared_users.remove(user.id)
        return self.shared_users

    # when the view is attached to the collection or whenever the state of the collection changes
    # (photos are added/deleted), photos in the view updated
    def update(self):
        print(f"View: {self.name} updated.")
        return self.filterByView()



    def attachedToCollection(self, attached_to):
        self.collection = attached_to
        self.filtered_photos_ids = attached_to.photos.keys()

    def photoList(self):
        return list(self.filtered_photos_ids)

    def fetchPhoto(self, ph_id):
        if ph_id in self.filtered_photos_ids:
            self.collection.fetchPhoto(ph_id)
        else:
            print("Photo with given id is not in the view")
            return None







# my=Photo("./canon.jpg")






    
        

