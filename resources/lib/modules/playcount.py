# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from resources.lib.modules.control import setting as getSetting, refresh as containerRefresh, addonInfo, progressDialogBG, monitor, condVisibility, execute
from resources.lib.modules import trakt
tmdb_api_key = '3320855e65a9758297fec4f7c9717698'
omdb_api_key = 'd4daa2b'
tvdb_api_key = '06cff30690f9b9622957044f2159ffae'
traktIndicators = trakt.getTraktIndicatorsInfo()
if not traktIndicators:
	try:
		if not condVisibility('System.HasAddon(script.module.metahandler)'): execute('InstallAddon(script.module.metahandler)', wait=True)
	except: pass


def getMovieIndicators(refresh=False):
	try:
		if traktIndicators:
			if not refresh: timeout = 720
			elif trakt.getMoviesWatchedActivity() < trakt.timeoutsyncMovies(): timeout = 720
			else: timeout = 0
			indicators = trakt.cachesyncMovies(timeout=timeout)
			return indicators
		else:
			from metahandler import metahandlers
			indicators = metahandlers.MetaData(tmdb_api_key, omdb_api_key, tvdb_api_key)
			return indicators
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def getTVShowIndicators(refresh=False):
	try:
		if traktIndicators:
			if not refresh: timeout = 720
			elif trakt.getEpisodesWatchedActivity() < trakt.timeoutsyncTVShows(): timeout = 720
			else: timeout = 0
			indicators = trakt.cachesyncTVShows(timeout=timeout)
			return indicators
		else:
			from metahandler import metahandlers
			indicators = metahandlers.MetaData(tmdb_api_key, omdb_api_key, tvdb_api_key)
			return indicators
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def getSeasonIndicators(imdb, refresh=False):
	try:
		if traktIndicators:
			timeoutsyncSeasons = trakt.timeoutsyncSeasons(imdb)
			if timeoutsyncSeasons is None: return # if no entry means no completed season watched so do not make needless requests 
			if not refresh: timeout = 720
			elif trakt.getEpisodesWatchedActivity() < timeoutsyncSeasons: timeout = 720
			else: timeout = 0
			indicators = trakt.cachesyncSeasons(imdb=imdb, timeout=timeout)[0]
			return indicators
		else:
			from metahandler import metahandlers
			indicators = metahandlers.MetaData(tmdb_api_key, omdb_api_key, tvdb_api_key)
			return indicators
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def getMovieOverlay(indicators, imdb):
	if not indicators: return '4'
	try:
		if traktIndicators:
			playcount = [i for i in indicators if i == imdb]
			playcount = 5 if len(playcount) > 0 else 4
			return str(playcount)
		else:
			playcount = indicators._get_watched('movie', imdb, '', '')
			return str(playcount)
	except:
		from resources.lib.modules import log_utils
		log_utils.error()
		return '4'

def getTVShowOverlay(indicators, imdb, tvdb): # tvdb no longer used
	if not indicators: return '4'
	try:
		if traktIndicators:
			playcount = [i[0] for i in indicators if i[0] == imdb and len(i[2]) >= int(i[1])]
			playcount = 5 if len(playcount) > 0 else 4
			return str(playcount)
		else:
			playcount = indicators._get_watched('tvshow', imdb, '', '')
			return str(playcount)
	except:
		from resources.lib.modules import log_utils
		log_utils.error()
		return '4'

def getSeasonOverlay(indicators, imdb, tvdb, season): # tvdb no longer used
	if not indicators: return '4'
	try:
		if traktIndicators:
			playcount = [i for i in indicators if int(season) == int(i)]
			playcount = 5 if len(playcount) > 0 else 4
			return str(playcount)
		else:
			playcount = indicators._get_watched('season', imdb, '', season)
			return str(playcount)
	except:
		from resources.lib.modules import log_utils
		log_utils.error()
		return '4'

def getEpisodeOverlay(indicators, imdb, tvdb, season, episode): # tvdb no longer used
	if not indicators: return '4'
	try:
		if traktIndicators:
			playcount = [i[2] for i in indicators if i[0] == imdb]
			playcount = playcount[0] if len(playcount) > 0 else []
			playcount = [i for i in playcount if int(season) == int(i[0]) and int(episode) == int(i[1])]
			playcount = 5 if len(playcount) > 0 else 4
			return str(playcount)
		else:
			playcount = indicators._get_watched_episode({'imdb_id': imdb, 'season': season, 'episode': episode, 'premiered': ''})
			# from resources.lib.modules import log_utils
			# log_utils.log('playcount=%s' % playcount)
			return str(playcount)
	except:
		from resources.lib.modules import log_utils
		log_utils.error()
		return '4'

def getShowCount(indicators, imdb, tvdb):
	if not imdb.startswith('tt'): return None
	try:
		if traktIndicators:
			if indicators and imdb in str(indicators):
				for indicator in indicators:
					if indicator[0] == imdb:
						total = indicator[1]
						watched = len(indicator[2])
						unwatched = total - watched
						return {'total': total, 'watched': watched, 'unwatched': unwatched}
			elif not indicators: # service sync provides so should always have value, leave for fallback
				result = trakt.showCount(imdb)
				return result
			else: # TMDb has "total_aired_episodes" now so return None and it will be used when indicators is populated but imdb id not found(means show has never been watched)
				return None
		else:
			return None # this code below for metahandler does not aply here nor does the addon offer a means to return such counts
			if not indicators: return None
			for indicator in indicators:
				if indicator[0] == tvdb:
					total = indicator[1]
					watched = len(indicator[2])
					unwatched = total - watched
					return {'total': total, 'watched': watched, 'unwatched': unwatched}
	except:
		from resources.lib.modules import log_utils
		log_utils.error()
		return None

def getSeasonCount(imdb, season=None):
	if not imdb.startswith('tt'): return None
	try:
		if not traktIndicators: return None # metahandler does not currently provide counts
		result = trakt.seasonCount(imdb)
		if not result: return None
		if not season: return result
		else: return result.get(int(season))
	except:
		from resources.lib.modules import log_utils
		log_utils.error()
		return None

def markMovieDuringPlayback(imdb, watched):
	try:
		if traktIndicators:
			if int(watched) == 5: trakt.markMovieAsWatched(imdb)
			else: trakt.markMovieAsNotWatched(imdb)
			trakt.cachesyncMovies()
		else:
			from metahandler import metahandlers
			metaget = metahandlers.MetaData(tmdb_api_key, omdb_api_key, tvdb_api_key)
			metaget.get_meta('movie', name='', imdb_id=imdb)
			metaget.change_watched('movie', name='', imdb_id=imdb, watched=int(watched))
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def markEpisodeDuringPlayback(imdb, tvdb, season, episode, watched):
	try:
		if traktIndicators:
			if int(watched) == 5: trakt.markEpisodeAsWatched(imdb, tvdb, season, episode)
			else: trakt.markEpisodeAsNotWatched(imdb, tvdb, season, episode)
			trakt.cachesyncTV(imdb) # updates all watched shows, as well as season indicators and counts for given imdb_id show
		else:
			from metahandler import metahandlers
			metaget = metahandlers.MetaData(tmdb_api_key, omdb_api_key, tvdb_api_key)
			metaget.get_meta('tvshow', name='', imdb_id=imdb)
			metaget.get_episode_meta('', imdb_id=imdb, season=season, episode=episode)
			metaget.change_watched('episode', '', imdb_id=imdb, season=season, episode=episode, watched=int(watched))
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def movies(name, imdb, watched):
	try:
		if traktIndicators:
			if int(watched) == 5: trakt.watch(name=name, imdb=imdb, refresh=True)
			else: trakt.unwatch(name=name, imdb=imdb, refresh=True)
		else:
			from metahandler import metahandlers
			metaget = metahandlers.MetaData(tmdb_api_key, omdb_api_key, tvdb_api_key)
			metaget.get_meta('movie', name=name, imdb_id=imdb)
			metaget.change_watched('movie', name=name, imdb_id=imdb, watched=int(watched))
			containerRefresh()
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def episodes(name, imdb, tvdb, season, episode, watched):
	try:
		if traktIndicators:
			if int(watched) == 5: trakt.watch(name=name, imdb=imdb, tvdb=tvdb, season=season, episode=episode, refresh=True)
			else: trakt.unwatch(name=name, imdb=imdb, tvdb=tvdb, season=season, episode=episode, refresh=True)
		else:
			from metahandler import metahandlers

			from resources.lib.modules import log_utils
			log_utils.log('name=%s' % name)

			metaget = metahandlers.MetaData(tmdb_api_key, omdb_api_key, tvdb_api_key)
			show_meta = metaget.get_meta('tvshow', name=name, imdb_id=imdb)
			log_utils.log('show_meta=%s' % show_meta)

			episode_meta = metaget.get_episode_meta(name, imdb_id=imdb, season=season, episode=episode)
    # def get_episode_meta(self, tvshowtitle, imdb_id, season, episode, air_date='', episode_title='', overlay=''):

			log_utils.log('episode_meta=%s' % episode_meta)

			log_utils.log('imdb=%s' % imdb)
			log_utils.log('tvdb=%s' % tvdb)
			log_utils.log('season=%s' % season)
			log_utils.log('episode=%s' % episode)
			log_utils.log('watched=%s' % watched)

			metaget.change_watched('episode', '', imdb_id=imdb, season=season, episode=episode, watched=int(watched))
    # def change_watched(self, media_type, name, imdb_id, tmdb_id='', season='', episode='', year='', watched='', air_date=''):

			# watched_episodes = metaget._get_watched_episode({'imdb_id': imdb, 'season': season, 'episode': episode, 'premiered': ''})
			watched_episodes = metaget._get_watched_episode({'imdb_id': imdb, 'tvdb_id': tvdb, 'season': season, 'episode': episode, 'premiered': ''})

			log_utils.log('watched_episodes=%s' % watched_episodes)

			# tvshowsUpdate(imdb=imdb, tvdb=tvdb) # control.refresh() done in this function
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def seasons(tvshowtitle, imdb, tvdb, season, watched):
	tvshows(tvshowtitle=tvshowtitle, imdb=imdb, tvdb=tvdb, season=season, watched=watched)

def tvshows(tvshowtitle, imdb, tvdb, season, watched):
	watched = int(watched)
	try:
		if traktIndicators:
			if watched == 5: trakt.watch(name=tvshowtitle, imdb=imdb, tvdb=tvdb, season=season, refresh=True)
			else: trakt.unwatch(name=tvshowtitle, imdb=imdb, tvdb=tvdb, season=season, refresh=True)
		else:
			from metahandler import metahandlers
			from resources.lib.menus import episodes
			from sys import exit as sysexit

			name = addonInfo('name')
			dialog = progressDialogBG
			dialog.create(str(name), str(tvshowtitle))
			dialog.update(0, str(name), str(tvshowtitle))

			metaget = metahandlers.MetaData(tmdb_api_key, omdb_api_key, tvdb_api_key)
			metaget.get_meta('tvshow', name='', imdb_id=imdb)

			items = episodes.Episodes().get(tvshowtitle, '0', imdb, tvdb, {}, create_directory=False)

			for i in range(len(items)):
				items[i]['season'] = int(items[i]['season'])
				items[i]['episode'] = int(items[i]['episode'])
			try: items = [i for i in items if int('%01d' % int(season)) == int('%01d' % i['season'])]
			except: pass

			items = [{'label': '%s S%02dE%02d' % (tvshowtitle, i['season'], i['episode']), 'season': int('%01d' % i['season']), 'episode': int('%01d' % i['episode'])} for i in items]
			count = len(items)
			for i in range(count):
				if monitor.abortRequested(): return sysexit()
				dialog.update(int(100.0 / count * i), str(name), str(items[i]['label']))
				season, episode = items[i]['season'], items[i]['episode']
				metaget.get_episode_meta('', imdb_id=imdb, season=season, episode=episode)
				metaget.change_watched('episode', '', imdb_id=imdb, season=season, episode=episode, watched=watched)
			tvshowsUpdate(imdb=imdb, tvdb=tvdb)

			try: dialog.close()
			except: pass
			del dialog
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def tvshowsUpdate(imdb, tvdb):
	try:
		if traktIndicators: return
		from metahandler import metahandlers
		from resources.lib.menus import seasons, episodes
		from resources.lib.indexers import tmdb as tmdb_indexer
		from resources.lib.database import cache
		from resources.lib.modules import log_utils

		# name = addonInfo('name')
		metaget = metahandlers.MetaData(tmdb_api_key, omdb_api_key, tvdb_api_key)
		show_meta = metaget.get_meta('tvshow', name='', imdb_id=imdb)
		log_utils.log('show_meta=%s' % show_meta)

		tvshowtitle = show_meta.get('title', '') # useless because it's in cleantitle format
		log_utils.log('tvshowtitle=%s' % tvshowtitle)

		# seasons_meta = seasons.Seasons().get('', '', imdb, '', tvdb, {}, create_directory=False)
		# items = seasons.Seasons().get('', '', imdb, '', tvdb, {}, create_directory=False)
	# def get(self, tvshowtitle, year, imdb, tmdb, tvdb, art, idx=True, create_directory=True):

		tmdb = ''
		if not tmdb and (imdb or tvdb):
			try:
				result = cache.get(tmdb_indexer.TVshows().IdLookup, 96, imdb, tvdb)
				tmdb = str(result.get('id')) if result else ''
			except:
				if control.setting('debug.level') != '1': return
				from resources.lib.modules import log_utils
				return log_utils.log('tvshowtitle: (%s) missing tmdb_id: ids={imdb: %s, tmdb: %s, tvdb: %s}' % (tvshowtitle, imdb, tmdb, tvdb), __name__, log_utils.LOGDEBUG) # log TMDb shows that they do not have
		items = cache.get(tmdb_indexer.TVshows().get_showSeasons_meta, 96, tmdb)
		log_utils.log('items=%s' % items)
		items = items.get('seasons', [])
		# for i in items:

		# items = episodes.Episodes().get('', '', imdb, '', tvdb, {}, create_directory=False)
	# def get(self, tvshowtitle, year, imdb, tmdb, tvdb, meta, season=None, episode=None, create_directory=True):
		# log_utils.log('items=%s' % items)

		for i in range(len(items)):
			log_utils.log('items[i]=%s' % items[i])

			items[i]['season'] = int(items[i]['season'])
			items[i]['episode'] = int(items[i]['episode'])

		seasons = {}
		for i in items:
			if i['season'] not in seasons: seasons[i['season']] = []
			seasons[i['season']].append(i)

		countSeason = 0
		metaget.get_seasons('', imdb, seasons.keys()) # Must be called to initialize the database.

		for key, value in iter(seasons.items()):
			countEpisode = 0
			for i in value:
				countEpisode += int(metaget._get_watched_episode({'imdb_id': i['imdb'], 'season': i['season'], 'episode': i['episode'], 'premiered': ''}) == 5)
			countSeason += int(countEpisode == len(value))
			metaget.change_watched('season', '', imdb_id=imdb, season=key, watched = 5 if countEpisode == len(value) else 4)
		metaget.change_watched('tvshow', '', imdb_id=imdb, watched = 5 if countSeason == len(seasons.keys()) else 4)
	except:
		from resources.lib.modules import log_utils
		log_utils.error()
	containerRefresh()