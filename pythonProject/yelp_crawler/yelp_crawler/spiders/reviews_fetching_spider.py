import scrapy
# from urllib.parse import urlparse
import urllib.parse as urlparse
from urllib.parse import parse_qs

import json
import numpy as np

from my_db_scripts.access_db import DBWorker

# ****************
#
# pattern1 = response.xpath("//a[contains(@href,'Jk5WqTfQwDGy43ikql9Y3w')]/img/@src").getall() # get all img srcs # sample review_id - Jk5WqTfQwDGy43ikql9Y3w
# pattern2 = response.xpath("//a[contains(@href,'?reviewid=')]/@href").getall() # get all review ids
# pattern3 = response.xpath("//a[contains(text(),'See all photos from')]/@href").getall() # get all the hrefs of reviews having more # of imgs that are yet to be traversed

# pattern4 = response.xpath("//li[@data-photo-id]/div/img/@src").getall() # get all the img src urls in "get all photos" page

# pattern5 = response.xpath("//a[contains(@href,'Jk5WqTfQwDGy43ikql9Y3w')]/parent::div/parent::span/parent::div/following-sibling::p/a[contains(text(),'See all photos from')]/@href").getall() # if the returned list is empty, there's no additional imgs in review. else, more imgs available
# patter6 = response.xpath("//link[contains(@href,'ios-app')]/@href").getall() # for checking biz_id
# ****************
from my_db_scripts.access_db import get_random_user_agent
from my_db_scripts.access_db import get_random_proxy

yelp_domain = "https://www.yelp.com"

offset = 0  # starts from offset + 1
limit = 10  # fetches 10 records

# use this
fetch_count = 5000     # fetches only n records

auth_key1 = "b191e20bde16ea66194744de4ee2e5cd_sr98766_ooPq87"
auth_key2 = "df55b2366d1ce0249bea17dab580f5a3_sr98766_ooPq87"

def get_all_img_src_urls_from_see_more_photos_page(see_more_photos_page_response):
    return see_more_photos_page_response.xpath("//li[@data-photo-id]/div/img/@src").getall()


class ReviewsFetchingSpider(scrapy.Spider):
    name = 'reviews'

    def start_requests(self):
        my_db_worker = DBWorker()

        for new_offset in range(fetch_count):

            reviews = my_db_worker.fetch_reviews(new_offset, 1)     # offset, limit

            print('\nnew offset: ', new_offset, 'fetched reviews:', reviews)

            for review in reviews:
                my_meta = {
                    "review": review,
                    "my_db_worker": my_db_worker,
                    # "proxy": "104.168.242.252:3128"  # get_random_proxy(),
                }

                url_to_crawl = "http://api.proxiesapi.com/" \
                               "?auth_key=auth_key2" \
                               "&url=" + review["imgs_pg_url"]

                url_to_crawl = review["imgs_pg_url"]

                print("\nurl_to_crawl: ", url_to_crawl)

                yield scrapy.Request(
                    url=url_to_crawl,
                    callback=self.parse_listing_page,
                    headers={
                        "User-Agent": get_random_user_agent()
                    },
                    meta=my_meta
                )

    def parse_listing_page(self, response):
        my_review = response.meta.get("review", "")

        print('\nreceived review in my_meta:', my_review)

        img_urls_list = response.xpath("//li[@data-photo-id]/div/img/@src").getall()
        print("\nlist of crawled img urls:", img_urls_list)

        my_review["l_img_urls_str"] = json.dumps(img_urls_list) # ''.join(img_urls_list)

        href_containing_biz_id = response.xpath("//link[contains(@href,'ios-app')]/@href").getall()
        print('\nhref containing biz id:', href_containing_biz_id)

        if href_containing_biz_id:

            parsed = urlparse.urlparse(href_containing_biz_id[0])
            qp_dict = parse_qs(parsed.query)

            biz_id_from_href = qp_dict['biz_id'][0]
            print('\nbiz id from href:', biz_id_from_href)

            if biz_id_from_href == my_review["b_id"]:
                print('biz ids matched')
                my_review["status"] = "biz ids matched"
            else:
                print('biz ids not matched')
                my_review["status"] = "biz ids not matched"

        else:
            print('\nbiz id field not found in the imgs page')
            my_review["status"] = "biz id field not found in the imgs page"

        my_db_worker_instance = response.meta.get("my_db_worker", "")
        my_db_worker_instance.dump_crawled_data_into_db(my_review)


def write_dict_to_file(my_dict):
    string_to_append = json.dumps(my_dict)
    f = open("review_id_and_img_srcs_sep_25.json", "w")
    f.write(string_to_append)
    f.close()
