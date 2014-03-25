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


"""Compute stats for an organization."""


import argparse
import csv
import json
import logging
import os
import sys
import urllib
import urllib2
import urlparse

from ckan import model
from ckan.config.environment import load_environment
from ckanext.etalab import model as etalab_model
from ckanext.youckan import models as youckan_model
from paste.deploy import appconfig
import pylons


app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)
piwik_url = u'http://stats.data.gouv.fr/'
weckan_url = u'http://www.data.gouv.fr/'


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('organization', help = 'name of organization')
    parser.add_argument('config', help = 'path of configuration file')
    parser.add_argument('-v', '--verbose', action = 'store_true', help = 'increase output verbosity')

    args = parser.parse_args()
#    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.WARNING, stream = sys.stdout)
    logging.basicConfig(level = logging.INFO if args.verbose else logging.WARNING, stream = sys.stdout)
    site_conf = appconfig('config:{}'.format(os.path.abspath(args.config)))
    load_environment(site_conf.global_conf, site_conf.local_conf)

    organization = model.Session.query(model.Group).filter(
        model.Group.name == args.organization,
        model.Group.is_organization == True,
        ).first()
    assert organization is not None
    with open('/tmp/{}-demandes-adhesion.csv'.format(organization.name), 'w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter = ';', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
        csv_writer.writerow([
            'ID',
            'Nom',
            'Courriel',
            'Statut',
            'Date création',
            'Commentaire',
            'Date gestion',
            'Commentaire de refus',
            ])
        for membership_request in organization.membership_requests:
            user = membership_request.user
            csv_writer.writerow([
                unicode(cell).encode('utf-8')
                for cell in (
                    user.name,
                    user.fullname,
                    user.email,
                    membership_request.status,
                    membership_request.created,
                    membership_request.comment,
                    membership_request.handled_on,
                    membership_request.refusal_comment,
                    )
                ])

    with open('/tmp/{}-jeux-de-donnees.csv'.format(organization.name), 'w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter = ';', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
        csv_writer.writerow([
            'URL',
            'Ressources - Titres',
            'Ressources - URL',
            'Réutilisations - Titres',
            'Réutilisations - URL',
            'Alertes - Type',
            'Alertes - Date création',
            'Alertes - Commentaire',
            'Alertes - Date fermeture',
            'Alertes - Commentaire fermeture',
            'Inscrits (Utiles)',
            'Pages vues',
            'Visites',
            'Taux de sortie',
            ])
        for package in model.Session.query(model.Package).filter(
                model.Package.owner_org == organization.id,
                model.Package.state != 'deleted',
                ):
            log.info(package.name)

            row = []
            row.append(u'http://www.data.gouv.fr/fr/dataset/{}'.format(package.name))

            community_resource_names = []
            community_resource_urls = []
            for community_resource in package.community_resources:
                community_resource_names.append(community_resource.name)
                community_resource_urls.append(community_resource.url)
            row.extend([u'\n'.join(community_resource_names), u'\n'.join(community_resource_urls)])

            related_titles = []
            related_urls = []
            for related in package.related:
                related_titles.append(related.title)
                related_urls.append(related.url)
            row.extend([u'\n'.join(related_titles), u'\n'.join(related_urls)])

            alerts_type = []
            alerts_created = []
            alerts_comment = []
            alerts_closed = []
            alerts_close_comment = []
            for alert in package.alerts:
                alerts_type.append(alert.type)
                alerts_created.append(unicode(alert.created))
                alerts_comment.append(alert.comment or u'')
                alerts_closed.append(unicode(alert.closed))
                alerts_close_comment.append(alert.close_comment or u'')
            row.extend([
                u'\n'.join(alerts_type),
                u'\n'.join(alerts_created),
                u'\n'.join(alerts_comment),
                u'\n'.join(alerts_closed),
                u'\n'.join(alerts_close_comment),
                ])

            followers_count = 0
            for following in model.Session.query(model.UserFollowingDataset).filter(
                    model.UserFollowingDataset.object_id == package.id,
                    ):
                user = model.Session.query(model.User).filter(
                    model.User.id == following.follower_id,
                    ).first()
                if user is None:
                    continue
                # user.name, user.fullname, user.email
                followers_count += 1
            row.append(followers_count)

            stats_url = urlparse.urljoin(piwik_url, u'index.php?{}'.format(
                urllib.urlencode((
                    ('date', 'today'),
                    ('format', 'JSON'),
                    ('idSite', '1'),
                    ('method', 'Actions.getPageUrls'),
                    ('module', 'API'),
                    ('period', 'month'),
                    ('segment', 'pageUrl=={}'.format(urlparse.urljoin(weckan_url, 'fr/dataset/{}'.format(package.name)))),
                    )),
                )).replace('%2C', ',').replace('%3D%3D', '==').replace('%5B', '[').replace('%5D', ']')
            response = urllib2.urlopen(stats_url)
            response_json = json.loads(response.read())
            if response_json:
                response_json = response_json[0]
                row.extend([response_json['nb_hits'], response_json['nb_visits'], response_json['exit_rate']])
            else:
                row.extend([0, 0, 0])

            csv_writer.writerow([
                unicode(cell).encode('utf-8')
                for cell in row
                ])

    return 0


if __name__ == '__main__':
    sys.exit(main())
