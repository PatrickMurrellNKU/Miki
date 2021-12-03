#!/Users/smcho/virtualenv/riki/bin/python

# -*- coding: utf-8 -*-
import os
import threading
import wiki.web.email

from wiki import create_app

directory = os.getcwd()
app = create_app(directory)


if __name__ == '__main__':
    x = threading.Thread(target=wiki.web.email.email())
    app.run(host='127.0.0.1', debug=True)
    x.start()

