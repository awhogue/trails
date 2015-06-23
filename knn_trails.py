#!/usr/bin/python

# Build a markov chain out of a user's pilgrim trails.
#
# Input fields are { dt, timestamp, lat, lng, llacc, speed } as per http://hive/hive_jobs/59453

import csv, datetime, glob, json, sys, urllib2
import tokens
import numpy as np
from sklearn.neighbors import NearestNeighbors

def key(lat, lng):
  return '%.2f,%.2f' % (round(lat, 2), round(lng, 2))

LIMIT = 1000000

def load(input):
  points = []  # [timestamp (secs), lat, lng, llacc]
  known_timestamps = {}

  print 'Loading %s' % input
  reader = csv.reader(open(input, 'rb'), delimiter='\t', quotechar='"')
  for line in reader:
    if line[0] == 'dt': continue
    if line[1] in known_timestamps: continue

    points.append((int(line[1]) / 1000, float(line[2]), float(line[3]), int(line[4])))
    known_timestamps[line[1]] = 1

    if len(known_timestamps) == LIMIT: break
    
  points.sort(key=lambda x: x[0])
  return points

def model_from_point(point):
  dt = datetime.datetime.fromtimestamp(point[0])
  return [
    (dt.hour * 60 + dt.minute) * 10,       # Minute of day, multiplied by 10 for weight
    dt.weekday() * 1000,                   # Day of week, multiplied by weight
    point[1] * 100000, point[2] * 100000,  # Multiply lat/lng by 100000 to get ~1 meter accuracy
    point[3]                               # Throwing this in here, not sure how to weight?
  ]

def create_model(points):
  X = np.array(map(model_from_point, points))
  nbrs = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(X)
  return nbrs

def point_to_string(point):
  dt = datetime.datetime.fromtimestamp(point[0])
  venue = venuesearch(point[1], point[2])
  return '%s at %s' % (dt.strftime('%a %b %d, %Y %I:%M %p'), venue)

def venuesearch(lat, lng):
  api_url = 'https://api.foursquare.com/v2/venues/search?oauth_token=%s&v=20150622&ll=%f,%f' % (tokens.TOKEN, lat, lng)
  content = urllib2.urlopen(api_url).read()
  response = json.loads(content)['response']
  if not response['confident']: conf = ' (low confidence)'
  else: conf = ''
  return '%s (%f, %f)%s' % (response['venues'][0]['name'], lat, lng, conf)

def get_future_point(points, point_index, future_time_in_secs):
  future_point = None
  best_diff = sys.maxint
  goal_time = points[point_index][0] + future_time_in_secs
  for point in points[point_index+1:point_index+100]:
    diff = abs(point[0] - goal_time)
    if diff < best_diff:
      future_point = point
      best_diff = diff
  return future_point  

def get_future_trail(points, point_index, future_time_in_secs):
  future_points = []
  goal_time = points[point_index][0] + future_time_in_secs
  for point in points[point_index+1:point_index+100]:
    if point[0] <= goal_time:
      future_points.append(point)

  return future_points

def main():
  if len(sys.argv) <= 2:
    test_point = (1431002436, 41.0029563, -74.0784164, 30)
  else:
    test_point = (int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]))

  print 'Testing point: %s' % point_to_string(test_point)
    
  points = load(sys.argv[1])
  model = create_model(points)
  closest = model.kneighbors([model_from_point(test_point)], return_distance=False)

  for close_point_idx in closest[0]:
    close_point = points[close_point_idx]
    print '\t=> %s' % point_to_string(close_point)
    print '\t  In an hour you\'ll be at %s' % point_to_string(get_future_point(points, close_point_idx, 60*60))

#   for close_point_idx in closest[0]:
#     trail = get_future_trail(points, close_point_idx, 60*60)
#     print trail

if __name__ == '__main__':
  main()

