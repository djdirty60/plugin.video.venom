# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from datetime import datetime, timedelta
import re
import sys
try: #Py2
	from urllib import quote_plus
except ImportError: #Py3
	from urllib.parse import quote_plus
from resources.lib.modules import cache
from resources.lib.modules import cleangenre
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import playcount
from resources.lib.modules import py_tools
from resources.lib.modules import trakt
from resources.lib.modules import views
from resources.lib.indexers import tvdb_v1
from resources.lib.menus import episodes as episodesx
from resources.lib.menus import tvshows as tvshowsx


class Seasons:
	def __init__(self, type = 'show'):
		self.list = []
		self.type = type
		self.lang = control.apiLanguage()['tvdb']
		self.season_special = False
		self.disable_fanarttv = control.setting('disable.fanarttv')

		# self.date_time = (datetime.utcnow() - timedelta(hours=5))
		self.date_time = datetime.utcnow()
		self.today_date = (self.date_time).strftime('%Y-%m-%d')

		self.tvdb_key = control.setting('tvdb.api.key')
		self.tvdb_image = 'https://thetvdb.com/banners/'
		self.tvdb_poster = 'https://thetvdb.com/banners/_cache/'

		self.trakt_user = control.setting('trakt.user').strip()
		self.traktCredentials = trakt.getTraktCredentialsInfo()
		self.traktwatchlist_link = 'https://api.trakt.tv/users/me/watchlist/seasons'
		self.traktlists_link = 'https://api.trakt.tv/users/me/lists'

		self.showunaired = control.setting('showunaired') or 'true'
		self.unairedcolor = control.getColor(control.setting('unaired.identify'))


	def get(self, tvshowtitle, year, imdb, tmdb, tvdb, idx=True):
		if idx:
			self.list = cache.get(self.tvdb_list, 24, tvshowtitle, year, imdb, tmdb, tvdb, self.lang)
			self.seasonDirectory(self.list)
			return self.list
		else:
			self.list = self.tvdb_list(tvshowtitle, year, imdb, tmdb, tvdb, 'en')
			return self.list


	def seasonList(self, url):
		# Dirty implementation, but avoids rewritting everything from episodes.py.
		episodes = episodesx.Episodes(type = self.type)
		self.list = cache.get(episodes.trakt_list, 0.3, url, self.trakt_user)
		self.list = self.list[::-1]

		tvshows = tvshowsx.tvshows(type = self.type)
		tvshows.list = self.list
		tvshows.worker()
		self.list = tvshows.list

		try: # Remove duplicate season entries.
			result = []
			for i in self.list:
				found = False
				for j in result:
					if i['imdb'] == j['imdb'] and i['season'] == j['season']:
						found = True
						break
				if not found:
					result.append(i)
			self.list = result
		except: pass
		self.seasonDirectory(self.list)


	def userlists(self):
		episodes = episodesx.Episodes(type = self.type)
		userlists = []
		try:
			if not self.traktCredentials: raise Exception()
			activity = trakt.getActivity()
		except: pass
		try:
			if not self.traktCredentials: raise Exception()
			self.list = []
			try:
				if activity > cache.timeout(episodes.trakt_user_list, self.traktlists_link, self.trakt_user):
					raise Exception()
				userlists += cache.get(episodes.trakt_user_list, 3, self.traktlists_link, self.trakt_user)
			except:
				userlists += cache.get(episodes.trakt_user_list, 0, self.traktlists_link, self.trakt_user)
		except: pass
		try:
			if not self.traktCredentials: raise Exception()
			self.list = []
			try:
				if activity > cache.timeout(episodes.trakt_user_list, self.traktlikedlists_link, self.trakt_user): raise Exception()
				userlists += cache.get(episodes.trakt_user_list, 3, self.traktlikedlists_link, self.trakt_user)
			except: userlists += cache.get(episodes.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)
		except: pass

		self.list = []
		# Filter the user's own lists that were
		for i in range(len(userlists)):
			contains = False
			adapted = userlists[i]['url'].replace('/me/', '/%s/' % self.trakt_user)
			for j in range(len(self.list)):
				if adapted == self.list[j]['url'].replace('/me/', '/%s/' % self.trakt_user):
					contains = True
					break
			if not contains: self.list.append(userlists[i])
		for i in range(0, len(self.list)): self.list[i].update({'image': 'traktlists.png', 'action': 'seasonsList'})
		if self.traktCredentials: # Trakt Watchlist
			self.list.insert(0, {'name': control.lang(32033), 'url': self.traktwatchlist_link, 'image': 'traktwatch.png', 'action': 'seasons'})
		episodes.addDirectory(self.list, queue = True)
		return self.list


	def tvdb_list(self, tvshowtitle, year, imdb, tmdb, tvdb, lang, limit=''):
		if (tvdb == '0' or tmdb == '0') and imdb != '0':
			try:
				trakt_ids = trakt.IdLookup('imdb', imdb, 'show')
				if trakt_ids:
					if tvdb == '0':
						tvdb = str(trakt_ids.get('tvdb', '0'))
						if not tvdb or tvdb == 'None': tvdb = '0'
					if tmdb == '0':
						tmdb = str(trakt_ids.get('tmdb', '0'))
						if not tmdb or tmdb == 'None': tmdb = '0'
			except:
				log_utils.error()

		if imdb == '0' or tmdb == '0' or tvdb == '0':
			try:
				trakt_ids = trakt.SearchTVShow(quote_plus(tvshowtitle), year, full=False)
				if not trakt_ids: raise Exception()
				trakt_ids = trakt_ids[0].get('show', '0')
				if imdb == '0':
					imdb = trakt_ids.get('ids', {}).get('imdb', '0')
					if not imdb or imdb == 'None': imdb = '0'
					if not imdb.startswith('tt'): imdb = '0'
				if tmdb == '0':
					tmdb = str(trakt_ids.get('ids', {}).get('tmdb', '0'))
					if not tmdb or tmdb == 'None': tmdb = '0'
				if tvdb == '0':
					tvdb = str(trakt_ids.get('ids', {}).get('tvdb', '0'))
					if not tvdb or tvdb == 'None': tvdb = '0'
			except:
				log_utils.error()

		if tvdb == '0' and imdb != '0': # Check TVDb by IMDB_ID for missing tvdb_id
			try: tvdb = cache.get(tvdb_v1.getSeries_ByIMDB, 96, tvshowtitle, year, imdb)
			except: tvdb = '0'
		if tvdb == '0': # Check TVDb by seriesname for missing tvdb_id
			try:
				ids = cache.get(tvdb_v1.getSeries_ByName, 96, tvshowtitle, year)
				if ids: tvdb = ids.get(tvdb, '0') or '0'
			except:
				tvdb = '0'
				log_utils.error()

		if tvdb == '0': return None
		try:
			result, artwork, actors = cache.get(tvdb_v1.getZip, 96, tvdb, True, True)
			dupe = client.parseDOM(result, 'SeriesName')[0]
			dupe = re.compile(r'[***]Duplicate (\d*)[***]').findall(dupe)
			if len(dupe) > 0:
				tvdb = str(dupe[0])
				result, artwork, actors = cache.get(tvdb_v1.getZip, 96, tvdb, True, True)

			artwork = artwork.split('<Banner>')
			artwork = [i for i in artwork if '<Language>en</Language>' in i and '<BannerType>season</BannerType>' in i]
			artwork = [i for i in artwork if not 'seasonswide' in re.findall(r'<BannerPath>(.+?)</BannerPath>', i)[0]]

			result = result.split('<Episode>')
			item = result[0]

			episodes = [i for i in result if '<EpisodeNumber>' in i]
			if control.setting('tv.specials') == 'true':
				episodes = [i for i in episodes]
			else:
				episodes = [i for i in episodes if not '<SeasonNumber>0</SeasonNumber>' in i]
				episodes = [i for i in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in i]

			# season still airing check for pack scraping
			premiered_eps = [i for i in episodes if not '<FirstAired></FirstAired>' in i]
			unaired_eps = [i for i in premiered_eps if int(re.sub(r'[^0-9]', '', str(client.parseDOM(i, 'FirstAired')))) > int(re.sub(r'[^0-9]', '', str(self.today_date)))]
			if unaired_eps: still_airing = client.parseDOM(unaired_eps, 'SeasonNumber')[0]
			else: still_airing = None

			seasons = [i for i in episodes if '<EpisodeNumber>1</EpisodeNumber>' in i]
			counts = self.seasonCountParse(seasons=seasons, episodes=episodes)
			# locals = [i for i in result if '<EpisodeNumber>' in i]

			if limit == '': episodes = []
			elif limit == '-1': seasons = []
			else:
				episodes = [i for i in episodes if '<SeasonNumber>%01d</SeasonNumber>' % int(limit) in i]
				seasons = []

			poster = client.replaceHTMLCodes(client.parseDOM(item, 'poster')[0])
			if poster != '': poster = '%s%s' % (self.tvdb_image, poster)

			fanart = client.replaceHTMLCodes(client.parseDOM(item, 'fanart')[0])
			if fanart != '': fanart = '%s%s' % (self.tvdb_image, fanart)

			banner = client.replaceHTMLCodes(client.parseDOM(item, 'banner')[0])
			if banner != '': banner = '%s%s' % (self.tvdb_image, banner)

			if poster != '': pass
			elif fanart != '': poster = fanart
			elif banner != '': poster = banner

			if banner != '': pass
			elif fanart != '': banner = fanart
			elif poster != '': banner = poster

			status = client.replaceHTMLCodes(client.parseDOM(item, 'Status')[0]) or 'Ended'
			studio = client.replaceHTMLCodes(client.parseDOM(item, 'Network')[0]) or ''
			genre = client.replaceHTMLCodes(client.parseDOM(item, 'Genre')[0])
			genre = ' / '.join([x for x in genre.split('|') if x != ''])
			duration = client.replaceHTMLCodes(client.parseDOM(item, 'Runtime')[0])
			rating = client.replaceHTMLCodes(client.parseDOM(item, 'Rating')[0])
			votes = client.replaceHTMLCodes(client.parseDOM(item, 'RatingCount')[0])
			mpaa = client.replaceHTMLCodes(client.parseDOM(item, 'ContentRating')[0])
			castandart = tvdb_v1.parseActors(actors)
			label = client.replaceHTMLCodes(client.parseDOM(item, 'SeriesName')[0])
			plot = client.replaceHTMLCodes(client.parseDOM(item, 'Overview')[0])
			plot = py_tools.ensure_str(plot)
		except:
			log_utils.error()

		for item in seasons:
			try:
				premiered = client.replaceHTMLCodes(client.parseDOM(item, 'FirstAired')[0]) or '0'
				# Show Unaired items.
				unaired = ''
				if status.lower() == 'ended': pass
				elif premiered == '0':
					unaired = 'true'
					if self.showunaired != 'true': continue
					pass
				elif int(re.sub(r'[^0-9]', '', str(premiered))) > int(re.sub(r'[^0-9]', '', str(self.today_date))):
					unaired = 'true'
					if self.showunaired != 'true': continue

				season = client.parseDOM(item, 'SeasonNumber')[0]
				season = '%01d' % int(season)

				thumb = [i for i in artwork if client.parseDOM(i, 'Season')[0] == season]
				try: thumb = client.replaceHTMLCodes(client.parseDOM(thumb[0], 'BannerPath')[0])
				except: thumb = ''
				if thumb != '': thumb = '%s%s' % (self.tvdb_image, thumb)
				else: thumb = poster

				try: seasoncount = counts[season]
				except: seasoncount = None
				try: total_seasons = len([i for i in counts if i != '0'])
				except: total_seasons = None

				self.list.append({'season': season, 'tvshowtitle': tvshowtitle, 'label': label, 'year': year, 'premiered': premiered,
										'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes,
										'mpaa': mpaa, 'castandart': castandart, 'plot': plot, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb,
										'tvshowid': imdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb,
										'unaired': unaired, 'seasoncount': seasoncount, 'total_seasons': total_seasons})
				self.list = sorted(self.list, key=lambda k: int(k['season'])) # fix for TVDb new sort by ID
			except:
				log_utils.error()

		for item in episodes:
			try:
				title = client.replaceHTMLCodes(client.parseDOM(item, 'EpisodeName')[0])
				title = py_tools.ensure_str(title)
				premiered = client.replaceHTMLCodes(client.parseDOM(item, 'FirstAired')[0]) or '0'
				# Show Unaired items.
				unaired = ''
				if status.lower() == 'ended': pass
				elif premiered == '0':
					unaired = 'true'
					if self.showunaired != 'true': continue
					pass
				elif int(re.sub(r'[^0-9]', '', str(premiered))) > int(re.sub(r'[^0-9]', '', str(self.today_date))):
					unaired = 'true'
					if self.showunaired != 'true': continue

				season = client.parseDOM(item, 'SeasonNumber')[0]
				season = '%01d' % int(season)
				episode = client.parseDOM(item, 'EpisodeNumber')[0]
				episode = re.sub(r'[^0-9]', '', '%01d' % int(episode))

				if still_airing:
					if int(still_airing) == int(season): is_airing = True
					else: is_airing = False
				else: is_airing = False

# ### episode IDS
				episodeIDS = {}
				if control.setting('enable.upnext') == 'true':
					episodeIDS = trakt.getEpisodeSummary(imdb, season, episode, full=False) or {}
					if episodeIDS != {}:
						episodeIDS = episodeIDS.get('ids', {})
##------------------

				thumb = client.replaceHTMLCodes(client.parseDOM(item, 'filename')[0])
				if thumb != '': thumb = '%s%s' % (self.tvdb_image, thumb)

				season_poster = [i for i in artwork if client.parseDOM(i, 'Season')[0] == season]
				try: season_poster = client.replaceHTMLCodes(client.parseDOM(season_poster[0], 'BannerPath')[0])
				except: season_poster = ''
				if season_poster != '': season_poster = '%s%s' % (self.tvdb_image, season_poster)
				else: season_poster = poster

				if thumb != '': pass
				elif fanart != '': thumb = fanart.replace(self.tvdb_image, self.tvdb_poster)
				elif season_poster != '': thumb = season_poster

				rating = client.replaceHTMLCodes(client.parseDOM(item, 'Rating')[0])
				director = client.replaceHTMLCodes(client.parseDOM(item, 'Director')[0])
				director = ' / '.join([x for x in director.split('|') if x != '']) # check if this needs ensure_str()
				writer = client.replaceHTMLCodes(client.parseDOM(item, 'Writer')[0]) 
				writer = ' / '.join([x for x in writer.split('|') if x != '']) # check if this needs ensure_str()
				label = client.replaceHTMLCodes(client.parseDOM(item, 'EpisodeName')[0])

				episodeplot = client.replaceHTMLCodes(client.parseDOM(item, 'Overview')[0]) or plot
				episodeplot = py_tools.ensure_str(episodeplot)

				try: seasoncount = counts[season]
				except: seasoncount = None
				try: total_seasons = len([i for i in counts if i != '0'])
				except: total_seasons = None

				self.list.append({'title': title, 'label': label, 'season': season, 'episode': episode, 'tvshowtitle': tvshowtitle, 'year': year,
										'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating,
										'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'castandart': castandart, 'plot': episodeplot,
										'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb,
										'season_poster': season_poster, 'unaired': unaired, 'seasoncount': seasoncount, 'counts': counts,
										'total_seasons': total_seasons, 'is_airing': is_airing, 'episodeIDS': episodeIDS})
				self.list = sorted(self.list, key=lambda k: (int(k['season']), int(k['episode']))) # fix for TVDb new sort by ID
				# meta = {}
				# meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'lang': self.lang, 'user': self.tvdb_key, 'item': item}
				# self.list.append(item)
				# metacache.insert(self.meta)
			except:
				log_utils.error()
		return self.list


	@classmethod
	def seasonCountParse(self, season=None, items=None, seasons=None, episodes=None):
		# Determine the number of episodes per season to estimate season pack episode sizes.
		index = season
		counts = {} # Do not use a list, since not all seasons are labeled by number. Eg: MythBusters
		if episodes is None:
			episodes = [i for i in items if '<EpisodeNumber>' in i]
			if control.setting('tv.specials') == 'true': episodes = [i for i in episodes]
			else:
				episodes = [i for i in episodes if not '<SeasonNumber>0</SeasonNumber>' in i]
				episodes = [i for i in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in i]
			seasons = [i for i in episodes if '<EpisodeNumber>1</EpisodeNumber>' in i]
		for s in seasons:
			season = client.parseDOM(s, 'SeasonNumber')[0]
			season = '%01d' % int(season)
			# season = season.encode('utf-8')
			counts[season] = 0
		for e in episodes:
			try:
				season = client.parseDOM(e, 'SeasonNumber')[0]
				season = '%01d' % int(season)
				# season = season.encode('utf-8')
				counts[season] += 1
			except: pass
		try:
			if index is None: return counts
			else: return counts[index]
		except:
			return None


	def seasonCount(self, tvshowtitle, year, imdb, tvdb, season):
		try: return cache.get(self._seasonCount, 168, tvshowtitle, year, imdb, tvdb)[season]
		except: return None


	def _seasonCount(self, tvshowtitle, year, imdb, tvdb):
		if imdb == '0':
			try:
				imdb = trakt.SearchTVShow(quote_plus(tvshowtitle), year, full=False)[0]
				imdb = imdb.get('show', '0')
				imdb = imdb.get('ids', {}).get('imdb', '0')
				imdb = 'tt' + re.sub(r'[^0-9]', '', str(imdb))
				if not imdb: imdb = '0'
			except:
				log_utils.error()
				imdb = '0'

		if tvdb == '0' and imdb != '0': # Check TVDb by IMDB_ID for missing
			try: tvdb = tvdb_v1.getSeries_ByIMDB(tvshowtitle, year, imdb) or '0'
			except: tvdb = '0'
		if tvdb == '0': # Check TVDb by seriesname
			try:
				ids = tvdb_v1.getSeries_ByName(tvshowtitle, year)
				if ids: tvdb = ids.get(tvdb, '0') or '0'
			except:
				tvdb = '0'
				log_utils.error()

		if tvdb == '0': return None
		try:
			result = tvdb_v1.getZip(tvdb)
			dupe = client.parseDOM(result, 'SeriesName')[0]
			dupe = re.compile(r'[***]Duplicate (\d*)[***]').findall(dupe)
			if len(dupe) > 0:
				# tvdb = str(dupe[0]).encode('utf-8')
				tvdb = str(dupe[0])
				result = tvdb_v1.getZip(tvdb)
			result = result.split('<Episode>')
			return self.seasonCountParse(items=result)
		except:
			log_utils.error()
			return None


	def seasonDirectory(self, items):
		if not items:
			control.hide()
			control.notification(title=32054, message=33049)
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		is_widget = 'plugin' not in control.infoLabel('Container.PluginName')
		settingFanart = control.setting('fanart')
		addonPoster = control.addonPoster()
		addonFanart = control.addonFanart()
		addonBanner = control.addonBanner()

		try: indicators = playcount.getSeasonIndicators(items[0]['imdb'], refresh=True)
		except: indicators = None
		unwatchedEnabled = control.setting('tvshows.unwatched.enabled') == 'true'

		if trakt.getTraktIndicatorsInfo():
			watchedMenu = control.lang(32068)
			unwatchedMenu = control.lang(32069)
		else:
			watchedMenu = control.lang(32066)
			unwatchedMenu = control.lang(32067)
		traktManagerMenu = control.lang(32070)
		queueMenu = control.lang(32065)
		showPlaylistMenu = control.lang(35517)
		clearPlaylistMenu = control.lang(35516)
		labelMenu = control.lang(32055)
		playRandom = control.lang(32535)
		addToLibrary = control.lang(32551)

		try: multi = [i['tvshowtitle'] for i in items]
		except: multi = []
		multi = len([x for y,x in enumerate(multi) if x not in multi[:y]])
		multi = True if multi > 1 else False

		if self.disable_fanarttv != 'true':
			tvdb = [i['tvdb'] for i in items][0]
			from resources.lib.indexers import fanarttv
			extended_art = cache.get(fanarttv.get_tvshow_art, 168, tvdb)
		else: extended_art = None

		for i in items:
			try:
				imdb, tmdb, tvdb, year, season = i.get('imdb', '0'), i.get('tmdb', '0'), i.get('tvdb', '0'), i.get('year', '0'), i['season']
				title = i['tvshowtitle']
				label = '%s %s' % (labelMenu, i['season'])

				if not self.season_special and control.setting('tv.specials') == 'true':
					self.season_special = True if int(season) == 0 else False
				try:
					if i['unaired'] == 'true': label = '[COLOR %s][I]%s[/I][/COLOR]' % (self.unairedcolor, label)
				except: pass

				systitle = quote_plus(title)
				meta = dict((k, v) for k, v in control.iteritems(i) if v and v != '0')
				meta.update({'code': imdb, 'imdbnumber': imdb, 'mediatype': 'tvshow', 'tag': [imdb, tvdb]})
				try: meta['plot'] = control.cleanPlot(meta['plot']) # Some plots have a link at the end remove it.
				except: pass
				try: meta.update({'duration': str(int(meta['duration']) * 60)})
				except: pass
				try: meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
				except: pass
				try: meta.update({'tvshowtitle': i['label']})
				except: pass

				try:
					# Year is the shows year, not the seasons year. Extract the correct year from the premier date.
					yearNew = re.findall(r'(\d{4})', i['premiered'])[0]
					# yearNew = yearNew.encode('utf-8')
					meta.update({'year': yearNew})
				except: pass

				# First check thumbs, since they typically contains the seasons poster. The normal poster contains the show poster.
				poster = meta.get('thumb') or meta.get('poster3') or meta.get('poster2') or meta.get('poster') or addonPoster
				fanart = ''
				if settingFanart:
					fanart = meta.get('fanart3') or meta.get('fanart2') or meta.get('fanart') or addonFanart
				thumb = meta.get('thumb') or poster
				icon = meta.get('icon') or poster
				banner = meta.get('banner3') or meta.get('banner2') or meta.get('banner') or addonBanner
				if extended_art:
					clearlogo = extended_art.get('clearlogo')
					clearart = extended_art.get('clearart')
				else: clearlogo = '0' ; clearart = '0'
				art = {}
				art.update({'poster': poster, 'tvshow.poster': poster, 'season.poster': poster, 'fanart': fanart, 'icon': icon,
									'thumb': thumb, 'banner': banner, 'clearlogo': clearlogo, 'clearart': clearart})

####-Context Menu and Overlays-####
				cm = []
				if self.traktCredentials:
					cm.append((traktManagerMenu, 'RunPlugin(%s?action=tools_traktManager&name=%s&imdb=%s&tvdb=%s&season=%s)' % (sysaddon, systitle, imdb, tvdb, season)))

				try:
					overlay = int(playcount.getSeasonOverlay(indicators, imdb, tvdb, season))
					watched = overlay == 7
					if watched:
						meta.update({'playcount': 1, 'overlay': 7})
						cm.append((unwatchedMenu, 'RunPlugin(%s?action=playcount_TVShow&name=%s&imdb=%s&tvdb=%s&season=%s&query=6)' % (sysaddon, systitle, imdb, tvdb, season)))
					else: 
						meta.update({'playcount': 0, 'overlay': 6})
						cm.append((watchedMenu, 'RunPlugin(%s?action=playcount_TVShow&name=%s&imdb=%s&tvdb=%s&season=%s&query=7)' % (sysaddon, systitle, imdb, tvdb, season)))
				except: pass

				url = '%s?action=episodes&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&season=%s' % (sysaddon, systitle, year, imdb, tmdb, tvdb, season)
				cm.append((playRandom, 'RunPlugin(%s?action=random&rtype=episode&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s&season=%s)' % (
									sysaddon, systitle, year, imdb, tvdb, season)))

				cm.append((queueMenu, 'RunPlugin(%s?action=playlist_QueueItem&name=%s)' % (sysaddon, systitle)))
				cm.append((showPlaylistMenu, 'RunPlugin(%s?action=playlist_Show)' % sysaddon))
				cm.append((clearPlaylistMenu, 'RunPlugin(%s?action=playlist_Clear)' % sysaddon))
				cm.append((addToLibrary, 'RunPlugin(%s?action=library_tvshowToLibrary&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s)' % (sysaddon, systitle, year, imdb, tmdb, tvdb)))
				cm.append(('[COLOR red]Venom Settings[/COLOR]', 'RunPlugin(%s?action=tools_openSettings)' % sysaddon))
####################################

				if not i.get('trailer'):
					meta.update({'trailer': '%s?action=trailer&type=%s&name=%s&year=%s&imdb=%s' % (sysaddon, 'show', quote_plus(title), year, imdb)})

				item = control.item(label = label)
				if 'castandart' in i: item.setCast(i['castandart'])
				if 'episodeIDS' in i: item.setUniqueIDs(i['episodeIDS'])
				if unwatchedEnabled:
					count = playcount.getSeasonCount(imdb, season, self.season_special)
					if count:
						item.setProperty('TotalEpisodes', str(count['total']))
						item.setProperty('WatchedEpisodes', str(count['watched']))
						item.setProperty('UnWatchedEpisodes', str(count['unwatched']))

				if 'total_seasons' in meta: item.setProperty('TotalSeasons', str(meta.get('total_seasons')))

				item.setArt(art)
				item.setProperty('IsPlayable', 'false')
				if is_widget:
					item.setProperty('isVenom_widget', 'true')
				item.setInfo(type='video', infoLabels=control.metadataClean(meta))
				item.addContextMenuItems(cm)
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				log_utils.error()

		try: control.property(syshandle, 'showplot', items[0]['plot'])
		except: pass

		control.content(syshandle, 'seasons')
		control.directory(syshandle, cacheToDisc=True)
		views.setView('seasons', {'skin.estuary': 55, 'skin.confluence': 500})