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


"""Delete all datasets, related, groups, organizations, etc created by a user."""


import argparse
import logging
import os
import sys

from ckan import model, plugins
if not hasattr(model, 'PackageRelationshipRevision'):
    # Monkey patch: Add missing class to model.
    from ckan.model import package_relationship
    model.PackageRelationshipRevision = package_relationship.PackageRelationshipRevision
from ckan.config.environment import load_environment
from ckanext.etalab import model as etalab_model
from ckanext.youckan import models as youckan_model
from paste.deploy import appconfig
from paste.registry import Registry
import pylons

from biryani1 import strings


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
    parser.add_argument('user', help = 'name of email of user')
    parser.add_argument('-d', '--dry-run', action = 'store_true',
        help = "simulate harvesting, don't update CKAN repository")
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

    user_name = args.user.lower().replace('.', '-dot-').replace('@', '-at-')
    user = model.Session.query(model.User).filter(model.User.name == user_name).one()
    assert user is not None, 'Unknown user: {}'.format(user_name)

    for membership_request in model.Session.query(youckan_model.MembershipRequest).filter(
            youckan_model.MembershipRequest.user_id == user.id,
            ):
        log.warning(u'Deleting membership request: {}'.format(membership_request))
        if not args.dry_run:
            model.Session.delete(membership_request)
            model.Session.commit()

    for related in model.Session.query(model.Related).filter(model.Related.owner_id == user.id):
        log.warning(u'Deleting related: {}'.format(related))
        if not args.dry_run:
            model.Session.delete(related)
            model.Session.commit()

    if not args.dry_run:
        model.repo.new_revision()

    for user_object_role in model.Session.query(model.UserObjectRole).filter(
            model.UserObjectRole.user_id == user.id,
            model.UserObjectRole.role == 'admin',
            ):

        if user_object_role.context == 'Group':
            group = user_object_role.group
            log.warning(u'Deleting group or organization: {}'.format(group))
            if not args.dry_run:
                model.Session.query(etalab_model.CertifiedPublicService).filter(
                    etalab_model.CertifiedPublicService.organization_id == group.id,
                    ).delete()
                model.Session.delete(group)
        else:
            assert user_object_role.context == 'Package', 'Unexpected context for role: {}'.format(
                user_object_role.context)
            package = user_object_role.package

            # Delete resource_revision before purging package, to avoid IntegrityError: update or delete on table
            # "resource_group" violates foreign key constraint "resource_revision_resource_group_id_fkey" on table
            # "resource_revision".
            for resource_group in model.Session.query(model.ResourceGroup).filter(
                    model.ResourceGroup.package_id == package.id,
                    ):
                for resource_revision in model.Session.query(model.ResourceRevision).filter(
                        model.ResourceRevision.resource_group_id == resource_group.id,
                        ):
                    if not args.dry_run:
                        log.warning(u'Deleting resource_revision')
                        model.Session.delete(resource_revision)

            # Delete package_relationship_revision before purging package, to avoid IntegrityError: update or
            # delete on table "package" violates foreign key constraint
            # "package_relationship_revision_subject_package_id_fkey" on table "package_relationship_revision".
            for package_relationship_revision in model.Session.query(model.PackageRelationshipRevision).filter(
                    model.PackageRelationshipRevision.subject_package_id == package.id,
                    ):
                if not args.dry_run:
                    log.warning(u'Deleting package_relationship_revision')
                    model.Session.delete(package_relationship_revision)
            for package_relationship_revision in model.Session.query(model.PackageRelationshipRevision).filter(
                    model.PackageRelationshipRevision.object_package_id == package.id,
                    ):
                if not args.dry_run:
                    log.warning(u'Deleting package_relationship_revision')
                    model.Session.delete(package_relationship_revision)

            log.warning(u'Deleting package: {}'.format(package))
            if not args.dry_run:
                model.Session.delete(package)

    if not args.dry_run:
        model.repo.commit_and_remove()

    if not args.dry_run:
        log.warning(u'Deleting user: {}'.format(user))
        model.Session.delete(user)
        model.Session.commit()

    return 0


if __name__ == '__main__':
    sys.exit(main())
