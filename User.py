from SharedPhotoLibrary import *
from threading import Lock


class User:
    counter = 0
    users_dict = {}  # {user_id: User obj}

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.id = User.counter
        User.counter += 1
        self.collections = []
        self.collections_dict = {}
        self.views = set()
        self.photos = {}
        self.sharedCollectionsWithMe = set()
        self.sharedViewsWithMe = set()
        print("id type: ", type(self.id))
        User.users_dict[self.id] = self
        print(User.users_dict)

    def __str__(self):
        return f"User({self.id},\n{self.username},\ncollections of user: {self.collections},\n" \
               f"views of user: {self.views},\nshared collections with user: {self.sharedCollectionsWithMe},\n" \
               f"shared views with user: {self.sharedViewsWithMe},\n" \
               f"added photos by user: {self.photos}\n)"

    __repr__ = __str__

    def uploadPhoto(self, path, encoded_img):
        new_photo = Photo(path, encoded_img)
        self.photos[new_photo.id] = (new_photo)

        tags = None
        if new_photo.tags:
            tags = str(tags)

        photo_info = [new_photo.id, tags, str(new_photo.location), new_photo.datetime, path,
                      encoded_img, self.id]
        return photo_info

    def addTagToPhoto(self, id, tag):
        try:
            self.photos[id].addTag(tag)
            return True, self.photos[id].tags
        except KeyError:
            return False, "Photo with given id does not exist"

    def removeTagFromPhoto(self, id, tag):
        try:
            success = self.photos[id].removeTag(tag)
            if success:
                if not self.photos[id].tags:
                    return f"Tag: {tag} removed from Photo(id={id})", True, None
                return f"Tag: {tag} removed from Photo(id={id})",  True, self.photos[id].tags
            return f"Photo(id={id} doesn't include given Tag: {tag})", False, None
        except KeyError:
            return "Photo with given id does not exist"

    def setLocationOfPhoto(self, id, long, latt):
        try:
            self.photos[id].setLocation(long, latt)
            return True, f"Location of Photo(id={id} is set to longitude={long} and latitude={latt})"

        except KeyError:
            return False, "Photo with given id does not exist"

    def removeLocationFromPhoto(self, id):
        try:
            self.photos[id].removeLocation()
            return True, f"Location of Photo(id={id}) is removed."

        except KeyError:
            return False, "Photo with given id does not exist"

    def setDatetimeOfPhoto(self, id, datetime):
        try:
            self.photos[id].setDateTime(datetime)
            return True, ""
        except KeyError:
            return False, "Photo with given id does not exist"

    def isCollectionSharedWithUser(fnc):
        def inner(*args):
            user = args[0]
            collection = args[1]
            if user == collection.owner or collection in user.sharedCollectionsWithMe:
                return fnc(*args)
            else:
                return False, f"{collection.name} is not shared with {user.username}. {user.username} cannot inspect and update the collection {collection.name}.", None

        return inner

    def createCollection(self, name):
        created_collection = Collection(name, self)
        self.collections.append(created_collection)
        self.collections_dict[created_collection.id] = created_collection
        # self.db.insert("Collections", ('col_id', 'col_name', 'owner_id'), created_collection.id, name, self.id)

        return created_collection.id

    def createView(self, name):
        # This function creates a view with given name and adds it to the users views.
        my_view = View(name)
        my_view.owner = self
        self.views.add(my_view)
        # self.db.insert("Views", ('view_id', 'view_name', 'location_filter', 'time_filter_start', 'time_filter_end',
        #                          'col_id', 'owner_id'), my_view.id, name, "", "", "", -1, self.id)

        return my_view.id

    def shareCollection(self, shared_collection, shared_with):
        if self == shared_collection.owner:
            shared_users = shared_collection.share(shared_with)
            print(shared_users, "shared users")
            return True, f"{self.username} shared {shared_collection.name} with {shared_with.username}", shared_users
        else:
            return False, f"You don't have access to share {shared_collection.name}", None
            # print(f"{self.username} couldn't share {shared_collection.name} with {shared_with.username}. "
            #       f"Because {shared_collection.name} can be shared only by {shared_collection.owner.username} ")

    def unshareCollection(self, unshared_collection, unshared_with):
        if self == unshared_collection.owner:
            shared_users = unshared_collection.unshare(unshared_with)
            return True, f"{self.username} unshared {unshared_collection.name} with {unshared_with.username}", shared_users
        else:
            return False, f"You don't have access to unshare {unshared_collection.name}", None
            # print(f"{self.username} couldn't share {unshared_collection.name} with {unshared_with.username}. "
            #       f"Because {unshared_collection.name} can be shared only by {unshared_collection.owner.username} ")

    def shareView(self, shared_view, shared_with):
        if shared_view in self.views:
            login_required, shared_users = shared_view.share(shared_with)
            return True, f"{self.username} shared {shared_view.name} with {shared_with.username}", login_required, shared_users
        else:
            return False, f"You don't have access to share {shared_view.name}", None, None

    def unshareView(self, unshared_view, unshared_with):
        if unshared_view in self.views:
            shared_users = unshared_view.unshare(unshared_with)
            return True, f"{self.username} shared {unshared_view.name} with {unshared_with.username}", shared_users
        else:
            return False, f"You don't have access to share {unshared_view.name}", None



    @isCollectionSharedWithUser
    def addPhotoToCollection(self, collection, photo):
        collection_photos = collection.addPhoto(photo)
        return True, f'{self.username} added Photo(id{photo.id}) to Collection({collection.name})', collection_photos


    @isCollectionSharedWithUser
    def removePhotoFromCollection(self, collection, photo):
        collection_photos = collection.removePhoto(photo)
        return True, f'{self.username} removed Photo(id{photo.id}) from Collection({collection.name})', collection_photos


    @isCollectionSharedWithUser
    def fetchPhotoFromCollection(self, collection, ph_id):
        collection.fetchPhoto(ph_id)

    @isCollectionSharedWithUser
    def addViewToCollection(self, collection, view):
        if view in self.views or view in self.sharedViewsWithMe:
            filtered_photos_ids = collection.addView(view)
            msg = f'View({view.name}) is added to Collection({collection.name}).\n' \
                  f'Photos ids in view is {filtered_photos_ids}'
            return True, msg, filtered_photos_ids
        else:
            msg = f"View({view.name}) is not shared with you. You don't have access to attach it to a collection."
            return False, msg, None

    def unsharedCollection(self, unshared_collection):
        if unshared_collection in self.sharedCollectionsWithMe:
            self.sharedCollectionsWithMe.remove(unshared_collection)

    def sharedCollection(self, shared_collection):
        self.sharedCollectionsWithMe.add(shared_collection)

    def sharedView(self, shared_view):
        self.sharedViewsWithMe.add(shared_view)

    def unsharedView(self, unshared_view):
        if unshared_view in self.sharedViewsWithMe:
            self.sharedViewsWithMe.remove(unshared_view)

    def setTagFilterToView(self, view, tag_list, conj=False):
        if view in self.views or view in self.sharedViewsWithMe:
            old_tags = view.tag_list
            old_filtered_photos_ids = view.filtered_photos_ids
            new_tags = tag_list
            new_filtered_photos_ids = view.setTagFilter(tag_list, conj)
            msg = f"Tag filter of view is changed from {old_tags} to {new_tags}\n " \
                  f"Photos ids list is changed from {old_filtered_photos_ids} to {new_filtered_photos_ids}"
            return True, msg, new_filtered_photos_ids
        else:
            msg = "You don't have the access to make changes on this view"
            return False, msg, None

    def removeTagFilterFromView(self, view):
        if view in self.views or view in self.sharedViewsWithMe:
            old_tags = view.tag_list
            old_filtered_photos_ids = view.filtered_photos_ids
            new_filtered_photos_ids = view.removeTagFilter()
            msg = f"Tag filter{old_tags} of view is removed.\n " \
                  f"Photos ids list is changed from {old_filtered_photos_ids} to {new_filtered_photos_ids}"
            return True, msg, new_filtered_photos_ids
        else:
            msg = "You don't have the access to make changes on this view"
            return False, msg, None


    def setLocationRectToView(self, view, rectangle):
        if view in self.views or view in self.sharedViewsWithMe:
            old_rec = view.location_rect
            old_filtered_photos_ids = view.filtered_photos_ids
            new_rec = rectangle
            new_filtered_photos_ids = view.setLocationRect(rectangle)
            msg = f"Location rectangle of view is changed from {old_rec} to {new_rec}\n " \
                  f"Photos ids list is changed from {old_filtered_photos_ids} to {new_filtered_photos_ids}"
            return True, msg, new_filtered_photos_ids

        else:
            msg = "You don't have the access to make changes on this view"
            return False, msg, None

    def removeLocRecFromView(self, view):
        if view in self.views or view in self.sharedViewsWithMe:
            old_rec = view.location_rect
            old_filtered_photos_ids = view.filtered_photos_ids
            new_filtered_photos_ids = view.removeLocationRect()
            msg = f"Location filter{old_rec} of view is removed.\n " \
                  f"Photos ids list is changed from {old_filtered_photos_ids} to {new_filtered_photos_ids}"
            return True, msg, new_filtered_photos_ids
        else:
            msg = "You don't have the access to make changes on this view"
            return False, msg, None

    def setTimeIntervalToView(self, view, start, end):
        if view in self.views or view in self.sharedViewsWithMe:
            old_time = view.time_interval
            old_filtered_photos_ids = view.filtered_photos_ids
            new_filtered_photos_ids = view.setTimeInterval(start, end)
            new_time = (start, end)
            msg = f"Time interval of view is changed from {old_time} to {new_time}\n " \
                  f"Photos ids list is changed from {old_filtered_photos_ids} to {new_filtered_photos_ids}"
            return True, msg, new_filtered_photos_ids
        else:
            msg = "You don't have the access to make changes on this view"
            return False, msg, None

    def removeTimeIntervalFromView(self, view):
        if view in self.views or view in self.sharedViewsWithMe:
            old_time = view.time_interval
            old_filtered_photos_ids = view.filtered_photos_ids
            new_filtered_photos_ids = view.removeTimeInterval()
            msg = f"Time interval {old_time} of view is removed.\n " \
                  f"Photos ids list is changed from {old_filtered_photos_ids} to {new_filtered_photos_ids}"
            return True, msg, new_filtered_photos_ids
        else:
            msg = "You don't have the access to make changes on this view"
            return False, msg, None


