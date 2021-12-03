from wiki.web import current_wiki
import time


def feature():
    pages = remove_home()
    if not pages:
        index = current_wiki.index()
        page = index[0]
    else:
        page = choose(pages)
    return page


def remove_home():
    index = current_wiki.index()
    pages = []
    for x in index:
        pages.append(x.url)
    i = pages.index('home')
    del index[i]
    return index


def choose(pages):
    day = int(get_time())
    length = len(pages)
    value = day % length
    return pages[value]


def get_time():
    t = time.localtime()
    day = time.strftime("%d", t)
    return day
