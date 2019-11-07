
import logging
logger = logging.getLogger('em.format_components')

import pandas as pd

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
	df = df.rename(index=str,columns={'I':'bus0','J':'bus1','X':'x','R':'r','B':'b','RATEA':'s_nom_A','RATEB':'s_nom_B','RATEC':'s_nom_C','CKT':'circuit','LEN':'length'})
	return df[['bus0','bus1','x','r','b','s_nom_A','s_nom_B','s_nom_C','length','circuit']]

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

def format_twodc(df):
	logger.debug('Formatting twodc {}'.format(len(df)))
	df.index = 'dc'+df['IPR'].astype(str)+'_'+df['IPI'].astype(str)+'_'+df['I'].str.replace(' ','').str.replace("'",'')
	df = df.rename(index=str,columns={'IPR':'bus0','IPI':'bus1'})
	df['p_nom']=1500
	df['p_min_pu']=-1
	return df[['bus0','bus1','p_nom','p_min_pu']]

def format_transformer(df,s_system=100):
	logger.debug('Formatting transformers {}'.format(len(df)))
	def get_x_field(field,s_nom_field='s_nom'):
		def get_x(item):
			cz = item['CZ']
			s_unit = item[s_nom_field]
			x = item[field]
			if cz == 1:
				# In system base already
				pass
			elif cz  == 2:
				# in unit base, convert to system
				x = x*s_unit/s_system
			else:
				pass
			return x
		return get_x

	def get_r_field(field,s_nom_field='s_nom'):
		def get_r(item):
			cz = item['CZ']
			s_unit = item[s_nom_field]
			r = item[field]
			if cz == 1:
				# In system base already
				pass
			elif cz  == 2:
				# in unit base, convert to system
				r = r*s_system/s_unit
			else:
				# watts to MVA, unit power factor
				if s_unit>0:
					r = r/s_unit/1000000
				else:
					logger.warning('Nominal Power of transformer is 0')
					#print(item)
					r = r/1000000
			return r
		return get_r

	t2=df[df['K']==0].copy()
	t3=df[df['K']!=0].copy()

	## Two winding transformers
	t2['name'] = ('two_wind_'+t2['I'].astype(str) + '_' +t2['J'].astype(str) + '_' + t2['CKT']).str.replace(' ','').str.replace("'",'')
	t2 = t2.rename(index=str,columns={'I':'bus0','J':'bus1','X1-2':'x','R1-2':'r','RATA1':'s_nom_A','RATB1':'s_nom_B','RATC1':'s_nom_C','ANG1':'phase_shift'})
	t2['s_nom']=t2['s_nom_A']
	t2['v0']=t2['NOMV1']
	t2['v1']=t2['NOMV2']
	t2['wind0']=t2['WINDV1']
	t2['wind1']=t2['WINDV2']
	t2['r'] = t2.apply(get_r_field('r'),axis=1)
	t2['x'] = t2.apply(get_x_field('x'),axis=1)
	trans_cols=['bus0','bus1','r','x','name','s_nom','s_nom_A','s_nom_B','s_nom_C','phase_shift','v0','v1']
	t2=t2[trans_cols]
	logger.debug('Created {} 2 winding transformers'.format(len(t2)))

	## Three winding transformers
	if len(t3)>0:
		t3['x12']=t3.apply(get_x_field('X1-2','SBASE1-2'),axis=1)
		t3['x23']=t3.apply(get_x_field('X2-3','SBASE2-3'),axis=1)
		t3['x31']=t3.apply(get_x_field('X3-1','SBASE3-1'),axis=1)
		t3['r12']=t3.apply(get_r_field('R1-2','SBASE1-2'),axis=1)
		t3['r23']=t3.apply(get_r_field('R2-3','SBASE2-3'),axis=1)
		t3['r31']=t3.apply(get_r_field('R3-1','SBASE3-1'),axis=1)
		
		t3['a']=t3['r12']+t3['r23']+t3['r31']
		t3['b']=t3['x12']+t3['x23']+t3['x31']
		
		t3['alpha1']=t3['r12']*t3['r31']-t3['x12']*t3['x31']
		t3['beta1']=t3['r31']*t3['x12']+t3['r12']*t3['x31']

		t3['alpha2']=t3['r12']*t3['r23']-t3['x12']*t3['x23']
		t3['beta2']=t3['r23']*t3['x12']+t3['r12']*t3['x23']
		
		t3['alpha3']=t3['r23']*t3['r31']-t3['x23']*t3['x31']
		t3['beta3']=t3['r31']*t3['x23']+t3['r23']*t3['x31']

		t3['denom']=t3['a']*t3['a']+t3['b']*t3['b']

		t3['r1']=(t3['a']*t3['alpha1']+t3['b']*t3['beta1'])/t3['denom']
		t3['x1']=(t3['a']*t3['beta1']-t3['b']*t3['alpha1'])/t3['denom']

		t3['r2']=(t3['a']*t3['alpha2']+t3['b']*t3['beta2'])/t3['denom']
		t3['x2']=(t3['a']*t3['beta2']-t3['b']*t3['alpha2'])/t3['denom']

		t3['r3']=(t3['a']*t3['alpha3']+t3['b']*t3['beta3'])/t3['denom']
		t3['x3']=(t3['a']*t3['beta3']-t3['b']*t3['alpha3'])/t3['denom']
		t3[['r12','r23','r31','x12','x23','x31','a','b','alpha1','beta1','alpha2','beta2','alpha3','beta3','r1','r2','r3','x1','x2','x3']].to_csv('t3ex.csv')
		

		t3['trans_id']=t3['I'].astype(str)+'_'+t3['J'].astype(str)+'_'+t3['K'].astype(str)+'_'+t3['CKT'].astype(str).str.replace("'",'').str.replace(" ","")
		t3['aux_bus']='aux'+t3['trans_id']
		t3['aux_bus_v_nom']=t3['NOMV1']
		t3['v_nom_1']=t3['NOMV1']
		t3['v_nom_2']=t3['NOMV2']
		t3['v_nom_3']=t3['NOMV3']

		t3_1 = t3.copy().rename(index=str,columns={'I':'bus0','x1':'x','r1':'r','RATA1':'s_nom_A','RATB1':'s_nom_B','RATC1':'s_nom_C','ANG1':'phase_shift'})
		t3_1['bus1']=t3_1['aux_bus']
		t3_1['s_nom']=t3_1['s_nom_A']
		t3_1['v0']=t3_1['v_nom_1']
		t3_1['v1']=t3_1['aux_bus_v_nom']
		t3_1['name'] = 'three_wind_I_'+t3_1['trans_id']
		t3_1=t3_1[trans_cols]
		
		t3_2 = t3.copy().rename(index=str,columns={'J':'bus1','x1':'x','r1':'r','RATA2':'s_nom_A','RATB2':'s_nom_B','RATC2':'s_nom_C','ANG2':'phase_shift'})
		t3_2['bus0']=t3_2['aux_bus']
		t3_2['s_nom']=t3_2['s_nom_A']
		t3_2['v0']=t3_2['aux_bus_v_nom']
		t3_2['v1']=t3_2['v_nom_2']
		t3_2['name'] = 'three_wind_J_'+t3_2['trans_id']
		t3_2=t3_2[trans_cols]
		
		t3_3 = t3.copy().rename(index=str,columns={'K':'bus1','x1':'x','r1':'r','RATA3':'s_nom_A','RATB3':'s_nom_B','RATC3':'s_nom_C','ANG3':'phase_shift'})
		t3_3['bus0']=t3_3['aux_bus']
		t3_3['s_nom']=t3_3['s_nom_A']
		t3_3['v0']=t3_3['aux_bus_v_nom']
		t3_3['v1']=t3_3['v_nom_3']
		t3_3['name'] = 'three_wind_K_'+t3_3['trans_id']
		t3_3=t3_3[trans_cols]
		

		logger.debug('Created {} transformers from {} 3 winding transformers'.format(len(t3)*3,len(t3)))

		nt = pd.concat([t2,t3_1,t3_2,t3_3],axis=0,sort=False)
	else:
		nt=t2


	print(nt)
	print(nt.columns)
	#sys.exit()
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
	'transformer':format_transformer,
	'twodc':format_twodc
}

def format_all(raw_data):
	out={}
	for i in raw_data:
		if 'df' in raw_data[i] and i in format_dict:
			out[i]=format_dict[i](raw_data[i]['df'])
	return out