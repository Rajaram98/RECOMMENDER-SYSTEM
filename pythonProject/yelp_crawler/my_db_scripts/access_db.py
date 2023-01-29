# -*- coding: utf-8 -*-
"""
Created on Wed Sep 23 12:04:46 2020

@author: Soofi Hussain S M M
"""

import pymysql
from urllib.parse import urlparse
from urllib.parse import parse_qs
import json
import random


def replace_space_with_symbol(t_string, symbol):
    return t_string.replace(' ', symbol).lower()


def replace_symbol1_with_symbol2(t_string, symbol1, symbol2):
    return t_string.replace(symbol1, symbol2).lower()


class DBWorker:
    user = "root"
    password = "P@ssw0rd"
    yelp_domain = "https://www.yelp.com"

    def __init__(self):
        self.my_db = self.create_connection_to_db()
        self.my_cursor = self.get_cursor()

    # creating connection
    def create_connection_to_db(self):
        return pymysql.connect(
            host="localhost",
            user=self.user,
            password=self.password,
            database="yelp"
        )

    def get_cursor(self):
        return self.my_db.cursor()

    def show_dbs(self):
        print("\nlist of dbs: ")
        self.my_cursor.execute("SHOW DATABASES")
        for x in self.my_cursor:
            print(x)

    def show_tables(self):
        print("\nlist of tables: ")
        self.my_cursor.execute("SHOW TABLES")
        for x in self.my_cursor:
            print(x)

    def execute_query(self, query):
        self.my_cursor.execute(query)
        return self.my_cursor.fetchall()

        # self.get_cursor(self).execute(self, query)
        # return self.get_cursor(self).fetchall()

    def get_imgs_pg_url(self, r_dict):
        query = "SELECT * FROM yelp.business where business_id = '" + r_dict['b_id'] + "'"
        res = self.execute_query(query)
        b_name = res[0][1]
        b_city = res[0][3]

        b_name = replace_symbol1_with_symbol2(b_name, "'", "")
        b_name = replace_symbol1_with_symbol2(b_name, "&", "and")

        imgs_pg_url = self.yelp_domain + '/biz/' + replace_space_with_symbol(b_name,
                                                                             '-') + '-' + replace_space_with_symbol(
            b_city,
            '-') + '?osq=' + replace_space_with_symbol(
            b_name, '+')
        # print(imgs_pg_url)  # business details page

        imgs_pg_url = self.yelp_domain + "/biz_photos/" + replace_space_with_symbol(b_name,
                                                                                    '-') + "-" + replace_space_with_symbol(
            b_city, '-') + "?userid=" + r_dict["u_id"]
        # print(imgs_pg_url)
        return imgs_pg_url

    def dump_crawled_data_into_db(self, r_dict):
        query = "INSERT INTO yelp.review_images (review_id, business_id, user_id, img_url_list, constructed_url, status) VALUES (%s, %s, %s, %s, %s, %s)"
        # val = tuple(r_dict.values())    # dont wanna trust the python dict in giving ordered values
        val = (r_dict['r_id'], r_dict['b_id'], r_dict['u_id'], r_dict['l_img_urls_str'], r_dict['imgs_pg_url'],
               r_dict['status'])
        self.my_cursor.execute(query, val)
        self.my_db.commit()

    def fetch_reviews(self, offset, limit):
        t_list = []
        # sub_query1 for fetching review ids not crawled earlier
        # and sub_q2 for fetching business ids in phoenix
        raw_q = "SELECT * FROM yelp.review r " \
                "WHERE r.review_id not in (SELECT distinct(ri.review_id) from yelp.review_images ri ) " \
                "and " \
                "r.business_id in " \
                "(SELECT distinct(b.business_id) FROM " \
                "yelp.business b WHERE b.city in ('phoenix')) " \
                "LIMIT " + str(limit) + " OFFSET " + str(offset)
        res = self.execute_query(raw_q)

        # res = self.execute_query("SELECT * FROM yelp.review LIMIT " + str(limit) + " OFFSET " + str(offset))

        for i, record in enumerate(res):
            print('\nrecord:', offset + i + 1)

            r_id = record[0]
            u_id = record[1]
            b_id = record[2]

            r_dict = {'r_id': r_id, 'b_id': b_id, 'u_id': u_id}
            imgs_pg_url = self.get_imgs_pg_url(r_dict)
            r_dict["imgs_pg_url"] = imgs_pg_url

            print("\nurl:", imgs_pg_url)
            print("\nr_dict: ", r_dict)

            t_list.append(r_dict)

        return t_list


def get_random_user_agent():
    file_path = "D:/my files/doms/research/projects/mmalfm/code/soofi yelp code/user_agents.txt"
    ua = ""
    no_of_lines_in_file = 842

    try:
        with open(file_path) as fp:
            for i, line in enumerate(fp):
                lucky_no = random.randint(0, no_of_lines_in_file)
                if i == lucky_no:
                    ua = line
                    break
    except:
        ua = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"

    return ua


def get_random_proxy():
    file_path = "D:/my files/doms/research/projects/mmalfm/code/soofi yelp code/proxy-list.txt"
    my_proxy = ""
    no_of_lines_in_file = 400

    try:
        with open(file_path) as fp:
            for i, line in enumerate(fp):
                lucky_no = random.randint(0, no_of_lines_in_file)
                if i == lucky_no:
                    my_proxy = line
                    break
    except:
        my_proxy = ""

    return my_proxy
