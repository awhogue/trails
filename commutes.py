#!/usr/bin/python

import csv, math
import gmatplotlib as gm
import folium
from geojson import LineString, MultiPoint

def load_data():
  fh = open('data/ahogue-sample.txt', 'rb')
  trails = {}
  for line in csv.reader(fh, delimiter='\t'):
    key = line[0]
    if key == 'dt': continue
    if key not in trails:
      trails[key] = []
    # Each entry is (timestamp, lat, lng, acc)
    if line[4] != '\\N': acc = int(line[4])
    else: acc = None
    trails[key].append([int(line[1]), float(line[2]), float(line[3]), acc, key])

  # Sort each day's trail by timestamp.
  for dt, points in trails.iteritems():
    trails[dt].sort(key=lambda x: x[0])

  return trails

HOME_LL = (41.0030105, -74.0785889)
WORK_LL = (40.7240291, -73.9973741)
SLACK = 0.005

def distance(p1, p2):
  def sq(x): return x * x
  return math.sqrt(sq(p1[0] - p2[0]) + sq(p1[1] - p2[1]))

def near(p1, p2):
  return distance(p1, p2) < SLACK

# Given a trail of points, return the subset that represents a commute
# from "orig" to "dest", if any.
def commute(trail, orig, dest):
  in_orig = False
  found_dest = False
  commute = []
  for t in trail:
    p = (t[1], t[2])
    if not commute:
      if not in_orig:
        if near(p, orig): in_orig = True
      else:
        if not near(p, orig):  # We left the origin.
          commute.append(t)
    else:
      if near(p, dest):
        found_dest = True
        commute.append(t)
        break
      else:
        commute.append(t)

  if found_dest:
    return commute
  else:
    return []

def all_commutes(trails, orig, dest):
  commutes = []
  for trail in trails:
    c = commute(trail, orig, dest)
    if c: commutes.append(c)
  return commutes


def trails_to_disk():
  fh = open('data/commutes.txt', 'wb')
  trails = list(load_data().iteritems())
  trails = sorted(trails, key=lambda t: int(t[1][0][0]))
  points = []
  for dt, trail in trails:
    morning = commute(trail, HOME_LL, WORK_LL)
    evening = commute(trail, WORK_LL, HOME_LL)
    if morning and evening:
      all = morning + evening
      found_jump = False
      for ii in xrange(len(all)):
        if ii == 0: continue
        if (distance(all[ii][1:3], all[ii-1][1:3]) > 0.05 or
            distance((40.868024,-74.154092), all[ii][1:3]) < 0.01 or
            distance((40.846178,-73.943481), all[ii][1:3]) < 0.01):
          found_jump = True


      if not found_jump:
        for p in morning + evening:
          points.append(p)
  
  for ii, p in enumerate(points):
    fh.write('%f,%f\n' % (p[1], p[2]))


def main():
  trails = load_data()
  trail = trails['2014-04-16']
  points = [(x[1], x[2]) for x in trail]
  bounds = gm.points_to_bounds([points])
  print 'bounds:', bounds
  (center, span) = gm.center_from_bounds(bounds)
  print 'center:', center
  (zoom, size) = gm.compute_zoom_and_size(bounds)
  map = folium.Map(location=center, zoom_start=zoom+2, tiles='Mapbox', API_key='foursquare.map-0y1jh28j',
                   width='100%', height='100%')

  points = [(x[2], x[1]) for x in trail]
  
  gjson = LineString(points)
  filename = r'trail.json'
  open('maps/' + filename, 'wb').write(str(gjson))
#   for point in trail:
#     map.circle_marker(location=[point[1], point[2]], radius=10,
#                       line_color="#FF0000", fill_color="#FF0000",
#                       popup=str(point))
  map.geo_json(geo_path=filename)
  map.create_map(path="maps/test.html")
    

if __name__ == '__main__':
  main()
