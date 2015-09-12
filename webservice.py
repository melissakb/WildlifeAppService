import flask
import flask_restful
from flask_restful import reqparse
import json

import species_list

app = flask.Flask(__name__)
api = flask_restful.Api(app)


class Species(flask_restful.Resource):
    def __init__(self):
        self._species_manager = species_list.SpeciesManager()

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('latitude', type=float)
        parser.add_argument('longitude', type=float)

        args = parser.parse_args()
        latitude = args['latitude']
        longitude = args['longitude']

        species_list = self._species_manager.list_species(latitude, longitude)
        print species_list
        return json.dumps({'species': species_list})

api.add_resource(Species, '/species')

if __name__ == '__main__':
    app.run(host='ec2-52-26-193-102.us-west-2.compute.amazonaws.com', debug=True)