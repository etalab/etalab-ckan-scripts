#! /usr/bin/env python
# -*- coding: utf-8 -*-


# Etalab-CKAN-Scripts -- Various scripts that handle Etalab datasets in CKAN repository
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2013 Etalab
# http://github.com/etalab/etalab-ckan-scripts
#
# This file is part of Etalab-CKAN-Scripts.
#
# Etalab-CKAN-Scripts is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Etalab-CKAN-Scripts is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Migrate resources from old data.gouv.fr to static HTTP server."""


import argparse
import hashlib
import io
import json
import logging
import os
import re
import socket
import sys
import urllib
import urllib2
import urlparse

from biryani1 import baseconv, custom_conv, states, strings
from ckan import model, plugins
from ckan.config.environment import load_environment
from ckantoolbox import ckanconv
from paste.deploy import appconfig
from paste.registry import Registry
import pylons


app_name = os.path.splitext(os.path.basename(__file__))[0]
conv = custom_conv(baseconv, ckanconv, states)
log = logging.getLogger(app_name)


class MockTranslator(object):
    def gettext(self, value):
        return value

    def ugettext(self, value):
        return value

    def ungettext(self, singular, plural, n):
        if n > 1:
            return plural
        return singular


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('config', help = 'path of configuration file')
    parser.add_argument('-g', '--go', action = 'store_true', help = 'Change URLs of files')
    parser.add_argument('-v', '--verbose', action = 'store_true', help = 'increase output verbosity')

    args = parser.parse_args()
#    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.WARNING, stream = sys.stdout)
    logging.basicConfig(level = logging.INFO if args.verbose else logging.WARNING, stream = sys.stdout)
    site_conf = appconfig('config:{}'.format(os.path.abspath(args.config)))
    load_environment(site_conf.global_conf, site_conf.local_conf)

    registry = Registry()
    registry.prepare()
    registry.register(pylons.translator, MockTranslator())

    plugins.load('synchronous_search')

    bad_resources_url = set()
    while True:
        model.repo.new_revision()
        resources_found = False
        resource_index = 0
        for resource in model.Session.query(model.Resource).filter(
                model.Resource.url.like('http://www.data.gouv.fr/%'),
                ):
            resource_url, error = conv.pipe(
                conv.make_input_to_url(full = True),
                conv.not_none,
                )(resource.url, state = conv.default_state)
            if error is not None:
                continue
            resource_url = resource_url.encode('utf-8')
            if resource_url.startswith(('http://static.data.gouv.fr/', 'https://static.data.gouv.fr/')):
                continue
            if not resource_url.startswith(('http://www.data.gouv.fr/', 'https://www.data.gouv.fr/')):
                continue
            if resource_url in bad_resources_url:
                continue
            resource_url_path = urlparse.urlsplit(resource_url).path
            print resource_url
            try:
                response = urllib2.urlopen(resource_url, timeout = 30)
            except socket.timeout:
                resources_found = True
                continue
            except urllib2.HTTPError:
                bad_resources_url.add(resource_url)
                continue
            except urllib2.URLError:
                bad_resources_url.add(resource_url)
                continue
            resources_found = True
            resource_buffer = response.read()
            resource_hash = hashlib.sha256(resource_buffer).hexdigest()
            resource_url_path = '{}/{}{}'.format(resource_hash[:2], resource_hash[2:],
                os.path.splitext(resource_url_path)[-1])
            resource_path = '/tmp/resources/{}'.format(resource_url_path)
            print '   ', resource_path
            dir = os.path.dirname(resource_path)
            if not os.path.exists(dir):
                os.makedirs(dir)
            with open(resource_path, 'w') as resource_file:
                resource_file.write(resource_buffer)
            if args.go:
                resource.url = 'http://static.data.gouv.fr/{}'.format(resource_url_path)
                resource_index += 1
                if resource_index >= 5:
                    break
        if resources_found:
            model.repo.commit_and_remove()
        else:
            break

    if not args.go:
        print 'WARNING: URLs have not been modified. Transfer images then use the --go option.'

    return 0


if __name__ == '__main__':
    sys.exit(main())
