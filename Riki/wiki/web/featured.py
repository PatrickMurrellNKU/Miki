from wiki.web import current_wiki
import time

# Main method to handle displaying the featured page
def feature():
    # First checks to remove home page if there are other pages
    pages = remove_home()
    if not pages:
        # If pages was empty, then home is the only page thus it should be displayed in place of the featured page
        index = current_wiki.index()
        page = index[0]
    else:
        # If pages wasn't empty, display the proper page
        page = choose(pages)
    return page

# Obtains a list of all the pages in the wiki and removes the home page since it doesn't need to be a featured page
def remove_home():
    index = current_wiki.index()
    pages = []
    for x in index:
        pages.append(x.url)
    i = pages.index('home')
    del index[i]
    return index

# Using time, chooses the correct page to display.  The page will change every new day
def choose(pages):
    day = int(get_time())
    length = len(pages)
    value = day % length
    return pages[value]

# Gets the time in a usable format for choose() method
def get_time():
    t = time.localtime()
    day = time.strftime("%d", t)
    return day
