#!/usr/bin/env python

import logging
try:                     # pragma: no cover
    from urllib.request import Request, urlopen
except ImportError:      # pragma: no cover
    from urllib2 import Request, urlopen, HTTPError, URLError
from json import loads

from .dev._exceptions import ISBNLibHTTPError, ISBNLibURLError
from .dev.webservice import query
from .registry import metadata_cache

COVERZOOM = 2
NOIMGSIZE = 15666
UA = "isbntools (gzip)"

LOGGER = logging.getLogger(__name__)


def download(url, tofile=None):
    headers = {'User-Agent': UA, 'Pragma': 'no-cache'}
    request = Request(url, headers=headers)
    try:
        response = urlopen(request)
        LOGGER.debug('Request headers:\n%s', request.header_items())
    except HTTPError as e:  # pragma: no cover
        LOGGER.critical('ISBNLibHTTPError for %s with code %s [%s]',
                        url, e.code, e.msg)
        if e.code in (401, 403, 429):
            raise ISBNLibHTTPError('%s Are you are making many requests?'
                                   % e.code)
        if e.code in (502, 504):
            raise ISBNLibHTTPError('%s Service temporarily unavailable!'
                                   % e.code)
        raise ISBNLibHTTPError('(%s) %s' % (e.code, e.msg))
    except URLError as e:   # pragma: no cover
        LOGGER.critical('ISBNLibURLError for %s with reason %s',
                        url, e.reason)
        raise ISBNLibURLError(e.reason)
    content = response.read()
    noimageavailable = len(content) == NOIMGSIZE
    if noimageavailable:
        return False
    if tofile:
        content_type = response.info().getheader('Content-Type')
        _, ext = content_type.split('/')
        tofile = tofile.split('.')[0] + '.' + ext.split('-')[-1]
        with open(tofile, 'wb') as f:
            f.write(content)
    else:
        print content
    return True


def goo_id(isbn):
    # check the cache fist
    cache = metadata_cache
    if cache is not None:
        key = 'gid' + isbn
        try:
            if cache[key]:
                return cache[key]
            else:                                           # pragma: no cover
                raise  # <-- IMPORTANT: usually the caches don't return error!
        except:
            pass
    url = "https://www.googleapis.com/books/v1/volumes?q="\
          "isbn+{isbn}&fields=items/id&maxResults=1".format(isbn=isbn)
    content = query(url, user_agent=UA)
    try:
        content = loads(content)
        gid = content['items'][0]['id']
        if gid and cache is not None:
            cache[key] = gid
        return gid
    except:
        return


def google_cover(gid, isbn, zoom=COVERZOOM):
    tpl = "http://books.google.com/books/content?id={gid}&printsec=frontcover"\
          "&img=1&zoom={zoom}&edge=curl&source=gbs_api"
    url = tpl.format(gid=gid, zoom=zoom)
    tofile = isbn + '.png' if zoom > 1 else isbn + '.jpg'
    while not download(url, tofile=tofile):
        # try a smaller resolution
        zoom -= 1
        if zoom > 0:
            tofile = isbn + '.png' if zoom > 1 else isbn + '.jpg'
            url = tpl.format(gid=gid, zoom=zoom)
        else:
            return
    return tofile


def cover(isbn, size=2):
    gid = goo_id(isbn)
    return google_cover(gid, isbn, zoom=size) if gid else None