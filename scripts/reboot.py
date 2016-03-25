#!/usr/bin/env python

from __future__ import print_function

import requests
import re
import hashlib
import base64


def login(baseurl, username, password):
    s = requests.Session()
    r = s.get(baseurl + "html/index.html")
    csrf_tokens = grep_csrf(r.text)

    s.headers.update({
        '__RequestVerificationToken': csrf_tokens[0]
    })

    # test token on statistics api
    # r = s.get(baseurl + "api/monitoring/statistic-server")

    data = login_data(username, password, csrf_tokens[0])
    r = s.post(baseurl + "api/user/login", data=data)

    s.headers.update({
        '__RequestVerificationToken': r.headers["__RequestVerificationTokenone"]
    })

    return s


def reboot(baseurl, session):
    s.post(baseurl + "api/device/control", data='<?xml version="1.0" encoding="UTF-8"?><request><Control>1</Control></request>')


def grep_csrf(html):
    pat = re.compile(r".*meta name=\"csrf_token\" content=\"(.*)\"", re.I)
    matches = (pat.match(line) for line in html.splitlines())
    return [m.group(1) for m in matches if m]


def login_data(username, password, csrf_token):
    def encrypt(text):
        m = hashlib.sha256()
        m.update(text)
        return base64.b64encode(m.hexdigest())

    password_hash = encrypt(username + encrypt(password) + csrf_token)

    return '<?xml version="1.0" encoding="UTF-8"?><request><Username>%s</Username><Password>%s</Password><password_type>4</password_type></request>' % (username, password_hash)


WEB = "http://192.168.1.1/"
USERNAME = "admin"
PASSWORD = "admin"

if __name__ == "__main__":
    s = login(WEB, USERNAME, PASSWORD)
    reboot(WEB, s)
