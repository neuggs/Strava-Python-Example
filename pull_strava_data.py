from stravalib import Client

client_id = '31196'
access_token_site = 'a2e9dc9caf7ebe57e8f60b7994052e27b9b929bd'
client_secret = '628d8f82fecf138a30c149b5b9b21d4a12419e47'

client = Client(access_token=access_token_site)
activities = client.get_activities(limit=3000)

sample = list(activities)[0]
sample.to_dict()

print('hi')
