from stravalib import Client

# Update with your data from Strava
client_id = '*****'
access_token_site = '***************************'
client_secret = '***************************'

client = Client(access_token=access_token_site)
activities = client.get_activities(limit=3000)

sample = list(activities)[0]
sample.to_dict()

print('hi')
