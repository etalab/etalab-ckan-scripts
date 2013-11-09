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


"""Add main postal distribution to each territory kind/code in territorial_coverage extra fields."""


import argparse
import json
import logging
import os
import sys
import urllib
import urllib2
import urlparse

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
    parser.add_argument('-t', '--territoria-url', help = 'Territoria URL', required = True)
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

    kind_code_name_by_kind_code = {}
    for package_extra in model.Session.query(model.PackageExtra).filter(
            model.PackageExtra.key == 'territorial_coverage',
            ):
        if package_extra.value == 'Coutry/FR':
            kind_code_name = 'Country/FR/FRANCE'
        elif package_extra.value == 'InternationalOrganization/EU':
            kind_code_name = 'InternationalOrganization/UE/UNION EUROPEENNE'
        elif package_extra.value.count('/') == 1:
            kind_code_name = kind_code_name_by_kind_code.get(package_extra.value)
            if kind_code_name is None:
                kind, code = package_extra.value.split('/')
                try:
                    response = urllib2.urlopen(urlparse.urljoin(args.territoria_url,
                        '/api/v1/territory?{}'.format(urllib.urlencode(dict(
                            code = code,
                            kind = kind,
                            ), doseq = True))))
                except urllib2.HTTPError, response:
                    print package_extra.value
                    raise
                response_dict = json.loads(response.read())
                main_postal_distribution = response_dict['data']['main_postal_distribution']
                kind_code_name_by_kind_code[package_extra.value] = kind_code_name = u'/'.join([kind, code,
                    main_postal_distribution])
                print kind_code_name
        else:
            continue
        package = package_extra.package
        if package.private or package.state != 'active':
            log.warning(u'Territorial coverage of package {} must be manually corrected'.format(package.name))
            continue
        package_extra.value = kind_code_name

    model.repo.commit_and_remove()

    return 0


if __name__ == '__main__':
    sys.exit(main())
