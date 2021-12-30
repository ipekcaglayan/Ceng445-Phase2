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
        # self.db.insert("Photos", ('ph_id', 'tags', 'location', 'datetime', 'user_id'), new_photo.id, "", "", "", self.id)

        photo_info = [new_photo.id, "-".join(list(new_photo.tags)), new_photo.location, new_photo.datetime,
                      encoded_img, self.id]
        return photo_info


    def addTagToPhoto(self, id, tag):
        try:
            self.photos[id].addTag(tag)
            return True
        except KeyError:
            print("Photo with given id does not exist")

    def removeTagFromPhoto(self, id, tag):
        try:
            success = self.photos[id].removeTag(tag)
            if success:
                return f"Tag: {tag} removed from Photo(id={id})"
            return f"Photo(id={id} doesn't include given Tag: {tag})"
        except KeyError:
            print("Photo with given id does not exist")

    def setLocationOfPhoto(self, id, long, latt):
        try:
            self.photos[id].setLocation(long, latt)
            return f"Location of Photo(id={id} is set to longitude={long} and latitude={latt})"
        except KeyError:
            print("Photo with given id does not exist")

    def removeLocationFromPhoto(self, id):
        try:
            self.photos[id].removeLocation()
            return f"Location of Photo(id={id}) is removed."

        except KeyError:
            print("Photo with given id does not exist")

    def setDatetimeOfPhoto(self, id, datetime):
        try:
            self.photos[id].setDateTime(datetime)
            return True
        except KeyError:
            print("Photo with given id does not exist")

    def isCollectionSharedWithUser(fnc):
        def inner(*args):
            user = args[0]
            collection = args[1]
            if user == collection.owner or collection in user.sharedCollectionsWithMe:
                return fnc(*args)
            else:
                print(f"{collection.name} is not shared with {user.username}. {user.username} cannot inspect and "
                      f"update the collection {collection.name}.")

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
        self.views.add(my_view)
        # self.db.insert("Views", ('view_id', 'view_name', 'location_filter', 'time_filter_start', 'time_filter_end',
        #                          'col_id', 'owner_id'), my_view.id, name, "", "", "", -1, self.id)

        return my_view.id

    def shareCollection(self, shared_collection, shared_with):
        if self == shared_collection.owner:
            shared_collection.share(shared_with)
            print(f"{self.username} shared {shared_collection.name} with {shared_with.username}")
        else:
            print(f"You don't have access to share {shared_collection.name}")
            print(f"{self.username} couldn't share {shared_collection.name} with {shared_with.username}. "
                  f"Because {shared_collection.name} can be shared only by {shared_collection.owner.username} ")

    def unshareCollection(self, unshared_collection, unshared_with):
        if self == unshared_collection.owner:
            unshared_collection.unshare(unshared_with)
            print(f"{self.username} unshared {unshared_collection.name} with {unshared_with.username}")
        else:
            print(f"You don't have access to unshare {unshared_collection.name}")
            print(f"{self.username} couldn't share {unshared_collection.name} with {unshared_with.username}. "
                  f"Because {unshared_collection.name} can be shared only by {unshared_collection.owner.username} ")

    @isCollectionSharedWithUser
    def addPhotoToCollection(self, collection, photo):
        collection.addPhoto(photo)


    @isCollectionSharedWithUser
    def removePhotoFromCollection(self, collection, photo):
        collection.removePhoto(photo)

    @isCollectionSharedWithUser
    def fetchPhotoFromCollection(self, collection, ph_id):
        collection.fetchPhoto(ph_id)

    @isCollectionSharedWithUser
    def addViewToCollection(self, collection, view):
        collection.addView(view)

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
            view.setTagFilter(tag_list, conj)
        else:
            print("You don't have the access to make changes on this view")

    def setLocationRectToView(self, view, rectangle):
        print("rectangleeee" ,rectangle)
        if view in self.views or view in self.sharedViewsWithMe:
            view.setLocationRect(rectangle)
        else:
            print("You don't have the access to make changes on this view")

    def setTimeIntervalToView(self, view, start, end):
        if view in self.views or view in self.sharedViewsWithMe:
            view.setTimeInterval(start, end)
        else:
            print("You don't have the access to make changes on this view")






# myph = Photo('/Users/ipekcaglayan/Downloads/canon.jpg')
# myph.addTag('yaz')
# myph.addTag('tatil')
#
# user1 = User("ipek")
# user1_collection = user1.createCollection("Ipek's Collection")
# user2 = User("Simge")
# user3 = User("Bugris")
# user4 = User("Ege")
# user1.shareCollection(user1_collection, user2)
# user1.shareCollection(user1_collection, user3)
# user2.shareCollection(user1_collection, user4)
# user2.addPhotoToCollection(user1_collection, myph)
# myph1 = Photo('/Users/ipekcaglayan/Downloads/canon.jpg')
# print(user1_collection)
# user4.removePhotoFromCollection(user1_collection, myph)
# print(user1_collection)
# user2.removePhotoFromCollection(user1_collection, myph)
# print(user1_collection)
# user3.addPhotoToCollection(user1_collection, myph1)
# user2.fetchPhotoFromCollection(user1_collection, 1)
# user4.fetchPhotoFromCollection(user1_collection, 1)