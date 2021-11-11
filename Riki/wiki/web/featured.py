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
    minute = int(get_time())
    length = len(pages)
    value = minute % length
    return pages[value]


def get_time():
    t = time.localtime()
    minute = time.strftime("%M", t)
    return minute
