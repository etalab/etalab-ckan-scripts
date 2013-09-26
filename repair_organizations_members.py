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


"""Repair members of organizations, to ensure that they match the owners of packages."""


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

    for package in model.Session.query(model.Package).filter(
            model.Package.owner_org != None,
            model.Package.state != 'deleted',
            ):
        organization = model.Session.query(model.Group).get(package.owner_org)
        if organization is None and package.state != 'active':
            log.warning(u'Purging package "{}" whose organization is missing'.format(package.name))
            package.purge()
            continue
        assert organization is not None
        assert organization.is_organization
        assert organization.state != 'deleted', str((organization, package))
        member = model.Session.query(model.Member).filter(
            model.Member.group_id == organization.id,
            model.Member.state == 'active',
            model.Member.table_id == package.id,
            ).first()
        if member is None:
            log.warning(u'Repairing organization "{}" package "{}" membership'.format(organization.name, package.name))
            member = model.Session.query(model.Member).filter(
                model.Member.group_id == organization.id,
                model.Member.table_id == package.id,
                ).first()
            assert member is not None
            if member.capacity != 'organization':
                member.capacity = 'organization'
            member.state = 'active'
            assert member.table_name == 'package'
        else:
            if member.capacity != 'organization':
                log.warning(u'Repairing capacity organization "{}" package "{}" membership'.format(organization, package))
                member.capacity = 'organization'
            assert member.table_name == 'package'
            continue

    for organization in model.Session.query(model.Group).filter(
            model.Group.is_organization == True,
            model.Group.state == 'active',
            ):
        for member in model.Session.query(model.Member).filter(
                model.Member.capacity != 'organization',
                model.Member.group_id == organization.id,
                model.Member.state == 'active',
                model.Member.table_name == 'package',
                ):
            package = model.Session.query(model.Package).get(member.table_id)
            if package is None:
                log.warning(u"Purging member of organization {} with capacity {}, whose package doesn't exist".format(
                    organization.name, member.capacity))
                member.purge()
            else:
                log.warning(u'Repairing capacity organization "{}" package "{}" membership'.format(organization.name, package))
                member.capacity = 'organization'

    member_by_table_id_by_group_id = {}
    for member in model.Session.query(model.Member).filter(
            model.Member.state == 'active',
            ):
        member_by_table_id = member_by_table_id_by_group_id.setdefault(member.group_id, {})
        if member.table_id in member_by_table_id:
            log.warning(u"Group {} contains several time the same object:\n  {}\n {}".format(member.group.name,
                member_by_table_id[member.table_id], member))
            member.purge()
            continue
        member_by_table_id[member.table_id] = member

    model.repo.commit_and_remove()

    return 0


if __name__ == '__main__':
    sys.exit(main())
