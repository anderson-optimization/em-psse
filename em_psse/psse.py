
import yaml
from io import StringIO
import pandas as pd

import logging
logger = logging.getLogger('em.psse')

import os
dirname = os.path.dirname(__file__)
with open('{}/psse-modes.yaml'.format(dirname),'r') as in_file:
	modes = yaml.load(in_file)


	
def get_signals(line_num,line,current_mode):
	#print(line_num,line)
	signals = []
	for m in modes:
		for s in m['signal']:
			if 'text' in s:
				if s['text'] in line:
					signals.append((s,m))
			if 'line' in s:
				if s['line'] == line_num:
					signals.append((s,m))
	return signals


def read_transformer(lines,records):
	iter_lines = iter(lines)
	#records=[]
	headers = [r['header'] for r in records]
	line_holder={
		2: [
			[headers[0]],
			[headers[1]],
			[headers[2]],
			[headers[3]]
		],
		3: [
			[headers[0]],
			[headers[1]],
			[headers[2]],
			[headers[3]],
			[headers[4]]
		]
	}
	for line in iter_lines:
		rows=[line]
		rows.append(next(iter_lines))
		rows.append(next(iter_lines))
		rows.append(next(iter_lines))
		windings = None
		try:
			flag=int(line.split(',')[2])
			if flag != 0:
				raise ValueError('Not a 2 phase winding')
			windings = 2
		except Exception as e:
			windings = 3
			rows.append(next(iter_lines))
		
		for r in range(len(rows)):
			line_holder[windings][r].append(rows[r])
	
	dfs={
		2:[],
		3:[]
	}
	for winding in line_holder:
		rc=0
		for record in line_holder[winding]:
			rc+=1
			text = StringIO(''.join(record))
			dfs[winding].append(pd.read_table(text,sep=','))
			logger.debug("{} {} {}".format(winding,rc,len(record)))
			logger.debug("{}".format(record[0]))
	return dfs

def read_twodc(lines,records):
	iter_lines = iter(lines)
	#records=[]
	headers = [r['header'] for r in records]
	line_holder=[
		[headers[0]],
		[headers[1]],
		[headers[2]]
	]
	for line in iter_lines:
		rows=[line]
		rows.append(next(iter_lines))
		rows.append(next(iter_lines))
		
		for r in range(len(rows)):
			line_holder[r].append(rows[r])
	
	dfs=[]
	rc=0
	for record in line_holder:
		rc+=1
		text = StringIO(''.join(record))
		dfs.append(pd.read_table(text,sep=','))
		logger.debug("{} {}".format(rc,len(record)))
		logger.debug("{}".format(record[0]))

	return dfs


def parse_raw(in_file_name):
	"""
	This function will parse a RAW file and return a PyPSA model
	"""

	# Initialize output
	output ={}
	for item in modes:
		key=item['key']
		output[key]={
			"name":item['name'],
			"key":key,
			"lines":[]
		}
		# Set up column structure
		if 'columns' in item:
			output[key]['columns']=item['columns']
			header = ",".join([c['name'] for c in item['columns']]).replace(' ','')+'\n'
			output[key]['header']=header
			output[key]['lines'].append(header)
		if 'records' in item:
			output[key]['records'] = item['records']
			for record in output[key]['records']:
				header = ",".join([c['name'] for c in record['columns']]).replace(' ','')+'\n'
				record['header']=header
		# Get parsing info
		output[key]['parse']=item.get('parse',{})

	# Initialize header mode
	current_mode = {
		'key': 'header'
	}

	# Read file and store in container
	with open(in_file_name,'r') as in_file:
		line = in_file.readline()
		line_num = 0
		while line:
			line_num+=1
			
			START = None
			STOP = None
			
			# Process signals
			signals = get_signals(line_num,line,current_mode)
			for signal,mode in signals:
				logger.debug("Signal: {} {} {}".format(line_num,signal['command'],mode['key']))
				if signal['command'] == 'start':
					START = mode
				if signal['command'] == 'stop':
					STOP = mode

			if current_mode and START and not STOP:
				raise ValueError('Current mode was never stopped')
			

			# Store lines
			if current_mode and (not STOP or 'keep_tail' in STOP):
				key = current_mode['key']
				output[key]['lines'].append(line)
				#print key
				
			if STOP and current_mode and current_mode['key'] != STOP['key']:
				raise ValueError('Attempting to stop a different mode',current_mode['key'],STOP['key'])
			elif START:
				current_mode = START
			elif STOP:
				current_mode = None
			
			line = in_file.readline()
			

	logger.debug("Captured Lines")
	for i in output:
		logger.debug('Item: {}, length: {}'.format(i,len(output[i]['lines'])))

	for i in output:
		if 'lines' not in output[i]:
			logger.debug('no lines {}'.format(i))
			continue
		lines=output[i]['lines']
		if len(lines)==1:
			logger.debug('only header {}'.format(i))
			continue
		
		if 'read_table' in output[i]['parse']:
			text = StringIO(''.join(lines))
			output[i]['df'] = pd.read_table(text,sep=',')
		
		if 'read_transformer' in output[i]['parse']:
			output[i]['dfs']=read_transformer(lines,output[i]['records'])
			df2=pd.concat(output[i]['dfs'][2],axis=1, sort=False)
			df3=pd.concat(output[i]['dfs'][3],axis=1, sort=False)
			output[i]['df']=df3.append(df2,sort=False)

		if 'read_twodc' in output[i]['parse']:
			output[i]['dfs']=read_twodc(lines,output[i]['records'])
			output[i]['df']=pd.concat(output[i]['dfs'],axis=1, sort=False)


		
		logger.debug('{} {} {}'.format(i, len(lines), 'df' in output[i]))
		if 'df' in output[i]:
			logger.info('Parsed {} {}'.format(len(output[i]['df']),i))
			if len(lines)>0:
				logger.debug("{}".format(lines[0]))

	return output



def get_volt(cw,nom=None,wind=None):
	if nom == None:
		raise ValueException('No nominal voltage value')
	if wind == None:
		raise ValueException('No winding value')
	if cw == 1 or cw == 3:
		return wind * nom
	elif cw == 2:
		return wind
	else:
		raise Exception('Unknown')

def format_load(df):
	logger.debug('Formatting load')
	df.index = 'load'+df['I'].astype(str) + '_' + df['ID'].str.replace(' ','').str.replace("'",'')
	df = df.rename(index=str,columns={'I':'bus','PL':'p_set','QL':'q_set'})
	return df[['bus','p_set','q_set']]

def format_bus(df):
	logger.debug('Formatting bus')		
	df = df.rename(index=str,columns={'I':'bus','BASKV':'v_nom','NAME':'psse_name','IDE':'bus_type','ZONE':'zone','OWNER':'owner','AREA':'area'})
	df.index = df['bus']
	return df[['bus','v_nom','psse_name','bus_type','zone','owner','area']]

def format_branch(df):
	logger.debug('Formatting branch')		
	df.index = 'branch'+df['I'].astype(str) + '_'+df['J'].astype(str) + '_' + df['CKT'].str.replace(' ','').str.replace("'",'')
	df = df.rename(index=str,columns={'I':'bus0','J':'bus1','X':'x','R':'r','B':'b','RATEA':'s_nom_A','RATEB':'s_nom_B','RATEC':'s_nom_C'})
	return df[['bus0','bus1','x','r','b','s_nom_A','s_nom_B','s_nom_C']]

def format_gen(df):
	logger.debug('Formatting gen')
	df.index = 'gen'+df['I'].astype(str) + '_' +df['ID'].str.replace(' ','').str.replace("'",'')
	df = df.rename(index=str,columns={'I':'bus','PT':'p_nom','PG':'p_gen','QG':'q_gen','QT':'q_nom'})
	return df[['bus','p_nom','p_gen','q_gen','q_nom']]

def format_area(df):
	logger.debug('Formatting area')
	df.index = 'area'+df['I'].astype(str)
	df = df.rename(index=str,columns={'I':'area','ARNAME':'area_name','ISW':'slack_bus','PDES':'desired_net_export','PTOL':'interchange_tolerance_bandwidth'})
	return df[['area','area_name','slack_bus','desired_net_export','interchange_tolerance_bandwidth']]

def format_zone(df):
	logger.debug('Formatting zone')
	df.index = 'zone'+df['I'].astype(str)
	df = df.rename(index=str,columns={'I':'zone','ZONAME':'zone_name'})
	return df[['zone','zone_name']]

def format_owner(df):
	logger.debug('Formatting owner')
	df.index = 'owner'+df['I'].astype(str)
	df = df.rename(index=str,columns={'I':'owner','OWNAME':'owner_name'})
	return df[['owner','owner_name']]

def format_transformer(df_tf,s_system=100):
	logger.debug('Formatting transformers')
	def get_x(item):
		cz = item['CZ']
		s_unit = item['s_nom']
		x = item['x']
		if cz == 1:
			# In system base, convert to unit base
			x = x*s_unit/s_system
		elif cz  == 2:
			# in unit base
			pass
		else:
			pass
		return x

	def get_r(item):
		cz = item['CZ']
		s_unit = item['s_nom']
		r = item['r']
		if cz == 1:
			# In system base, convert to unit base
			r = r*s_unit/s_system
		elif cz  == 2:
			# in unit base
			pass
		else:
			# watts to MVA, unit power factor
			r = r/s_unit/1000000
		return r

	t2=df_tf[df_tf['K']==0].copy()
	t3=df_tf[df_tf['K']!=0].copy()

	## Two winding transformers
	t2['name'] = ('tt'+t2['I'].astype(str) + '_' +t2['J'].astype(str) + '_' + t2['CKT']).str.replace(' ','').str.replace("'",'')
	t2 = t2.rename(index=str,columns={'I':'bus0','J':'bus1','X1-2':'x','R1-2':'r','RATA1':'s_nom'})
	t2['s_nom_A']=t2['s_nom']
	t2['s_nom_B']=t2['RATB1']
	t2['s_nom_C']=t2['RATC1']
	t2['v0']=t2['NOMV1']
	t2['v1']=t2['NOMV2']
	t2['wind0']=t2['WINDV1']
	t2['wind1']=t2['WINDV2']
	t2['r'] = t2.apply(get_r,axis=1)
	t2['x'] = t2.apply(get_x,axis=1)
	t2=t2[['bus0','bus1','r','x','name','s_nom_A','s_nom_B','s_nom_C','v0','v1','wind0','wind1']]
	logger.debug('Created {} 2 winding transformers'.format(len(t2)))


	## Three winding transformers
	#
	# ISSUE
	# This network topology is based off of pandapower 3 winding transformer, although it seems like definition of parameters don't line up
	# 
	
	if len(t3)>0:
		t3['aux_bus']=('taux_'+t3['I'].astype(str) + '_' +t3['J'].astype(str) + '_' + t3['K'].astype(str) + '_' + t3['CKT']).str.replace(' ','').str.replace("'",'')

		t3_1 = t3.copy().rename(index=str,columns={'I':'bus0','aux_bus':'bus1','X1-2':'x','R1-2':'r','SBASE1-2':'s_nom'})
		t3_1['name'] = ('tta'+t3_1['bus0'].astype(str) + '_' +t3_1['bus1'].astype(str) + '_' + t3_1['CKT'] + '_' + t3_1['NAME']).str.replace(' ','').str.replace("'",'')
		t3_1['r'] = t3_1.apply(get_r,axis=1)
		t3_1['x'] = t3_1.apply(get_x,axis=1)
		t3_1=t3_1[['bus0','bus1','r','x','name','s_nom']]

		t3_2 = t3.copy().rename(index=str,columns={'aux_bus':'bus0','J':'bus1','X2-3':'x','R2-3':'r','SBASE2-3':'s_nom'})
		t3_2['name'] = ('ttb'+t3_2['bus0'].astype(str) + '_' +t3_2['bus1'].astype(str) + '_' + t3_2['CKT'] + '_' + t3_2['NAME']).str.replace(' ','').str.replace("'",'')
		t3_2['r'] = t3_2.apply(get_r,axis=1)
		t3_2['x'] = t3_2.apply(get_x,axis=1)
		t3_2=t3_2[['bus0','bus1','r','x','name','s_nom']]

		t3_3 = t3.copy().rename(index=str,columns={'aux_bus':'bus0','K':'bus1','X3-1':'x','R3-1':'r','SBASE3-1':'s_nom'})
		t3_3['name'] = ('ttc'+t3_3['bus0'].astype(str) + '_' +t3_3['bus1'].astype(str) + '_' + t3_3['CKT'] + '_' + t3_3['NAME']).str.replace(' ','').str.replace("'",'')	
		t3_3['r'] = t3_3.apply(get_r,axis=1)
		t3_3['x'] = t3_3.apply(get_x,axis=1)
		t3_3=t3_3[['bus0','bus1','r','x','name','s_nom']]

		logger.debug('Created {} transformers from {} 3 winding transformers'.format(len(t3)*3,len(t3)))

		nt = pd.concat([t2,t3_1,t3_2,t3_3],axis=0,sort=False)
	else:
		nt=t2

	return nt


format_dict={
	'load':format_load,
	'bus':format_bus,
	'branch':format_branch,
	'gen':format_gen,
	'area':format_area,
	'zone':format_zone,
	'owner':format_owner,
	'transformer':format_transformer
}

def format_all(raw_data):
	out={}
	for i in raw_data:
		if 'df' in raw_data[i] and i in format_dict:
			out[i]=format_dict[i](raw_data[i]['df'])
	return out