"""Module to make calls to the BISON API"""

import logging
import requests
from collections import Counter

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def search(area_of_interest, basis_of_observation='observation',
           count=1000000):
    """Wrapper around the BISON search endpoint

    :param area_of_interest:        A list of tuples (latitude, longitude)
                                        representing a well-known text polygon
                                        to search
    :param basis_of_observation:    Basis of observation to include in the
                                        results
    :param count:                   Number of results to return

    :returns:                       A BisonSearchResult object

    """
    url = 'http://bison.usgs.ornl.gov/api/search.json?'

    aoi = ','.join(['{0} {1}'.format(xy[1], xy[0]) for xy in area_of_interest])
    params = {'aoi': 'POLYGON(({0}))'.format(aoi),
              'basisOfObservation': basis_of_observation,
              'count': count}
    response = requests.get(url, params=params)

    if response.status_code != requests.codes.ok:
        logging.debug('BISON Search API returned status code {0}'.format(
            response.status_code))
        return None
    return BisonSearchResult(response.json())


class BisonSearchResult:
    """Class to represent the response of a call to the search endpoint of the
    BISON Search API

    :param api_result:      A JSON dictionary representing the response body
                                of a call to the search endpoint of the BISON
                                Search API

    """

    def __init__(self, api_result):
        self.total = api_result['total']
        self.georeferenced = api_result['georeferenced']
        self.occurences = api_result['occurrences']['legend']
        self.counties = api_result['counties']
        self.states = api_result['states']
        self.search_time = api_result['searchTime']
        self.offset = api_result['offset']
        self.items_per_page = api_result['itemsPerPage']
        self._data = api_result['data']

    @property
    def species_names(self):
        """Get a list of the unique species in the search result, in order of
        descending number of occurrences

        :returns:       A list of scientific species names

        """
        species_counter = Counter()
        for record in self._data:
            species_counter[record['name']] += 1

        ordered_species = species_counter.most_common()
        filtered_species = []
        # If a name has three words, it is a subspecies. Convert it to a
        # species name by removing the subspecies name (third word)
        for species_name in ordered_species:
            if len(species_name[0].split()) == 2:
                filtered_species.append(species_name)
            elif len(species_name[0].split()) == 3:
                name = (' '.join(species_name[0].split()[0:2]),
                        species_name[1])
                filtered_species.append(name)

        species_counter = Counter()
        for species in ordered_species:
            species_counter[species[0]] += species[1]
        ordered_species = [species[0]
                           for species in species_counter.most_common()]
        return ordered_species
