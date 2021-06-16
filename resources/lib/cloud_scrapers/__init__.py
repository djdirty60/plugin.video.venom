# -*- coding: UTF-8 -*-

import os
from pkgutil import walk_packages
from resources.lib.modules.control import setting as getSetting

debug_enabled = getSetting('debug.enabled') == 'true'


def cloudSources():
	try:
		sourceDict = []
		sourceFolderLocation = os.path.dirname(__file__)
		for loader, module_name, is_pkg in walk_packages([sourceFolderLocation]):
			if is_pkg: continue
			if enabledCheck(module_name):
				try:
					module = loader.find_module(module_name).load_module(module_name)
					sourceDict.append((module_name, module.source()))
				except Exception as e:
					if debug_enabled:
						from resources.lib.modules import log_utils
						log_utils.log('Error: Loading module: "%s": %s' % (module_name, e), level=log_utils.LOGWARNING)
		return sourceDict
	except:
		from resources.lib.modules import log_utils
		log_utils.error()
		return []

def enabledCheck(module_name):
	try:
		if getSetting(module_name + '.enabled') == 'true': return True
		else: return False
	except:
		from resources.lib.modules import log_utils
		log_utils.error()
		return True