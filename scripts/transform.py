#!/usr/bin/python

## Transformation script for geojson


import os
import jinja2
import sys
import json
import yaml
import copy
#import ijson.backends.yajl2 as ijson
import itertools
from collections import OrderedDict

import logging

logger = logging.getLogger('ao.transform')

def build_render_from_string(string):
    env = jinja2.Environment()
    return env.from_string(string)




def nested_get(obj,path):
    keys = path.split('.')
    for k in keys:
        try:
            obj = obj[k]
        except KeyError:
            return None
    return obj

def nested_set(obj,path,value):
    keys = path.split('.')
    for k in keys[:-1]:
        if k not in obj.keys():
            obj[k] = {}
        obj = obj[k]
    obj[keys[-1]] = value


def isNaN(num):
    return num != num

def from_wkt(geom):
    out = {}
    if geom.geom_type == 'Point' and geom.x and geom.y:
        if not isNaN(geom.x) and not isNaN(geom.y):
            out['lat']=geom.y
            out['long']=geom.x
    elif geom.geom_type == 'LineString':
        path=[[point[1],point[0]] for point in geom.coords if not isNaN(point[1]) and not isNaN(point[0])]
        if len(path)>=2:
            out['path']=path
    elif geom.geom_type == 'LinearRing':
        ring=[[point[1],point[0]] for point in geom.coords]
        out['ring']=ring
    else:
        logger.debug(geom.geom_type)
        out['wkt']=str(geom)
    return out


class Transform:
    base={}
    render={}

    def __init__(self,template_file):
        logger.debug("Loading Template",template_file)

        with open(template_file,'r') as in_file:
            template=yaml.load(in_file)

        ## flatten parameters
        if 'parameter' in template:
            for i in template['parameter']:
                obj=template['parameter'][i]
                obj['set']='parameter.'+i
                logger.debug('Parameters',i,obj)
                template[i]=obj
            del template['parameter']

        for i in template:
            if 'template' in template[i]:
                logger.debug('Building Render',i)
                self.render[i]=build_render_from_string(template[i]['template'])

        ## build renders
        logger.debug(template)

        self.template=OrderedDict(sorted(template.items(),key=lambda item: item[1].get('order',100)))
        logger.debug(self.template)
        ## load renders

    def transform_item(self,item):
        out=copy.copy(self.base)
        for key in self.template:
            #logger.debug item
            t = self.template[key]
            value=None
            ## Get Value
            if 'constant' in t:
                value = t['constant']
            elif 'value' in t:
                value = nested_get(item,t['value'])
            elif 'template' in t:
                value = self.render[key].render(item)

            ## Check if NAN
            if 'na_value' in t and value:
                try:
                    if value==t['na_value']:
                        value=None
                except:
                    pass
                try:    
                    if value in t['na_value']:
                        value=None
                except:
                    pass

            if 'itemif' in t and not nested_get(item,t['itemif']):
                value=None
            if 'outif' in t and not nested_get(out,t['outif']):
                value=None

            if 'to_string' in t:
                value=str(value)

            if 'strip_whitespace' in t:
                value=" ".join(value.split())

            if 'location' in t:
                value=from_wkt(value)
            if 'str' in t:
                value=str(value)

            nested_set(item,key,value)
            if value and 'set' in t:
                nested_set(out,t['set'],value)
        return item['key'],out

    def to_file(self,items,outfilename):
        logger.debug('Output items to',outfilename)
        with open(outfilename, 'w') as outfile:   
            logger.debug("Starting Render")
            count=0 
            outdict={}
            for item in items:
                key,transformed=self.transform_item(item._asdict())
                outdict[key]=transformed
                count+=1
                if count%1000==0:
                    logger.debug(count)

            json.dump(outdict,outfile)
            logger.debug("Render Complete")
        logger.info("Transformation Complete")


