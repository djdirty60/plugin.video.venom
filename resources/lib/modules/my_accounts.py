# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

import myaccounts
from resources.lib.modules import control

def syncMyAccounts(silent=False):
	try:
		all_acct = myaccounts.getAll()
		trakt_acct = all_acct.get('trakt')
		if control.setting('trakt.username') != trakt_acct.get('username'):
			control.setSetting('trakt.isauthed', 'true')
			control.setSetting('trakt.token', trakt_acct.get('token'))
			control.setSetting('trakt.username', trakt_acct.get('username'))
			control.setSetting('trakt.refresh', trakt_acct.get('refresh'))
			control.setSetting('trakt.expires', trakt_acct.get('expires'))
		ad_acct = all_acct.get('alldebrid')
		if control.setting('alldebrid.username') != ad_acct.get('username'):
			control.setSetting('alldebrid.token', ad_acct.get('token'))
			control.setSetting('alldebrid.username', ad_acct.get('username'))
		pm_acct = all_acct.get('premiumize')
		if control.setting('premiumize.username') != pm_acct.get('username'):
			control.setSetting('premiumize.token', pm_acct.get('token'))
			control.setSetting('premiumize.username', pm_acct.get('username'))
		rd_acct = all_acct.get('realdebrid')
		if control.setting('realdebrid.username') != rd_acct.get('username'):
			control.setSetting('realdebrid.token', rd_acct.get('token'))
			control.setSetting('realdebrid.username', rd_acct.get('username'))
			control.setSetting('realdebrid.client_id', rd_acct.get('client_id'))
			control.setSetting('realdebrid.refresh', rd_acct.get('refresh'))
			control.setSetting('realdebrid.secret', rd_acct.get('secret'))
		fanart_acct = all_acct.get('fanart_tv')
		if control.setting('fanart.tv.api.key') != fanart_acct.get('api_key'):
			control.setSetting('fanart.tv.api.key', fanart_acct.get('api_key'))
		tmdb_acct = all_acct.get('tmdb')
		if control.setting('tmdb.api.key') != tmdb_acct.get('api_key'):
			control.setSetting('tmdb.api.key', tmdb_acct.get('api_key'))
		if control.setting('tmdb.username') != tmdb_acct.get('username'):
			control.setSetting('tmdb.username', tmdb_acct.get('username'))
		if control.setting('tmdb.password') != tmdb_acct.get('password'):
			control.setSetting('tmdb.password', tmdb_acct.get('password'))
		if control.setting('tmdb.session_id') != tmdb_acct.get('session_id'):
			control.setSetting('tmdb.session_id', tmdb_acct.get('session_id'))
		tvdb_acct = all_acct.get('tvdb')
		if control.setting('tvdb.api.key') != tvdb_acct.get('api_key'):
			control.setSetting('tvdb.api.key', tvdb_acct.get('api_key'))
		imdb_acct = all_acct.get('imdb')
		if control.setting('imdb.user') != imdb_acct.get('user'):
			control.setSetting('imdb.user', imdb_acct.get('user'))
		fu_acct = all_acct.get('furk')
		if control.setting('furk.username') != fu_acct.get('username'):
			control.setSetting('furk.username', fu_acct.get('username'))
			control.setSetting('furk.password', fu_acct.get('password'))
		if fu_acct.get('api_key', None):
			if control.setting('furk.api') != fu_acct.get('api_key'):
				control.setSetting('furk.api', fu_acct.get('api_key'))
		if not silent: control.notification(message=32114)
	except:
		from resources.lib.modules import log_utils
		log_utils.error()