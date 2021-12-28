import sqlite3


class Database:
    def __init__(self, conn, curs):
        self.conn = conn
        self.curs = curs
        self.curs.execute("create table if not exists Users(user_id, username, password)")
        self.curs.execute("create table if not exists Photos(ph_id, tags, location, datetime, user_id)")
        self.curs.execute("create table if not exists Collections(col_id, col_name, owner_id)")
        self.curs.execute("create table if not exists CollectionPhotos(col_id, ph_id)")
        self.curs.execute("create table if not exists Views(view_id, view_name, location_filter, "
                          "time_filter_start, time_filter_end, col_id)")
        self.curs.execute("create table if not exists ViewTags(view_id, tag)")

    def insert(self, table_name, field_names, *data):
        query = f'INSERT INTO {table_name} {field_names} VALUES ( {",".join(["?"] * len(data))})'

        self.curs.execute(query, data)
        self.conn.commit()

    def update(self, table_name, updated_inst, filter_field, *data):
        query = f'UPDATE {table_name} SET {updated_inst} = ? WHERE {filter_field} = ?;'

        self.curs.execute(query, data)
        self.conn.commit()

    def delete(self, table_name, filter_field, *data):
        query = f'DELETE FROM {table_name} WHERE {filter_field} = ?;'

        self.curs.execute(query, data)
        self.conn.commit()


