#! /usr/bin/env python
# -*- coding: utf-8 -*-


# Etalab-CKAN-Scripts -- Various scripts that handle Etalab datasets in CKAN repository
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2013 Emmanuel Raviart
# http://gitorious.org/etalab/etalab-ckan-scripts
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


"""Update the list of CKAN datasets in realtime by consuming fedmsg messages.."""


from setuptools import setup


setup(
    name = 'ckan-datasets-list-updater',
    version = '0.1',
    description = '',
    author = '',
    author_email = '',
    url = '',
    install_requires = ['fedmsg'],
    packages = [],
    entry_points = """
        [moksha.consumer]
        ckan-datasets-list-updater = consumer:CkanDatasetsListUpdater
        """,
    )
