import logging

import api.bison_api
import database.mongodb
import geography


class SpeciesManager():
    def __init__(self):
        self._db_con = database.mongodb.MongoDBConnection()

    def list_species(self, latitude, longitude, radius=10):
        """Get a list of species that are recorded within the given radius of the
        given latitude and longitude

        :param latitude:        Latitude
        :param longitude:       Longitude
        :param radius:          Radius in kilometers

        :returns:               A list of taxa.Species

        """
        area_of_interest = geography.get_circle_coordinates(
            latitude, longitude, radius=radius)

        search_result = api.bison_api.search(area_of_interest)
        if not search_result:
            return None
        species_names = search_result.species_names
        species_list = []
        for species_name in species_names:
            species = self._db_con.find_species(species_name)
            if species:
                species_list.append(species)
        return species_list
