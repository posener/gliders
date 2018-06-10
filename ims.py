import requests

_IMS_AUTH = {'Authorization': 'ApiToken 1a901e45-9028-44ff-bd2c-35e82407fb9b'}

session = requests.Session()
session.headers = _IMS_AUTH
