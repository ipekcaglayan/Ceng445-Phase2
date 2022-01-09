# Ceng445-Phase2

#Simge Tekin 2306686
#Ipek Caglayan 2306090


Virtual environment can be created by running following commands:
1) virtualenv -p python3.8 venv (creates venv)
2) source venv/bin/activate (activates venv)
3) pip install -r Requirements.txt (installs necessary packages)


Commands:


CREATE_USER = 0 username password
LOGIN = 1 username password
UPLOAD_PHOTO = 2 path
ADD_TAG_TO_PHOTO = 3 photo_id tag
REMOVE_TAG_FROM_PHOTO = 4 photo_id tag
SET_LOC_OF_PHOTO = 5 photo_id long lat  tuples without space=> 5 1 (0,0,0) (10,10,10)
REMOVE_LOC_FROM_PHOTO = 6 photo_id
SET_DATETIME_OF_PHOTO = 7 photo_id yyy-mm-dd hh:mm:ss
CREATE_COLLECTION = 8 col_name
CREATE_VIEW = 9 view_name
SHARE_COLLECTION = 10 col_id shared_user_id
UNSHARE_COLLECTION =  11 col_id unshared_user_id
ADD_PHOTO_TO_COLLECTION = 12 col_id photo_id
REMOVE_PHOTO_FROM_COLLECTION = 13 col_id photo_id
SET_TAG_FILTER_TO_VIEW = 14 view_id [tag1,tag2,tag3] conj(True/False)
SET_LOC_REC_TO_VIEW = 15 view_id start_long end_long start_lat end_lat => 15 1 (0,0,0) (10,10,10) (0,0,0) (10,10,10)
SET_TIME_INTERVAL_TO_VIEW = 16 view_id start_yy-mm-dd start_hh:mm:ss end_yy-mm-dd end_hh:mm:ss
SHARE_VIEW = 17 view_id shared_user_id
UNSHARE_VIEW = 18 view_id unshared_user_id
ADD_VIEW_TO_COLLECTION = 19 col_id view_id
REMOVE_TAG_FILTER_FROM_VIEW = 20 view_id
REMOVE_LOC_FILTER_FROM_VIEW = 21 view_id
REMOVE_TIME_FILTER_FROM_VIEW = 22 view_id
DELETE_VIEW = 23 view_id
LIST = 24 C (List collections)
FETCH = 26 col_id photo_id
exit = closes client