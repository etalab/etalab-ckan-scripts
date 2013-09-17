#! /usr/bin/env python
# -*- coding: utf-8 -*-


# Etalab-CKAN-Scripts -- Various scripts that handle Etalab datasets in CKAN repository
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2013 Emmanuel Raviart
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


"""Certify organizations that are public services."""


import argparse
import logging
import os
import sys

from ckan import model, plugins
from ckan.config.environment import load_environment
from ckanext.etalab import model as etalab_model
from paste.deploy import appconfig
from paste.registry import Registry
import pylons
import sqlalchemy as sa
import sqlalchemy.exc
from sqlalchemy import sql


app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)
public_services_name = (
    u'agence-bio',
    u'agence-de-services-et-de-paiement',
    u'agence-nationale-de-securite-sanitaire-de-l-alimentation-de-l-environnement-et-du-travail',
    u'agence-nationale-pour-la-cohesion-sociale-et-l-egalite-des-chances',
    u'agence-nationale-pour-la-renovation-urbaine',
    u'agence-pour-l-enseignement-francais-a-l-etranger',
    u'agence-technique-de-l-information-sur-l-hospitalisation',
    u'atout-france-agence-de-developpement-touristique-de-la-france',
    u'autorite-de-controle-prudentiel-agent-comptable',
    u'autorite-de-regulation-des-communications-electroniques-et-des-postes',
    u'bibliotheque-nationale-de-france',
    u'caisse-nationale-de-l-assurance-maladie-des-travailleurs-salaries',
    u'centre-national-du-cinema-et-de-l-image-animee',
    u'conseil-superieur-de-l-audiovisuel',
    u'franceagrimer-etablissement-national-des-produits-de-l-agriculture-et-de-la-mer',
    u'haute-autorite-de-sante',
    u'haute-autorite-pour-la-diffusion-des-oeuvres-et-la-protection-des-droits-sur-internet',
    u'institut-francais-du-cheval-et-de-l-equitation',
    u'institut-national-de-l-information-geographique-et-forestiere',
    u'institut-national-de-l-origine-et-de-la-qualite',
    u'institut-national-de-la-statistique-et-des-etudes-economiques-insee',
    u'institut-national-des-hautes-etudes-de-la-securite-et-de-la-justice-departement-observatoire-nation',
    u'la-poste',
    u'meteo-france',
    u'ministere-de-l-agriculture-de-l-agroalimentaire-et-de-la-foret',
    u'ministere-de-l-ecologie-du-developpement-durable-et-de-l-energie',
    u'ministere-de-l-economie-et-des-finances',
    u'ministere-de-l-education-nationale',
    u'ministere-de-l-egalite-des-territoires-et-du-logement',
    u'ministere-de-l-enseignement-superieur-et-de-la-recherche',
    u'ministere-de-l-enseignement-superieur-et-de-la-recherche-departement-des-outils-d-aide-au-pilotage',
    u'ministere-de-l-interieur',
    u'ministere-de-la-culture-et-de-la-communication',
    u'ministere-de-la-defense',
    u'ministere-de-la-justice',
    u'ministere-des-affaires-etrangeres',
    u'ministere-des-sports-de-la-jeunesse-de-l-education-populaire-et-de-la-vie-associative',
    u'ministere-du-travail-de-l-emploi-de-la-formation-professionnelle-et-du-dialogue-social',
    u'observatoire-francais-des-drogues-et-des-toxicomanies',
    u'office-national-d-information-sur-les-enseignements-et-les-professions',
    u'office-national-de-l-eau-et-des-milieux-aquatiques',
    u'office-national-des-forets',
    u'premier-ministre',
    u'regie-autonome-des-transports-parisiens-ratp',
    u'reseau-ferre-de-france',
    u'societe-nationale-des-chemins-de-fer-francais',
    )


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

    revision = model.repo.new_revision()

    for organization_name in public_services_name:
        organization = model.Session.query(model.Group).filter(
            model.Group.is_organization == True,
            model.Group.name == organization_name,
            ).first()
        if organization is None:
            log.warning(u'Unknown organization: {}'.format(organization_name))
            continue
        if organization.certified_public_service is None:
            log.info(u'Certifying "{}" as public service'.format(organization_name))
            certified_public_service = etalab_model.CertifiedPublicService()
            certified_public_service = etalab_model.CertifiedPublicService()
            certified_public_service.organization_id = organization.id
            model.Session.add(certified_public_service)

    model.repo.commit_and_remove()

    return 0


if __name__ == '__main__':
    sys.exit(main())
