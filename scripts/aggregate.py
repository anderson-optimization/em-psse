
import pandas as pd
import geopandas as gp
from shapely.geometry import Point
import matplotlib.pyplot as plt

import glob
import os.path

import argparse
import logging

logger = logging.getLogger('em.aggregate')

parser = argparse.ArgumentParser(description='Aggregate exported data')

parser.add_argument('--prefix',
	help="File prefix")

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

args = parser.parse_args()
logging.basicConfig(level=args.loglevel)
store = pd.HDFStore(args.store)


items=['bus','branch','gen','transformer']
for i in glob.glob(args.prefix+"*.raw"):
	name=os.path.splitext(os.path.basename(i))[0]
	print(name)

	dfs={}
	for item in items:
		dfs[item]=store.get('{}_{}'.format(name,item))
		print('{}: {}'.format(item,len(dfs[item])))
