
import logging
logger = logging.getLogger('em.format_components')


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
	logger.debug('Formatting load {}'.format(len(df)))
	df.index = 'load'+df['I'].astype(str) + '_' + df['ID'].str.replace(' ','').str.replace("'",'')
	df = df.rename(index=str,columns={'I':'bus','PL':'p_set','QL':'q_set'})
	return df[['bus','p_set','q_set']]

def format_bus(df):
	logger.debug('Formatting bus {}'.format(len(df)))		
	df = df.rename(index=str,columns={'I':'bus','BASKV':'v_nom','NAME':'psse_name','IDE':'bus_type','ZONE':'zone','OWNER':'owner','AREA':'area'})
	df.index = df['bus']
	return df[['bus','v_nom','psse_name','bus_type','zone','owner','area']]

def format_branch(df):
	logger.debug('Formatting branch {}'.format(len(df)))		
	df.index = 'branch'+df['I'].astype(str) + '_'+df['J'].astype(str) + '_' + df['CKT'].str.replace(' ','').str.replace("'",'')
	df = df.rename(index=str,columns={'I':'bus0','J':'bus1','X':'x','R':'r','B':'b','RATEA':'s_nom_A','RATEB':'s_nom_B','RATEC':'s_nom_C'})
	return df[['bus0','bus1','x','r','b','s_nom_A','s_nom_B','s_nom_C']]

def format_gen(df):
	logger.debug('Formatting gen {}'.format(len(df)))
	df.index = 'gen'+df['I'].astype(str) + '_' +df['ID'].str.replace(' ','').str.replace("'",'')
	df = df.rename(index=str,columns={'I':'bus','PT':'p_nom','PG':'p_gen','QG':'q_gen','QT':'q_nom'})
	return df[['bus','p_nom','p_gen','q_gen','q_nom']]

def format_area(df):
	logger.debug('Formatting area {}'.format(len(df)))
	df.index = 'area'+df['I'].astype(str)
	df = df.rename(index=str,columns={'I':'area','ARNAME':'area_name','ISW':'slack_bus','PDES':'desired_net_export','PTOL':'interchange_tolerance_bandwidth'})
	return df[['area','area_name','slack_bus','desired_net_export','interchange_tolerance_bandwidth']]

def format_zone(df):
	logger.debug('Formatting zone {}'.format(len(df)))
	df.index = 'zone'+df['I'].astype(str)
	df = df.rename(index=str,columns={'I':'zone','ZONAME':'zone_name'})
	return df[['zone','zone_name']]

def format_owner(df):
	logger.debug('Formatting owner {}'.format(len(df)))
	df.index = 'owner'+df['I'].astype(str)
	df = df.rename(index=str,columns={'I':'owner','OWNAME':'owner_name'})
	return df[['owner','owner_name']]

def format_transformer(df,s_system=100):
	logger.debug('Formatting transformers {}'.format(len(df)))
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

	t2=df[df['K']==0].copy()
	t3=df[df['K']!=0].copy()

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

	nt.index=nt['name']
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