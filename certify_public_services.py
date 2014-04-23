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


app_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(app_name)
is_public_service_by_organization_name = {
    u'ademe': True,
    u'adt-et-ots-des-alpes-de-haute-provence': False,
    u'agence-bio': True,
    u'agence-de-l-eau-adour-garonne': False,
    u'agence-de-l-eau-rhone-mediterranee-et-corse': False,
    u'agence-des-espaces-verts-idf': False,
    u'agence-nationale-de-securite-sanitaire-de-l-alimentation-de-l-environnement-et-du-travail-anses': True,
    u'agence-nationale-pour-la-cohesion-sociale-et-l-egalite-des-chances': True,
    u'agence-nationale-pour-la-renovation-urbaine': True,
    u'agence-pour-l-enseignement-francais-a-l-etranger': True,
    u'agence-regionale-du-livre': False,
    u'agence-technique-de-l-information-sur-l-hospitalisation': True,
    u'air-lr': False,
    u'airaq': False,
    u'airpaca': False,
    u'aquitaine-europe-communication': False,
    u'arcade': False,
    u'arles-crau-camargue-montagnette': False,
    u'arts-vivants-en-ille-et-vilaine': False,
    u'asf': False,
    u'association-trans-musicales': False,
    u'atout-france-agence-de-developpement-touristique-de-la-france': True,
    u'autolib': False,
    u'autorite-de-controle-prudentiel': True,
    u'autorite-de-regulation-des-communications-electroniques-et-des-postes': True,
    u'banque-mondiale': False,
    u'bassin-adour-garonne': False,
    u'bibliotheque-nationale-de-france': True,
    u'bouches-du-rhone-tourisme': True,
    u'caisse-nationale-de-l-assurance-maladie-des-travailleurs-salaries': True,
    u'caisse-nationale-de-solidarite-pour-l-autonomie': False,
    u'cap-digital': False,
    u'cap-sciences': False,
    u'cci-territoire-de-montpellier': False,
    u'centre-des-monuments-nationaux': True,
    u'centre-national-d-art-et-de-culture-georges-pompidou': True,
    u'centre-national-du-cinema-et-de-l-image-animee': True,
    u'chambre-de-commerce-et-d-industrie-marseille-provence': False,
    u'cite-de-la-musique': True,
    u'comite-departemental-du-tourisme': False,
    u'comite-regional-de-tourisme': False,
    u'commission-d-acces-aux-documents-administratifs-cada': True,
    u'commission-nationale-consultative-des-droits-de-l-homme': True,
    u'commission-nationale-des-comptes-de-campagne-et-des-financements-politiques-cnccfp': True,
    u'communaute-du-pays-d-aix': True,
    u'communaute-urbaine-de-bordeaux': True,
    u'commune-de-brocas': True,
    u'commune-de-brocas-landes': False,
    u'commune-de-saint-andre-de-cubzac': False,
    u'cour-des-comptes': True,
    u'conseil-general-de-l-oise': True,
    u'conseil-general-de-la-gironde': True,
    u'conseil-general-de-la-manche': True,
    u'conseil-general-de-loir-et-cher': True,
    u'conseil-general-de-saone-et-loire-cg71': True,
    u'conseil-general-des-hauts-de-seine': True,
    u'conseil-general-des-landes': True,
    u'conseil-general-du-cantal': True,
    u'conseil-regional-d-aquitaine': True,
    u'conseil-regional-nord-pas-de-calais': True,
    u'conseil-superieur-de-l-audiovisuel': True,
    u'contribuables-associes': False,
    u'cooperation-pour-l-information-geographique-en-alsace-cigal': False,
    u'coulommiers': True,
    u'crige-paca': False,
    u'croix-rouge-francaise': False,
    u'data-gouv-fr': True,
    u'data-publica': False,
    u'dataveyes': False,
    u'departement-de-l-information-et-de-la-communication': False,
    u'direction-departementale-des-territoires-du-haut-rhin-68': True,
    u'driea-sit-del-2': False,
    u'easter-eggs': False,
    u'ecole-nationale-superieure-d-art-villa-arson-de-nice': True,
    u'ecole-nationale-superieure-des-metiers-de-l-image-et-du-son-la-femis': True,
    u'esrifrance': False,
    u'etablissement-public-de-la-reunion-des-musees-nationaux-et-du-grand-palais-des-champs-elysees': True,
    u'etablissement-public-du-chateau-du-musee-et-du-domaine-national-de-versailles': True,
    u'etablissement-public-du-musee-d-orsay-et-du-musee-de-l-orangerie': True,
    u'etalab': True,
    u'eurostat': False,
    u'fabrique-spinoza': False,
    u'federation-des-laboureurs-en-herbe': False,
    u'federation-nationale-des-bistrots-de-pays': False,
    u'franceagrimer-etablissement-national-des-produits-de-l-agriculture-et-de-la-mer': True,
    u'frotsi': False,
    u'gip-corse-competences': False,
    u'gironde-numerique': False,
    u'grand-lyon': True,
    u'haute-autorite-de-sante': True,
    u'haute-autorite-pour-la-diffusion-des-oeuvres-et-la-protection-des-droits-sur-internet-hadopi': True,
    u'iau-idf': False,
    u'ijba': False,
    u'ined': True,
    u'institut-francais-du-cheval-et-de-l-equitation': True,
    u'institut-national-de-l-information-geographique-et-forestiere': True,
    u'institut-national-de-l-origine-et-de-la-qualite': True,
    u'institut-national-de-la-statistique-et-des-etudes-economiques-insee': True,
    u'institut-national-de-recherches-archeologiques-preventives': True,
    u'institut-national-des-hautes-etudes-de-la-securite-et-de-la-justice': True,
    u'institut-de-recherche-et-documentation-en-economie-de-la-sante-irdes': True,
    u'jcdecaux-developer': False,
    u'kel-quartier': False,
    u'keolis': False,
    u'la-poste': True,
    u'le-perreux-sur-marne': False,
    u'le-rif': False,
    u'longjumeau': False,
    u'mairie-de-paris': True,
    u'mairie-des-lilas': True,
    u'marseille-provence-2013': False,
    u'marseille-provence-metropole': False,
    u'meteo-france': True,
    u'metropole-nice-cote-d-azur': False,
    u'ministere-de-l-agriculture-de-l-agroalimentaire-et-de-la-foret': True,
    u'ministere-de-l-ecologie-du-developpement-durable-et-de-l-energie': True,
    u'ministere-de-l-economie-et-des-finances': True,
    u'ministere-de-l-education-nationale': True,
    u'ministere-de-l-egalite-des-territoires-et-du-logement': True,
    u'ministere-de-l-enseignement-superieur-et-de-la-recherche': True,
    u'ministere-de-l-interieur': True,
    u'ministere-de-la-culture-et-de-la-communication': True,
    u'ministere-de-la-defense': True,
    u'ministere-de-la-justice': True,
    u'ministere-de-la-reforme-de-l-etat-de-la-decentralisation-et-de-la-fonction-publique': True,
    u'ministere-des-affaires-etrangeres': True,
    u'ministere-des-affaires-sociales-et-de-la-sante': True,
    u'ministere-des-sports-de-la-jeunesse-de-l-education-populaire-et-de-la-vie-associative': True,
    u'ministere-du-redressement-productif': True,
    u'ministere-du-travail-de-l-emploi-de-la-formation-professionnelle-et-du-dialogue-social': True,
    u'montpellier-territoire-numerique': False,
    u'musee-des-arts-asiatiques-guimet': True,
    u'musee-du-louvre': True,
    u'nantes-metropole': True,
    u'nosdonnees-fr': False,
    u'observatoire-francais-des-drogues-et-des-toxicomanies': True,
    u'office-national-d-information-sur-les-enseignements-et-les-professions': True,
    u'office-national-de-l-eau-et-des-milieux-aquatiques-onema': True,
    u'office-national-des-forets': True,
    u'oise-open-data': False,
    u'open-data-71': False,
    u'open-data-alsace': False,
    u'open-data-hauts-de-seine': False,
    u'open-data-nord-pas-de-calais': False,
    u'open-paca': True,
    u'openclassrooms': False,
    u'opendatasoft': False,
    u'orga': False,
    u'ouest-france': False,
    u'pays-d-aubagne-et-de-l-etoile': False,
    u'pod-product-open-data': False,
    u'pole-metier-eau-environnement-crige-paca': False,
    u'premier-ministre': True,
    u'pse-ecole-d-economie-de-paris': True,
    u'regie-autonome-des-transports-parisiens-ratp': True,
    u'regie-culturelle-regionale': False,
    u'region-alsace': True,
    u'region-ile-de-france': True,
    u'region-provence-alpes-cote-d-azur': True,
    u'region-provence-alpes-cote-d-azur-earthcase': False,
    u'region-provence-alpes-cote-d-azur-items': False,
    u'region-provence-alpes-cote-d-azur-mv2': False,
    u'rennes-metropole': True,
    u'reseau-ferre-de-france': True,
    u'reseau-sitra': False,
    u'resot-alsace': False,
    u'ressourcerie-datalocale': False,
    u'saint-maur-des-fosses': True,
    u'saint-quentin-aisne': True,
    u'san-ouest-provence': False,
    u'sarlat-la-caneda': False,
    u'secretariat-general': False,
    u'shom': True,
    u'sncf': True,
    u'societe-du-grand-paris': False,
    u'syndicat-mixte-des-transports-des-bouches-du-rhone': False,
    u'syndicat-mixte-du-pays-d-arles': False,
    u'systeme-d-information-sur-l-eau': False,
    u'theatre-national-de-l-odeon-theatre-de-l-europe': True,
    u'var-tourisme': False,
    u'ville-d-aix-en-provence': True,
    u'ville-d-arles-commune-de-saint-martin-de-crau-accm': False,
    u'ville-d-issy-les-moulineaux': True,
    u'ville-de-digne-les-bains': True,
    u'ville-de-marseille': False,
    u'ville-de-montpellier': True,
    u'ville-de-nantes': True,
    u'ville-de-rennes': True,
    u'villemomble': False,
    u'wwf': False,
    }


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

    for organization_name, is_service_public in sorted(is_public_service_by_organization_name.iteritems()):
        if not is_service_public:
            continue
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
            certified_public_service.organization_id = organization.id
            model.Session.add(certified_public_service)

    model.repo.commit_and_remove()

    return 0


if __name__ == '__main__':
    sys.exit(main())
