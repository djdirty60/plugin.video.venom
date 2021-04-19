# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.debrid import alldebrid
from resources.lib.debrid import premiumize
from resources.lib.debrid import realdebrid

def debrid_resolvers(order_matters=True):
	try:
		ad_enabled = control.setting('alldebrid.token') != '' and control.setting('alldebrid.enable') == 'true'
		pm_enabled = control.setting('premiumize.token') != '' and control.setting('premiumize.enable') == 'true'
		rd_enabled = control.setting('realdebrid.token') != '' and control.setting('realdebrid.enable') == 'true'
		premium_resolvers = []
		if ad_enabled: premium_resolvers.append(alldebrid.AllDebrid())
		if pm_enabled: premium_resolvers.append(premiumize.Premiumize())
		if rd_enabled: premium_resolvers.append(realdebrid.RealDebrid())
		if order_matters:
			premium_resolvers.sort(key=lambda x: get_priority(x))
			# log_utils.log('premium_resolvers sorted = %s' % str(premium_resolvers), __name__, log_utils.LOGDEBUG)
		return premium_resolvers
	except:
		log_utils.error()

def status():
	return debrid_resolvers() != []

def get_priority(cls):
	try:
		return int(control.setting((cls.__class__.__name__ + '.priority').lower()))
	except:
		log_utils.error()
		return 10