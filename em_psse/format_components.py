import sys
import logging
logger = logging.getLogger('em.format_components')

import pandas as pd

def format_load(df):
	logger.debug('Formatting load {}'.format(len(df)))
	df.index = 'load'+df['I'].astype(str) + '_' + df['ID'].str.replace(' ','').str.replace("'",'')
	df = df.rename(index=str,columns={'I':'bus','PL':'p_set','QL':'q_set','STATUS':'status'})
	return df[['bus','p_set','q_set','status']]

def format_bus(df):
	logger.debug('Formatting bus {}'.format(len(df)))		
	df = df.rename(index=str,columns={'I':'bus','BASKV':'v_nom','NAME':'psse_name','IDE':'bus_type','ZONE':'zone','OWNER':'owner','AREA':'area'})
	df.index = df['bus']
	return df[['bus','v_nom','psse_name','bus_type','zone','owner','area']]

def format_branch(df):
	logger.debug('Formatting branch {}'.format(len(df)))		
	df.index = 'branch'+df['I'].astype(str) + '_'+df['J'].astype(str) + '_' + df['CKT'].str.replace(' ','').str.replace("'",'')
	df = df.rename(index=str,columns={'I':'bus0','J':'bus1','X':'x','R':'r','B':'b','RATEA':'s_nom_A','RATEB':'s_nom_B','RATEC':'s_nom_C','CKT':'circuit','LEN':'length','ST':'status'})
	return df[['bus0','bus1','x','r','b','s_nom_A','s_nom_B','s_nom_C','length','circuit','status']]

def format_gen(df):
	logger.debug('Formatting gen {}'.format(len(df)))
	df.index = 'gen'+df['I'].astype(str) + '_' +df['ID'].str.replace(' ','').str.replace("'",'')
	df = df.rename(index=str,columns={'I':'bus','PT':'p_nom','PG':'p_gen','PB':'p_min','QG':'q_gen','QT':'q_nom','QB':'q_min','STAT':'status'})
	return df[['bus','p_nom','p_gen','p_min','q_gen','q_nom','q_min','status']]

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

def format_switchedshunt(df):
	logger.debug('Formatting switchedshunt {}'.format(len(df)))
	df.index = 'sshunt'+df['I'].astype(str) # this appears to be unique, if not, we have to add some ID that is not in PSSE Raw file
	# use binit as b, this removes switched behavior, which is not ideal
	# however, incorporating switching into pypsa seems nontrivial

	# it actually seems like B defined in RAW is in MVar and b in pypsa is Siemens, need to figure out different implementation
	df = df.rename(index=str,columns={'I':'bus','BINIT':'b'})
	return df[['bus','b']]

def format_fixedshunt(df):
	logger.debug('Formatting fixedshunt {}'.format(len(df)))
	df.index = 'fshunt'+df['I'].astype(str) # this appears to be unique, if not, we have to add some ID that is not in PSSE Raw file

	# it actually seems like B defined in RAW is in MVar and b in pypsa is Siemens, need to figure out different implementation
	df = df.rename(index=str,columns={'I':'bus','B':'b','STATUS':'status'})
	return df[['bus','b','status']]


def format_transformer(df,s_system=100):
	logger.debug('Formatting transformers {}'.format(len(df)))

	## PSSE Raw file
	## 
	## Lines have x and r defined in pu
	## 		Zero impedence lines are special
	## 		- We should throw a error/warning on them
	## Transformers
	# 	The impedance data I/O code that defines the units in which the winding imped-
	# 	ances R1-2, X1-2, R2-3, X2-3, R3-1 and X3-1 are specified: 
	# 	1 for resistance and reactance in pu on system base quantities
	# 	2 for resistance and reactance in pu on a specified base MVA and winding bus base voltage
	# 	3 for transformer load loss in watts and impedance magnitude
	# 		 in pu on a specified base MVA and 
	# 		 winding bus base voltage. CZ = 1 by default.

	# Phase angle shift
	# 	The winding one phase shift angle in degrees. ANG1 is positive for a positive
	# 		phase shift from the winding one side to the winding two side (for a two-winding
	# 		transformer), or from the winding one side to the 'T' (or star) point bus (for a three-
	# 		winding transformer). ANG1 must be greater than -180.0 and less than or equal to
	# 		+1 80.0. ANG1 = 0.0 by default.

	## Pypsa 
	## Line component expects x in non pu quantities 
	## -- This format code does not have access to voltage as its a bus quantity
	## -- Should put in as x_pu so don't naively mix up as x in non pu
	## -- code for conversion in pypsa
	#		> network.lines["v_nom"] = network.lines.bus0.map(network.buses.v_nom)
	#    	> network.lines["x_pu"] = network.lines.x/(network.lines.v_nom**2)
    #		> network.lines["r_pu"] = network.lines.r/(network.lines.v_nom**2)
	#
	## Transformer expects x in pu with base as s_nom (s_unit)
	## -- code for conversion in pypsa
	#		> #convert transformer impedances from base power s_nom to base = 1 MVA
    #		> network.transformers["x_pu"] = network.transformers.x/network.transformers.s_nom
    #		> network.transformers["x_pu_eff"] = network.transformers["x_pu"]* network.transformers["tap_ratio"]
    #	where tap_ratio="Ratio of per unit voltages at each bus for tap changed."
    #	  and tap_side="Defines if tap changer is modelled at the primary 0 side 
    #	  				(usually high-voltage) or the secondary 1 side (usually low voltage) 
    #	  				(must be 0 or 1, defaults to 0). Ignored if type defined."


	def get_x_field(field,s_nom_field='s_nom'):
		def get_x(item):
			# if 'I' in item and item.I == 5966 and item.J == 79690:
			# 	print('row')
			# 	for c in item.index:
			# 		print(c,item[c])
			cz = item['CZ']
			s_unit = item[s_nom_field]
			x = item[field]
			if cz == 1:
				# In system base, convert to 1 MVA base
				x = x/s_system
			elif cz  == 2:
				# in unit base, convert to 1 MVA base
				x = x/s_unit
			else:
				# Load loss in watts, impedence in unit base
				x = x/s_unit
			if x == 0:
				logger.error('Impedence X is 0')
			elif x < 0:
				logger.error('Impedence X is < 0')
			elif x > 10:
				logger.error('Impedence is pretty high, X > 10')
			return x
		return get_x

	def get_r_field(field,s_nom_field='s_nom'):
		def get_r(item):
			cz = item['CZ']
			s_unit = item[s_nom_field]
			r = item[field]
			if cz == 1:
				# In system base, convert to unit
				r = r/s_system
			elif cz  == 2:
				# in unit base
				r = r/s_unit
			else:
				# watts to MVA w/ 1 MVA base, unit power factor
				r = r/1000000
			return r
		return get_r


	def get_winding(nom_field,wind_field):
		def _get_winding(item):
			nom = item[nom_field]
			wind = item[wind_field]
			cw = item['CW']
			if nom == None:
				raise ValueException('No nominal voltage value')
			if wind == None:
				raise ValueException('No winding value')
			if cw == 1 or cw == 3:
				return wind 
			elif cw == 2:
				return wind / nom
			else:
				raise Exception('Unknown')
		return _get_winding


	t2=df[df['K']==0].copy()
	t3=df[df['K']!=0].copy()

	## Two winding transformers
	t2['name'] = ('two_wind_'+t2['I'].astype(str) + '_' +t2['J'].astype(str) + '_' + t2['CKT']).str.replace(' ','').str.replace("'",'')
	t2 = t2.rename(index=str,columns={'I':'bus0','J':'bus1','X1-2':'x','R1-2':'r','RATA1':'s_nom_A','RATB1':'s_nom_B','RATC1':'s_nom_C','ANG1':'phase_shift','STAT':'status'})
	t2['s_nom']=t2['s_nom_A']
	t2['v0']=t2['NOMV1']
	t2['v1']=t2['NOMV2']
	t2['wind0']=t2.apply(get_winding('v0','WINDV1'),axis=1)
	t2['wind1']=t2.apply(get_winding('v1','WINDV2'),axis=1)
	t2['r'] = t2.apply(get_r_field('r','SBASE1-2'),axis=1)
	t2['x'] = t2.apply(get_x_field('x','SBASE1-2'),axis=1)
	trans_cols=['bus0','bus1','r','x','name','s_nom','s_nom_A','s_nom_B','s_nom_C','phase_shift','v0','v1','wind0','wind1','status']
	t2=t2[trans_cols]
	logger.debug('Created {} 2 winding transformers'.format(len(t2)))

	## Three winding transformers, perform delta to wye conversion
	if len(t3)>0:
		t3['x12']=t3.apply(get_x_field('X1-2','SBASE1-2'),axis=1)
		t3['x23']=t3.apply(get_x_field('X2-3','SBASE2-3'),axis=1)
		t3['x31']=t3.apply(get_x_field('X3-1','SBASE3-1'),axis=1)
		t3['r12']=t3.apply(get_r_field('R1-2','SBASE1-2'),axis=1)
		t3['r23']=t3.apply(get_r_field('R2-3','SBASE2-3'),axis=1)
		t3['r31']=t3.apply(get_r_field('R3-1','SBASE3-1'),axis=1)

		# These are power world calculations to convert impedence.  We actually want in unit base though.  Convert in following section.
		t3['r1']=s_system/2 * (t3['r12']/t3['SBASE1-2'] - t3['r23']/t3['SBASE2-3'] + t3['r31']/t3['SBASE3-1'])
		t3['x1']=s_system/2 * (t3['x12']/t3['SBASE1-2'] - t3['x23']/t3['SBASE2-3'] + t3['x31']/t3['SBASE3-1'])

		t3['r2']=s_system/2 * (t3['r12']/t3['SBASE1-2'] + t3['r23']/t3['SBASE2-3'] - t3['r31']/t3['SBASE3-1'])
		t3['x2']=s_system/2 * (t3['x12']/t3['SBASE1-2'] + t3['x23']/t3['SBASE2-3'] - t3['x31']/t3['SBASE3-1'])

		t3['r3']=s_system/2 * (-t3['r12']/t3['SBASE1-2'] + t3['r23']/t3['SBASE2-3'] + t3['r31']/t3['SBASE3-1'])
		t3['x3']=s_system/2 * (-t3['x12']/t3['SBASE1-2'] + t3['x23']/t3['SBASE2-3'] + t3['x31']/t3['SBASE3-1'])

		# out = t3.iloc[266].to_dict()

		# for k in out:
		# 	print(k,out[k])

		# sys.exit()

		t3['trans_id']=t3['I'].astype(str)+'_'+t3['J'].astype(str)+'_'+t3['K'].astype(str)+'_'+t3['CKT'].astype(str).str.replace("'",'').str.replace(" ","")
		t3['aux_bus']='aux'+t3['trans_id']
		t3['aux_bus_v_nom']=t3['NOMV1']
		t3['aux_bus_wind']=1
		t3['v_nom_1']=t3['NOMV1']
		t3['v_nom_2']=t3['NOMV2']
		t3['v_nom_3']=t3['NOMV3']
		t3['wind1']=t3.apply(get_winding('v_nom_1','WINDV1'),axis=1)
		t3['wind2']=t3.apply(get_winding('v_nom_2','WINDV2'),axis=1)
		t3['wind3']=t3.apply(get_winding('v_nom_3','WINDV3'),axis=1)

		t3_1 = t3.copy().rename(index=str,columns={'I':'bus0','x1':'x','r1':'r','RATA1':'s_nom_A','RATB1':'s_nom_B','RATC1':'s_nom_C','ANG1':'phase_shift','STAT':'status'})
		t3_1['bus1']=t3_1['aux_bus']
		t3_1['s_nom']=t3_1['s_nom_A']
		t3_1['x']=t3_1['x']/s_system
		t3_1['r']=t3_1['r']/s_system
		t3_1['v0']=t3_1['v_nom_1']
		t3_1['v1']=t3_1['aux_bus_v_nom']
		t3_1['wind0']=t3_1['wind1']
		t3_1['wind1']=t3_1['aux_bus_wind']
		t3_1['name'] = 'three_wind_I_'+t3_1['trans_id']
		t3_1=t3_1[trans_cols]
		
		t3_2 = t3.copy().rename(index=str,columns={'J':'bus1','x2':'x','r2':'r','RATA2':'s_nom_A','RATB2':'s_nom_B','RATC2':'s_nom_C','ANG2':'phase_shift','STAT':'status'})
		t3_2['bus0']=t3_2['aux_bus']
		t3_2['s_nom']=t3_2['s_nom_A']
		t3_2['x']=t3_2['x']/s_system
		t3_2['r']=t3_2['r']/s_system
		t3_2['v0']=t3_2['aux_bus_v_nom']
		t3_2['v1']=t3_2['v_nom_2']
		t3_2['wind0']=t3_2['aux_bus_wind']
		t3_2['wind1']=t3_2['wind2']
		t3_2['name'] = 'three_wind_J_'+t3_2['trans_id']
		t3_2=t3_2[trans_cols]
		
		t3_3 = t3.copy().rename(index=str,columns={'K':'bus1','x3':'x','r3':'r','RATA3':'s_nom_A','RATB3':'s_nom_B','RATC3':'s_nom_C','ANG3':'phase_shift','STAT':'status'})
		t3_3['bus0']=t3_3['aux_bus']
		t3_3['s_nom']=t3_3['s_nom_A']
		t3_3['x']=t3_3['x']/s_system
		t3_3['r']=t3_3['r']/s_system
		t3_3['v0']=t3_3['aux_bus_v_nom']
		t3_3['v1']=t3_3['v_nom_3']
		t3_3['wind0']=t3_3['aux_bus_wind']
		t3_3['wind1']=t3_3['wind3']
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
	'twodc':format_twodc,
	'switchedshunt':format_switchedshunt,
	'fixedshunt':format_fixedshunt
}

def format_all(raw_data):
	out={}
	for i in raw_data:
		if 'df' in raw_data[i] and i in format_dict:
			out[i]=format_dict[i](raw_data[i]['df'])
	return out