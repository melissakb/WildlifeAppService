"""Module to communicate with MongoDB"""

import gridfs
import os
import pymongo

speciesdb_name = 'speciesdb'
species_collection = 'species'
alternate_names_collection = 'alternate_names'
imagedb_name = 'imagedb'

class MongoDBConnection:
    """Class to communicate with MongoDB"""
    def __init__(self):
        self._client = pymongo.MongoClient()
        self._speciesdb = self._client[speciesdb_name]
        self._species = self._speciesdb[species_collection]
        self._alternate_names = self._speciesdb[alternate_names_collection]
        self._imagedb = gridfs.GridFS(self._client[imagedb_name])

    def find_accepted_name(self, scientific_name):
        """Search for the accepted scientific name of a species"""
        names = self._alternate_names.find_one(
            {'alternate_name': scientific_name})
        if names:
            accepted_name = names['primary_name']
        else:
            accepted_name = None
        return accepted_name

    def find_species(self, scientific_name):
        """Find a document for a species with the given scientific name

        :param scientific_name:     Scientific name of the species

        :returns:                   A taxonomy.Species object

        """
        document = self._species.find_one(
            {'scientific_name': scientific_name}, {'_id': False})
        if not document:
            accepted_name = self.find_accepted_name(scientific_name)
            document = self._species.find_one(
                {'scientific_name': accepted_name}, {'_id': False})
        return document

    def set_image_meta(self, scientific_name, value):
        self._species.find_one_and_update(
            {'scientific_name': scientific_name},
            {'$set': {'image_meta': {}}})
        for key in value:
            self._species.find_one_and_update(
                {'scientific_name': scientific_name},
                {'$set': {'image_meta.{0}'.format(key): {value[key]}}})

    def set_image_id(self, scientific_name, value):
        self._species.find_one_and_update(
            {'scientific_name': scientific_name},
            {'$set': {'image_id': value}})

    def insert_image(self, path, name):
        image = open(path, 'r')
        filename = os.path.split(path)[1]
        return self._imagedb.put(image.read(), filename=filename)