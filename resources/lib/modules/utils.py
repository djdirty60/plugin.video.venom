# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from json import loads as jsloads
import re
from resources.lib.modules import py_tools


def json_load_as_str(file_handle):
	return byteify(jsloads(file_handle, object_hook=byteify), ignore_dicts=True)

def json_loads_as_str(json_text):
	return byteify(jsloads(json_text, object_hook=byteify), ignore_dicts=True)

def byteify(data, ignore_dicts=False):
	if isinstance(data, py_tools.string_types):
		if py_tools.isPY2:
			return data.encode('utf-8')
		else:
			return data
	if isinstance(data, list):
		return [byteify(item, ignore_dicts=True) for item in data]
	if isinstance(data, dict) and not ignore_dicts:
		return dict([(byteify(key, ignore_dicts=True), byteify(value, ignore_dicts=True)) for key, value in py_tools.iteritems(data)])
	return data

def title_key(title):
	try:
		if not title: title = ''
		articles_en = ['the', 'a', 'an']
		articles_de = ['der', 'die', 'das']
		articles = articles_en + articles_de
		match = re.match(r'^((\w+)\s+)', title.lower())
		if match and match.group(2) in articles: offset = len(match.group(1))
		else: offset = 0
		return title[offset:]
	except:
		return title