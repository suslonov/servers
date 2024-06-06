#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle
import zlib
import MySQLdb

class db_nn_art(object):
    db_host="127.0.0.1"
    db_user="nn_art"
    db_passwd="nn_art"
    db_name="nn_art"
    db_port=3306

    def __init__(self, local = False):
        self.local = local

    def __enter__(self):
        port = db_nn_art.db_port
        self.db = MySQLdb.connect(host=db_nn_art.db_host, user=db_nn_art.db_user, passwd=db_nn_art.db_passwd, db=db_nn_art.db_name, port=port)
        self.cursor = self.db.cursor()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.commit()
        self.db.close()

    def add_image_to_db(self, image, ts):
        s1 = """INSERT INTO images_table (ts, image) VALUES (%s, _binary "%s")"""
        self.cursor.execute(s1, (ts, zlib.compress(pickle.dumps(image))))

    def set_image_processed(self, ts):
        s2 = 'UPDATE images_table set processed=1 where ts = "'+ str(ts) +'"'
        self.cursor.execute(s2, )

    def add_results_to_db(self, results, ts):
        s3 = """INSERT INTO results_table (ts, results) VALUES (%s, %s)"""
        self.cursor.execute(s3, (ts, results))

    def get_unprocessed_images_list(self):
        s = 'SELECT ts from images_table where processed=0'
        self.cursor.execute(s)
        l = list(self.cursor.fetchall())
        return l

    def get_image_from_db(self, ts):
        s = 'SELECT ts, image from images_table where ts = "'+ str(ts) +'"'
        i = self.cursor.execute(s)
        if i == 0:
            return None
        (_, image) = self.cursor.fetchone()
        return pickle.loads(zlib.decompress(image[1:-1]))

    def get_results_from_db(self, ts):
        s = 'SELECT ts, results FROM results_table where ts = "'+ str(ts) +'"'
        i = self.cursor.execute(s)
        if i == 0:
            return None
        (_, results) = self.cursor.fetchone()
        return results

