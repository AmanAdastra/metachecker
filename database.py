import pymongo
from common_layer import constants
from pymongo import MongoClient

mongodb_uri = f"{constants.MONGODB_URL}"
client = MongoClient(mongodb_uri)
db_name = pymongo.uri_parser.parse_uri(mongodb_uri)['database']
db = client[f'{db_name}']

                
