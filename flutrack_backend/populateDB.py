from pymongo import MongoClient
import requests
import os
import pprint

geo_api_key = os.environ.get('GEOLOCATION_KEY')
mongo_uri = os.environ.get('MONGOLAB_URI')
if mongo_uri:
    client = MongoClient(mongo_uri)
    print('client connected')
    db = client.heroku_k99m6wnb
    db.tweets.drop()
    cities = db.cities
    tweets = db.tweets
    cursor = cities.find()
else:
    client = MongoClient('mongodb://localhost:27017/')
    db = client.flutrack
    cities = db.cities
    tweets = db.tweets


def populate_from_flutrack_api():
    r = requests.get("http://api.flutrack.org/?time=28")
    data = r.json()
    populate_from_json(data)


def populate_from_json(data):
    results = []
    for tweet in data:
        lat = tweet['latitude']
        lng = tweet['longitude']
        city = lookup_city_name(lat, lng)
        results.append({'text': tweet['tweet_text'], 'city': city, 'date': tweet['tweet_date']})

    tweets.insert(results)


def populate_from_txt(file):
    with open(file) as f:
        index = 0
        for row in f:
            row = row.split(sep=',')
            json = requests.get('https://maps.googleapis.com/maps/api/geocode/json',
                                {'key': os.environ.get('GEOLOCATION_KEY'), 'address': row[0]}).json()
            cities.insert({
                'index': index,
                'zone': row[2].strip('\n'),
                'city': row[0],
                'location': json['results'][0]['geometry']['location'],
                'bounding_box': json['results'][0]['geometry']['bounds'],
                'population': row[1].strip('\n')
            })
            index += 1




def lookup_city_name(lat, lng):
    for document in cursor:
        bounds = document['bounding_box']
        if is_within_bounds(lat, lng, bounds):
            return document['city']
    cursor.rewind()
    return "Unknown city"
    # latlng = lat + ',' + lng
    # geo_api_key = os.environ.get('GEOLOCATION_KEY')
    # params = {
    #     'latlng': latlng,
    #     'key': geo_api_key,
    #     'result_type': 'locality'
    # }
    # url = 'https://maps.googleapis.com/maps/api/geocode/json'
    # result = requests.get(url, params).json()
    # if len(result['results']) > 0:
    #     for component in result['results'][0]['address_components']:
    #         if 'locality' in component['types']:
    #             return component['long_name']
    # # else:
    #     return 'Unknown city'


def is_within_bounds(lat, lng, box):
    return float(box['southwest']['lat']) < float(lat) < float(box['northeast']['lat']) and float(
            box['southwest']['lng']) < float(lng) < float(box['northeast']['lng'])


if __name__ == '__main__':
    # populate_from_txt('../prediction/data/dummypopulation.csv')

    populate_from_flutrack_api()
    # cities_array = []
    # cursor = cities.find()
    # for city in cursor:
    #     cities_array.append(city['city'])
    #
    # counter = 0
    # cursor = tweets.find()
    # for tweet in cursor:
    #     if tweet['city'] in cities_array:
    #         counter += 1
    #
    # print(counter)
