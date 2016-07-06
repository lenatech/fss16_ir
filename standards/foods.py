# coding=UTF-8
import requests
from bs4 import BeautifulSoup
import sqlite3 as lite

# crawling start page
base_url = "http://www.51edu.com/chuguo/yglx/catlist1_catids_2_"
# store_posts_amount how many articles do you want to store in the database
store_posts_amount = 500

current_posts_count = 0
posts_count_per_page = 11
must_parse_pages = (store_posts_amount%posts_count_per_page) + 1
must_parse_pages = 43

current_page_number = (current_posts_count%posts_count_per_page) +1


# Insert Data using SQL execution
sql = 'insert into table_food(title, content) values(?,?)'
site_domain_url = "http://www.51edu.com"


def get_post_links_list(parse_url):
    res = requests.get(parse_url)
    soup = BeautifulSoup(res.text)
    post_links_list = []

    for post in soup.select(".pdbox"):
        post_link = site_domain_url + post.select('a')[0]['href']
        post_links_list.append(post_link)

    return post_links_list

def get_post_detail(cur, post_link):
    res = requests.get(post_link)
    res.encoding = 'gbk'
    soup = BeautifulSoup(res.text)
    post_title = soup.select('.sj-nr-title')[0].text
    post_content = soup.select('.sj-nr-con')[0].text
    post_detail = [post_title, post_content]
    cur.execute(sql, post_detail)

con = lite.connect('db.sqlite')
cur = con.cursor()
cur.execute('create table if not exists table_food (id INTEGER PRIMARY KEY NOT NULL, title varchar(100), content text)')

for k in range(must_parse_pages):
    current_page = k +1
    parse_url = base_url + str(current_page) + "/"

    current_post_links_list = get_post_links_list(parse_url)

    for m in range(len(current_post_links_list)):
        if current_posts_count <= (store_posts_amount - 1):
            current_posts_count = current_posts_count + 1
            get_post_detail(cur, current_post_links_list[m])
            print current_posts_count
        else:
            break


con.commit()
con.close()
