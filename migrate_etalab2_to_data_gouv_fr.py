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


"""Change URLs pointing to Etalab2 CKAN to Data.gouv.fr."""


import argparse
import logging
import os
import sys

from ckan import model, plugins
from ckan.config.environment import load_environment
from paste.deploy import appconfig
from paste.registry import Registry
import pylons


app_name = os.path.splitext(os.path.basename(__file__))[0]
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

    model.repo.new_revision()
    for resource in model.Session.query(model.Resource).filter(
            model.Resource.url.like('%etalab2.fr%'),
            ):
        url = resource.url
        if url.startswith('http://ckan.etalab2.fr/'):
            resource.url = resource.url.replace('http://ckan.etalab2.fr/', 'http://www.data.gouv.fr/fr/')
        elif url.startswith('http://ckan-hetic.etalab2.fr/'):
            resource.url = resource.url.replace('http://ckan-hetic.etalab2.fr/', 'http://www.data.gouv.fr/fr/')
        elif url.startswith('http://www.etalab2.fr/'):
            resource.url = resource.url.replace('http://www.etalab2.fr/', 'http://www.data.gouv.fr/')
        else:
            print resource.url
    model.repo.commit_and_remove()

    model.repo.new_revision()
    for resource in model.Session.query(model.Resource).filter(
            model.Resource.url.like('%www.data.gouv.fr%'),
            ):
        if resource.url.startswith('http://www.data.gouv.fr/'):
            resource.url = resource.url.replace('http://www.data.gouv.fr/', 'http://new.data.gouv.fr/')
    model.repo.commit_and_remove()

    return 0


if __name__ == '__main__':
    sys.exit(main())
