
import pandas as pd

from transform import Transform
from shapely.geometry import Point,LineString

import glob
import os.path
import json

import argparse
import logging

from scipy.stats import truncnorm
import matplotlib.pyplot as plt

lower, upper = 0, 7500
mu, sigma = 150, 150
X = truncnorm(
    (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)

logger = logging.getLogger('em.aggregate')

parser = argparse.ArgumentParser(description='Aggregate exported data')

parser.add_argument('--prefix',
	help="File prefix",
	default="data")

parser.add_argument('--filter',
	help="File prefix",
	action="store_true",
	default=False)

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
parser.add_argument(
	'-t', '--team',
	help="Team for ao system",
	default="ao-ercot-tx-system"
)

parser.add_argument('--store',
	nargs='?', 
	default="store.h5",
	help="Path for local hdf storage")

args = parser.parse_args()
logging.basicConfig(level=args.loglevel)
store = pd.HDFStore(args.store)


items=['bus','branch','gen','transformer']

data={
	"bus":{},
	"branch":{},
	"gen":{},
	"transformer":{}
}


bus_template='templates/substation.yaml'
bus_transform=Transform(bus_template)
bus_outfile='bus-'

bus_group_template='templates/substation-group.yaml'
bus_group_transform=Transform(bus_group_template)
bus_group_outfile='group-bus-'


line_template='templates/transmission.yaml'
line_transform=Transform(line_template)
line_outfile='line-'

line_group_template='templates/transmission-group.yaml'
line_group_transform=Transform(line_group_template)
line_group_outfile='group-line-'


data_bus={}
bus_voltage={}
bus_name={}
bus_geo={}

df_bus_list=[]
df_line_list=[]

team=args.team

def get_bus_key(num):
	return 'mmwg_bus_'+str(num)

def get_branch_key(branch_id):
	return "mmwg_"+branch_id

def get_rn(item_id):
	return "team/{team}/asset/{item_id}".format(team=team,item_id=item_id)

def get_branch_rns(edges):
	return ";".join([ get_rn(get_branch_key(edge)) for edge in edges.split(",") ])

def get_capacity(row):
	return X.rvs(1)[0]

for i in glob.glob(args.prefix+"*.raw"):
	name=os.path.splitext(os.path.basename(i))[0]
	print(name)

	dfs={}
	for item in items:
		dfs[item]=store.get('{}_{}'.format(name,item))
		print('{}: {}'.format(item,len(dfs[item])))

	dbus=dfs['bus']
	dbranch=dfs['branch']

	dbus['bus_key']=dbus['bus'].apply(get_bus_key)
	dbus['rn']=dbus['bus_key'].apply(get_rn)
	dbranch['id']=dbranch.index.map(get_branch_key)
	dbranch['rn']=dbranch['id'].apply(get_rn)
	dbranch['bus0_key']=dbranch['bus0'].apply(get_bus_key)
	dbranch['bus1_key']=dbranch['bus1'].apply(get_bus_key)
	
	if args.filter:
		print('Bus before: ',dbus.shape)
		print('Branch before:',dbranch.shape)
		#filtered_bus=dbus.loc[(dbus['bus']>=30000)&(dbus['bus']<=40000)].copy()
		filtered_bus=dbus.copy()
		print(dbus.edges.head())
		edges=set(filtered_bus['edges'].str.cat(sep=',').split(','))
		dbranch=dbranch.loc[dbranch.index.isin(edges)].copy()
		buses=list(dbus.bus)
		dbranch=dbranch.loc[(dbranch.bus0.isin(buses))&dbranch.bus1.isin(buses)]
		print('Bus Middle:',filtered_bus.shape)

		#all_bus=set(dbranch['bus0_key']).union(set(dbranch['bus1_key']))
		#dbus=dbus.loc[dbus['bus_key'].isin(all_bus)].copy()
		print('Bus after: ',dbus.shape)
		print('Branch after:',dbranch.shape)

	dbus['branch_rns']=dbus.edges.apply(get_branch_rns)
	dbus['available_capacity']=dbus['bus'].apply(get_capacity)
	dbus.loc[dbus['v_nom']<100,'available_capacity']/=100
	dbus.loc[dbus['v_nom']<200,'available_capacity']/=10
	dbus.loc[dbus['v_nom']>200,'available_capacity']*=1.5
	dbus.loc[dbus['v_nom']>300,'available_capacity']*=2
	dbus.loc[dbus['v_nom']>400,'available_capacity']*=1.5
#	dbus.plot()
#	dbus['available_capacity'].hist()
	#plt.show()

	print('DBUS',dbus.head(),dbus.columns)

	## Buses
	if 'lat' in dbus and 'long' in dbus:
		dbus['bus_name']=dbus['ev_name']+' '+dbus['voltage'].astype(str)+'kV'
		dbus.loc[dbus['bus_name'].isnull(),'bus_name']=dbus['psse_name'].str.replace("'",'').str.replace(" ",'') + ' '+dbus['voltage'].astype(str)+'kV'
		print(dbus['bus_name'])
		dbus['geometry'] = list(zip(dbus.long, dbus.lat))
		dbus['geometry'] = dbus['geometry'].apply(Point)
		

		dbus['psse_name']=dbus['psse_name'].str.replace("'",'')
		dbus['zone_name']=dbus['zone_name'].str.replace("'",'')
		dbus['area_name']=dbus['area_name'].str.replace("'",'')
		dbus['owner_name']=dbus['owner_name'].str.replace("'",'')

		#print('bus',dbus)
		print('columns',dbus.columns)
		bus_group_transform.to_file(dbus.itertuples(),bus_group_outfile+name.lower()+'.json')
		
		total_load=dbus['p_load'].sum()
		total_gen=dbus['p_gen'].sum()
		dbus['ldf']=dbus['p_load']/total_load
		df_bus_list.append(dbus)
		for itemrow in dbus.iterrows():
			item=itemrow[1]

			bus_key=item['bus_key']
			bus_voltage[bus_key]=item['voltage']
			bus_name[bus_key]=item['bus_name']
			bus_geo[bus_key]=item['geometry']
			if bus_key not in data_bus:
				data_bus[bus_key]={}
			if name not in data_bus[bus_key]:
				data_bus[bus_key]={}	
				data_bus[bus_key][name]={}
			for df in ['p_load','p_gen','ldf']:
				data_bus[bus_key][name][df]=item[df]
		


		# Transmission
		print(dbranch)
		dbranch['bus0_name']=dbranch['bus0_key'].apply(lambda x: bus_name.get(x,'Unknown'))
		dbranch['bus1_name']=dbranch['bus1_key'].apply(lambda x: bus_name.get(x,'Unknown'))
		dbranch['voltage']=dbranch['bus0_key'].apply(lambda x: bus_voltage.get(x,130))
		dbranch['branch_key']=dbranch['id']
		dbranch['geometry']=dbranch.apply(lambda x: LineString([bus_geo[x['bus0_key']],bus_geo[x['bus1_key']]]),axis=1)


		line_group_transform.to_file(dbranch.itertuples(),line_group_outfile+name.lower()+'.json')

		df_line_list.append(dbranch)

		print(dbranch)
		print(dbranch.columns)
		break


# # Buses
df_bus=pd.concat(df_bus_list)
df_bus.drop_duplicates(subset='bus_key',inplace=True)

bus_transform.to_file(df_bus.itertuples(),bus_outfile+name.lower()+'.json')

with open('bus-data-'+name.lower()+'.json','w') as out_file:
	json.dump(data_bus,out_file)

# Transmission
df_line=pd.concat(df_line_list)
df_line.drop_duplicates(subset='branch_key',inplace=True)

line_transform.to_file(df_line.itertuples(),line_outfile+name.lower()+'.json')