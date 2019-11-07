
import pandas as pd
import geopandas as gp
from shapely.geometry import Point
import matplotlib.pyplot as plt


import sys
print(sys.argv)
import argparse
import logging

logger = logging.getLogger('em.ev')

parser = argparse.ArgumentParser(description='Read EV Geometry')

parser.add_argument('--input',
	help="Input RAW file")
parser.add_argument('-n','--name',
	help="Name for data in storage",
	default="network")

parser.add_argument(
	'-d', '--debug',
	help="Print lots of debugging statements",
	action="store_const", dest="loglevel", const=logging.DEBUG,
	default=logging.WARNING,
)
parser.add_argument(
	'-v', '--verbose',
	help="Be verbose",
	action="store_const", dest="loglevel", const=logging.INFO,
)
parser.add_argument('--store',
	nargs='?', 
	default="store.h5",
	help="Path for local hdf storage")
parser.add_argument(
	'--plot',
	help="Plot",
	action="store_true",
	default=False
)


args = parser.parse_args()
print(args.name)
logging.basicConfig(level=args.loglevel)
store = pd.HDFStore(args.store)

df_location = pd.read_excel(args.input)
print('DF_location',df_location.head())
print('Columns',df_location.columns)
df_location['geometry'] = df_location.apply(lambda z: Point(z['Substation Longitude'], z['Substation Latitude']), axis=1)

df_location=df_location.rename(columns={
		"Sub Name":'ev_name',
		"Substation Longitude":"sub_long",
		"Substation Latitude":"sub_lat",
		"Longitude":'long',
		"Latitude":'lat',
		"Number":'number',
		"Name":"ev_psse_name",
		"Nom kV":'voltage'
	})

if 'long' not in df_location:
	df_location['long']=df_location['sub_long']
	df_location['lat']=df_location['sub_lat']
	
df_location=df_location[['ev_name','sub_long','sub_lat','long','lat','number','voltage','ev_psse_name']]

print(df_location.head())
print(df_location.columns)
df_location.index=df_location.number
if args.plot:
	geo_location = gp.GeoDataFrame(df_location,geometry=gp.points_from_xy(df_location.long,df_location.lat))
	geo_location.plot()
	plt.show()

store_name='{name}_bus_geometry'.format(name=args.name)
print(args.name)
print('write to {}'.format(store_name))
store.put(store_name,df_location)