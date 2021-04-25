# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

try: import AddonSignals
except: pass
from hashlib import md5
from json import dumps as jsdumps, loads as jsloads
from sys import argv, exit as sysexit
try: from sqlite3 import dbapi2 as database
except ImportError: from pysqlite2 import dbapi2 as database
import xbmc
from resources.lib.database import metacache
from resources.lib.modules import control
from resources.lib.modules import cleantitle
from resources.lib.modules import log_utils
from resources.lib.modules import playcount
from resources.lib.modules import py_tools
from resources.lib.modules import trakt
LOGNOTICE = 2 if control.getKodiVersion() < 19 else 1 # (2 in 18, deprecated in 19 use LOGINFO(1)) = 2 if control.getKodiVersion() < 19 else 1 # (2 in 18, deprecated in 19 use LOGINFO(1))


class Player(xbmc.Player):
	def __init__(self):
		xbmc.Player.__init__(self)
		self.play_next_triggered = False
		self.media_type = None
		self.offset = '0'
		self.media_length = 0
		self.current_time = 0
		self.meta = {}
		self.playback_started = False
		self.scrobbled = False
		self.playback_resumed = False
		self.av_started = False


	def play_source(self, title, year, season, episode, imdb, tmdb, tvdb, url, meta, select=None):
		try:
			if not url: raise Exception
			self.media_type = 'movie' if season is None or episode is None else 'episode'
			self.title = title
			self.year = str(year)
			if self.media_type == 'movie':
				self.name = '%s (%s)' % (title, self.year)
				self.season = None
				self.episode = None
			elif self.media_type == 'episode':
				self.name = '%s S%02dE%02d' % (title, int(season), int(episode))
				self.season = '%01d' % int(season)
				self.episode = '%01d' % int(episode)

			self.DBID = None
			self.imdb = imdb if imdb is not None else ''
			self.tmdb = tmdb if tmdb is not None else ''
			self.tvdb = tvdb if tvdb is not None else ''
			self.ids = {'imdb': self.imdb, 'tmdb': self.tmdb, 'tvdb': self.tvdb}

## - compare meta received to database and use largest(eventually switch to a request to fetch missing db meta for item)
			self.imdb_user = control.setting('imdb.user').replace('ur', '')
			self.tmdb_key = control.setting('tmdb.api.key')
			if not self.tmdb_key: self.tmdb_key = '3320855e65a9758297fec4f7c9717698'
			self.tvdb_key = control.setting('tvdb.api.key')
			if self.media_type == 'episode': self.user = str(self.imdb_user) + str(self.tvdb_key)
			else: self.user = str(self.tmdb_key)
			self.lang = control.apiLanguage()['tvdb']
			meta1 = meta
			meta2 = metacache.fetch([{'imdb': self.imdb, 'tmdb': self.tmdb, 'tvdb': self.tvdb}], self.lang, self.user)[0]
			if meta2 != self.ids: meta2 = dict((k, v) for k, v in control.iteritems(meta2) if v is not None and v != '')
			if meta1 is not None:
				try:
					if len(meta2) > len(meta1):
						meta2.update(meta1)
						meta = meta2
					else: meta = meta1
				except: log_utils.error()
			else: meta = meta2 if meta2 != self.ids else meta1
##################
			self.meta = meta
			poster, thumb, season_poster, fanart, banner, clearart, clearlogo, discart, meta = self.getMeta(meta)
			runtime = meta.get('duration') if meta else 0
			self.offset = Bookmarks().get(name=self.name, imdb=imdb, tmdb=tmdb, tvdb=tvdb, season=season, episode=episode, year=self.year, runtime=runtime)
			item = control.item(path=url)
			item.setUniqueIDs(self.ids)
			if control.setting('disable.player.art') == 'true':
				remove_keys = ('clearart', 'clearlogo', 'discart')
				for k in remove_keys: meta.pop(k, None)
			if self.media_type == 'episode':
				if control.setting('disable.player.art') == 'true':
					item.setArt({'thumb': thumb, 'tvshow.poster': season_poster, 'season.poster': season_poster, 'tvshow.fanart': fanart})
				else:
					item.setArt({'tvshow.clearart': clearart, 'tvshow.clearlogo': clearlogo, 'tvshow.discart': discart, 'thumb': thumb, 'tvshow.poster': season_poster, 'season.poster': season_poster, 'tvshow.fanart': fanart})
			else:
				if control.setting('disable.player.art') == 'true': item.setArt({'thumb': thumb, 'poster': poster, 'fanart': fanart})
				else: item.setArt({'clearart': clearart, 'clearlogo': clearlogo, 'discart': discart, 'thumb': thumb, 'poster': poster, 'fanart': fanart})

			if 'castandart' in meta: item.setCast(meta.get('castandart', ''))
			item.setInfo(type='video', infoLabels=control.metadataClean(meta))
			if 'plugin' not in control.infoLabel('Container.PluginName') or select != '1':
				control.busy()
				control.resolve(int(argv[1]), True, item)
			elif select == '1':
				control.busy()
				control.player.play(url, item)
			control.homeWindow.setProperty('script.trakt.ids', jsdumps(self.ids))
			self.keepAlive()
			control.homeWindow.clearProperty('script.trakt.ids')
		except:
			log_utils.error()
			return control.cancelPlayback()


	def getMeta(self, meta):
		try:
			if not meta: raise Exception()
			poster = meta.get('poster3') or meta.get('poster2') or meta.get('poster') #poster2 and poster3 may not be passed anymore
			thumb = meta.get('thumb')
			thumb = thumb or poster or control.addonThumb()
			season_poster = meta.get('season_poster') or poster
			fanart = meta.get('fanart')
			banner = meta.get('banner')
			clearart = meta.get('clearart')
			clearlogo = meta.get('clearlogo')
			discart = meta.get('discart')
			if 'mediatype' not in meta:
				meta.update({'mediatype': 'episode' if self.episode else 'movie'})
				if self.episode:
					meta.update({'season': self.season})
					meta.update({'episode': self.episode})
					meta.update({'tvshowtitle': self.title})
			return (poster, thumb, season_poster, fanart, banner, clearart, clearlogo, discart, meta)
		except:
			log_utils.error()

		try:
			if self.media_type != 'movie': raise Exception()
			meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["title", "originaltitle", "year", "genre", "studio", "country", "runtime", "rating", "votes", "mpaa", "director", "writer", "plot", "plotoutline", "tagline", "thumbnail", "file"]}, "id": 1}' % (self.year, str(int(self.year) + 1), str(int(self.year) - 1)))
			meta = py_tools.ensure_text(meta, errors='ignore')
			meta = jsloads(meta)['result']['movies']
			t = cleantitle.get(self.title)
			meta = [i for i in meta if self.year == str(i['year']) and (t == cleantitle.get(i['title']) or t == cleantitle.get(i['originaltitle']))][0]
			if 'mediatype' not in meta:
				meta.update({'mediatype': 'movie'})
			if 'duration' not in meta:
				meta.update({'duration': meta.get('runtime') / 60}) # this doesn't make sense

			for k, v in control.iteritems(meta):
				if type(v) == list:
					try: meta[k] = str(' / '.join([i for i in v]))
					except: meta[k] = ''
				else:
					try: meta[k] = str(v)
					except: meta[k] = str(v)

			if 'plugin' not in control.infoLabel('Container.PluginName'):
				self.DBID = meta.get('movieid')
			poster = thumb = meta.get('thumbnail')
			return (poster, thumb, '', '', '', '', '', '', meta)
		except:
			log_utils.error()

		try:
			if self.media_type != 'episode': raise Exception()
			meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["title", "year", "thumbnail", "file"]}, "id": 1}' % (self.year, str(int(self.year)+1), str(int(self.year)-1)))
			meta = py_tools.ensure_text(meta, errors='ignore')
			meta = jsloads(meta)['result']['tvshows']
			t = cleantitle.get(self.title)
			meta = [i for i in meta if self.year == str(i['year']) and t == cleantitle.get(i['title'])][0]
			tvshowid = meta['tvshowid']
			poster = meta['thumbnail']
			meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params":{ "tvshowid": %d, "filter":{"and": [{"field": "season", "operator": "is", "value": "%s"}, {"field": "episode", "operator": "is", "value": "%s"}]}, "properties": ["title", "season", "episode", "showtitle", "firstaired", "runtime", "rating", "director", "writer", "plot", "thumbnail", "file"]}, "id": 1}' % (tvshowid, self.season, self.episode))
			meta = py_tools.ensure_text(meta, errors='ignore')
			meta = jsloads(meta)['result']['episodes'][0]
			if 'mediatype' not in meta:
				meta.update({'mediatype': 'episode'})
			if 'duration' not in meta:
				meta.update({'duration': meta.get('runtime') / 60}) # this doesn't make sense

			for k, v in control.iteritems(meta):
				if type(v) == list:
					try: meta[k] = str(' / '.join([i for i in v]))
					except: meta[k] = ''
				else:
					try: meta[k] = str(v)
					except: meta[k] = str(v)

			if 'plugin' not in control.infoLabel('Container.PluginName'):
				self.DBID = meta.get('episodeid')
			thumb = meta['thumbnail']
			return (poster, thumb, '', '', '', '', '', '', meta)
		except:
			log_utils.error()
			poster, thumb, season_poster, fanart, banner, clearart, clearlogo, discart, meta = '', '', '', '', '', '', '', '', {'title': self.name}
			return (poster, thumb, season_poster, fanart, banner, clearart, clearlogo, discart, meta)


	def getWatchedPercent(self):
		if self.isPlayback():
			try:
				position = self.getTime()
				if position != 0: self.current_time = position
				total_length = self.getTotalTime()
				if total_length != 0: self.media_length = total_length
			except: pass
		current_position = self.current_time
		total_length = self.media_length
		watched_percent = 0
		if int(total_length) != 0:
			try:
				watched_percent = float(current_position) / float(total_length) * 100
				if watched_percent > 100: watched_percent = 100
			except:
				log_utils.error()
		return watched_percent


	def keepAlive(self):
		pname = '%s.player.overlay' % control.addonInfo('id')
		control.homeWindow.clearProperty(pname)

		if self.media_type == 'movie':
			overlay = playcount.getMovieOverlay(playcount.getMovieIndicators(), self.imdb)
		elif self.media_type == 'episode':
			overlay = playcount.getEpisodeOverlay(playcount.getTVShowIndicators(), self.imdb, self.tvdb, self.season, self.episode)
		else: overlay = '4'


		for i in range(0, 240):
			if self.isPlayback():
				control.closeAll()
				break
			xbmc.sleep(1000)

		while self.isPlayingVideo():
			try:
				if not self.playback_started:
					xbmc.sleep(1000)
					continue
				if not self.playback_started: self.start_playback()

				try:
					self.current_time = self.getTime()
					self.media_length = self.getTotalTime()
				except: pass

				watcher = (self.getWatchedPercent() >= 80)
				property = control.homeWindow.getProperty(pname)
				if self.media_type == 'movie':
					try:
						if watcher and property != '5':
							control.homeWindow.setProperty(pname, '5')
							playcount.markMovieDuringPlayback(self.imdb, '5')
						# elif watcher is False and property != '4': # removes any previousely watched indicator, NO
							# control.homeWindow.setProperty(pname, '4')
							# playcount.markMovieDuringPlayback(self.imdb, '4')
					except: continue
					xbmc.sleep(2000)

				elif self.media_type == 'episode':
					try:
						if watcher and property != '5':
							control.homeWindow.setProperty(pname, '5')
							playcount.markEpisodeDuringPlayback(self.imdb, self.tvdb, self.season, self.episode, '5')
						# elif watcher is False and property != '4':# removes any previousely watched indicator, NO
							# control.homeWindow.setProperty(pname, '4')
							# playcount.markEpisodeDuringPlayback(self.imdb, self.tvdb, self.season, self.episode, '4')
					except: continue
					xbmc.sleep(2000)
			except:
				log_utils.error()
				xbmc.sleep(1000)
				continue
		control.homeWindow.clearProperty(pname)
		# self.onPlayBackEnded()


	def start_playback(self):
		try:
			if self.playback_started: return
			if not self.isPlayback(): return
			self.playback_started = True
			self.current_time = self.getTime()
			self.media_length = self.getTotalTime()

			if self.media_type == 'episode' and control.setting('enable.upnext') == 'true':
				if int(control.playlist.getposition()) == -1:
					control.playlist.clear()
					return
				source_id = 'plugin.video.venom'
				return_id = 'plugin.video.venom_play_action'
				try:
					if int(control.playlist.getposition()) < (control.playlist.size() - 1):
						if self.media_type is None: return
						next_info = self.next_info()
						AddonSignals.sendSignal('upnext_data', next_info, source_id)
						AddonSignals.registerSlot('upnextprovider', return_id, self.signals_callback)
						# # Prescrape
						# from resources.lib.modules import sources
						# psources = sources.Sources().preScrape(title=next_info['next_episode']['title'], year=next_info['next_episode']['year'], imdb=next_info['next_episode']['tvshowimdb'], tvdb=next_info['next_episode']['tvshowid'], season=next_info['next_episode']['season'], episode=next_info['next_episode']['episode'], tvshowtitle=next_info['next_episode']['showtitle'], premiered=next_info['next_episode']['firstaired'])
				except:
					log_utils.error()
		except:
			log_utils.error()


	def libForPlayback(self):
		if self.DBID is None: return
		try:
			if self.media_type == 'movie':
				rpc = '{"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {"movieid": %s, "playcount": 1 }, "id": 1 }' % str(self.DBID)
			elif self.media_type == 'episode':
				rpc = '{"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid": %s, "playcount": 1 }, "id": 1 }' % str(self.DBID)
			control.jsonrpc(rpc)
		except:
			log_utils.error()


	def isPlayback(self):
		# Kodi often starts playback where isPlaying() is true and isPlayingVideo() is false, since the video loading is still in progress, whereas the play is already started.
		return self.isPlaying() and self.isPlayingVideo() and self.getTime() >= 0


	def onPlayBackSeek(self, time, seekOffset):
		seekOffset /= 1000


	def onAVStarted(self):
		for i in range(0, 500):
			if self.isPlayback():
				self.av_started = True
				break
			else: control.sleep(1000)
		if self.offset != '0' and self.playback_resumed is False:
			self.seekTime(float(self.offset))
			self.playback_resumed = True
		if control.setting('subtitles') == 'true':
			Subtitles().get(self.name, self.imdb, self.season, self.episode)
		self.start_playback()
		xbmc.log('[ plugin.video.venom ] onAVStarted callback', LOGNOTICE)


	def onPlayBackStarted(self):
		control.sleep(5000)
		if self.av_started: return
		for i in range(0, 500):
			if self.isPlayback(): break
			else: control.sleep(1000)
		if self.offset != '0' and self.playback_resumed is False:
			self.seekTime(float(self.offset))
			self.playback_resumed = True
		if control.setting('subtitles') == 'true':
			Subtitles().get(self.name, self.imdb, self.season, self.episode)
		self.start_playback()
		xbmc.log('[ plugin.video.venom ] onPlayBackStarted callback', LOGNOTICE)


	def onPlayBackStopped(self):
		if self.media_length == 0: return
		try:
			Bookmarks().reset(self.current_time, self.media_length, self.name, self.year)
			if control.setting('trakt.scrobble') == 'true':
				Bookmarks().set_scrobble(self.current_time, self.media_length, self.media_type, self.imdb, self.tmdb, self.tvdb, self.season, self.episode)
			if (self.current_time / self.media_length) > .85:
				self.libForPlayback()
		except:
			log_utils.error()
		# if control.setting('crefresh') == 'true':
			# control.refresh()
			# control.sleep(500)
		# control.playlist.clear()
		control.trigger_widget_refresh()
		xbmc.log('[ plugin.video.venom ] onPlayBackStopped callback', LOGNOTICE)


	def onPlayBackEnded(self):
		Bookmarks().reset(self.current_time, self.media_length, self.name, self.year)
		trakt.scrobbleReset(imdb=self.imdb, tvdb=self.tvdb, season=self.season, episode=self.episode, refresh=False)
		self.libForPlayback()
		# if control.setting('crefresh') == 'true':
			# control.refresh()
			# control.sleep(500)
		control.trigger_widget_refresh()
		xbmc.log('[ plugin.video.venom ] onPlayBackEnded callback', LOGNOTICE)


	def onPlayBackError(self):
		Bookmarks().reset(self.current_time, self.media_length, self.name, self.year)
		log_utils.error()
		sysexit(1)
		xbmc.log('[ plugin.video.venom ] onPlayBackError callback', LOGNOTICE)


	def signals_callback(self, data):
		try:
			log_utils.log('self.play_next_triggered = %s' % self.play_next_triggered)
			log_utils.log('data = %s' % data)

			if not self.play_next_triggered:
				if not self.scrobbled:
					try:
						self.onPlayBackEnded()
						self.scrobbled = True
					except: pass
				self.play_next_triggered = True
				# Using a seek here as playnext causes Kodi gui to wig out. So we seek instead so it looks more graceful
				log_utils.log('forced AddonSignals seek')
				self.seekTime(self.media_length)
		except:
			log_utils.error()


	def next_info(self):
		current_info = self.meta
		current_episode = {}
		current_episode["episodeid"] = current_info.get('tmdb_epID', '')
		current_episode["tvshowid"] = current_info.get('tvdb', '')
		current_episode["title"] = current_info.get('title', '')
		current_episode["art"] = {}
		current_episode["art"]["thumb"] = current_info.get('thumb', '')
		current_episode["art"]["tvshow.clearart"] = current_info.get('clearart', '')
		current_episode["art"]["tvshow.clearlogo"] = current_info.get('clearlogo', '')
		current_episode["art"]["tvshow.fanart"] = current_info.get('fanart', '')
		current_episode["art"]["tvshow.landscape"] = current_info.get('fanart', '')
		current_episode["art"]["tvshow.poster"] = current_info.get('poster', '')
		current_episode["season"] = current_info.get('season', '')
		current_episode["episode"] = current_info.get('episode', '')
		current_episode["showtitle"] = current_info.get('tvshowtitle', '')
		current_episode["plot"] = current_info.get('plot', '')
		current_episode["playcount"] = current_info.get('playcount', '')
		current_episode["rating"] = current_info.get('rating', '')
		current_episode["firstaired"] = current_info.get('premiered', '')
		current_episode["runtime"] = current_info.get('duration', '')
		# log_utils.log('current_episode = %s' % current_episode, __name__, log_utils.LOGDEBUG)

		current_position = control.playlist.getposition()
		next_url = control.playlist[current_position + 1].getPath()

		try: # Py2
			from urlparse import parse_qsl
		except ImportError: # Py3
			from urllib.parse import parse_qsl
		params = dict(parse_qsl(next_url.replace('?', '')))
		next_info = jsloads(params.get('meta'))

		next_episode = {}
		next_episode["episodeid"] = next_info.get('tmdb_epID', '')
		next_episode["tvshowid"] = next_info.get('tvdb', '')
		next_episode["title"] = next_info.get('title', '')
		next_episode["art"] = {}
		next_episode["art"]["thumb"] = next_info.get('thumb', '')
		next_episode["art"]["tvshow.clearart"] = next_info.get('clearart', '')
		next_episode["art"]["tvshow.clearlogo"] = next_info.get('clearlogo', '')
		next_episode["art"]["tvshow.fanart"] = next_info.get('fanart', '')
		next_episode["art"]["tvshow.landscape"] = next_info.get('fanart', '')
		next_episode["art"]["tvshow.poster"] = next_info.get('poster', '')
		next_episode["season"] = next_info.get('season', '')
		next_episode["episode"] = next_info.get('episode', '')
		next_episode["showtitle"] = next_info.get('tvshowtitle', '')
		next_episode["plot"] = next_info.get('plot', '')
		next_episode["playcount"] = next_info.get('playcount', '')
		next_episode["rating"] = next_info.get('rating', '')
		next_episode["firstaired"] = next_info.get('premiered', '')
		next_episode["runtime"] = next_info.get('duration', '')

		play_info = {}
		play_info["item_id"] = next_info.get('tmdb_epID', '')

		next_info = {
			"current_episode": current_episode,
			"next_episode": next_episode,
			"play_info": play_info,
			"notification_time": int(control.setting('upnext.time'))
		}
		return next_info


class Subtitles:
	def get(self, name, imdb, season, episode):
		import gzip, codecs
		try: from cStringIO import StringIO
		except ImportError: from io import BytesIO as StringIO
		import xmlrpclib, re, base64
		try:
			langDict = {'Afrikaans': 'afr', 'Albanian': 'alb', 'Arabic': 'ara', 'Armenian': 'arm', 'Basque': 'baq', 'Bengali': 'ben', 'Bosnian': 'bos', 'Breton': 'bre', 'Bulgarian': 'bul', 'Burmese': 'bur', 'Catalan': 'cat', 'Chinese': 'chi', 'Croatian': 'hrv', 'Czech': 'cze', 'Danish': 'dan', 'Dutch': 'dut', 'English': 'eng', 'Esperanto': 'epo', 'Estonian': 'est', 'Finnish': 'fin', 'French': 'fre', 'Galician': 'glg', 'Georgian': 'geo', 'German': 'ger', 'Greek': 'ell', 'Hebrew': 'heb', 'Hindi': 'hin', 'Hungarian': 'hun', 'Icelandic': 'ice', 'Indonesian': 'ind', 'Italian': 'ita', 'Japanese': 'jpn', 'Kazakh': 'kaz', 'Khmer': 'khm', 'Korean': 'kor', 'Latvian': 'lav', 'Lithuanian': 'lit', 'Luxembourgish': 'ltz', 'Macedonian': 'mac', 'Malay': 'may', 'Malayalam': 'mal', 'Manipuri': 'mni', 'Mongolian': 'mon', 'Montenegrin': 'mne', 'Norwegian': 'nor', 'Occitan': 'oci', 'Persian': 'per', 'Polish': 'pol', 'Portuguese': 'por,pob', 'Portuguese(Brazil)': 'pob,por', 'Romanian': 'rum', 'Russian': 'rus', 'Serbian': 'scc', 'Sinhalese': 'sin', 'Slovak': 'slo', 'Slovenian': 'slv', 'Spanish': 'spa', 'Swahili': 'swa', 'Swedish': 'swe', 'Syriac': 'syr', 'Tagalog': 'tgl', 'Tamil': 'tam', 'Telugu': 'tel', 'Thai': 'tha', 'Turkish': 'tur', 'Ukrainian': 'ukr', 'Urdu': 'urd'}
			codePageDict = {'ara': 'cp1256', 'ar': 'cp1256', 'ell': 'cp1253', 'el': 'cp1253', 'heb': 'cp1255', 'he': 'cp1255', 'tur': 'cp1254', 'tr': 'cp1254', 'rus': 'cp1251', 'ru': 'cp1251'}
			quality = ['bluray', 'hdrip', 'brrip', 'bdrip', 'dvdrip', 'webrip', 'hdtv']
			langs = []
			try:
				try: langs = langDict[control.setting('subtitles.lang.1')].split(',')
				except: langs.append(langDict[control.setting('subtitles.lang.1')])
			except: pass

			try:
				try: langs = langs + langDict[control.setting('subtitles.lang.2')].split(',')
				except: langs.append(langDict[control.setting('subtitles.lang.2')])
			except: pass

			try: subLang = xbmc.Player().getSubtitles()
			except: subLang = ''
			if subLang == langs[0]: raise Exception()

			server = xmlrpclib.Server('https://api.opensubtitles.org/xml-rpc', verbose=0)
			token = server.LogIn('', '', 'en', 'XBMC_Subtitles_v1')
			token = token['token']
			sublanguageid = ','.join(langs)
			imdbid = re.sub(r'[^0-9]', '', imdb)

			if not (season is None or episode is None):
				result = server.SearchSubtitles(token, [{'sublanguageid': sublanguageid, 'imdbid': imdbid, 'season': season, 'episode': episode}])['data']
				fmt = ['hdtv']
			else:
				result = server.SearchSubtitles(token, [{'sublanguageid': sublanguageid, 'imdbid': imdbid}])['data']
				try: vidPath = xbmc.Player().getPlayingFile()
				except: vidPath = ''
				fmt = re.split(r'\.|\(|\)|\[|\]|\s|\-', vidPath)
				fmt = [i.lower() for i in fmt]
				fmt = [i for i in fmt if i in quality]

			filter = []
			result = [i for i in result if i['SubSumCD'] == '1']
			for lang in langs:
				filter += [i for i in result if i['SubLanguageID'] == lang and any(x in i['MovieReleaseName'].lower() for x in fmt)]
				filter += [i for i in result if i['SubLanguageID'] == lang and any(x in i['MovieReleaseName'].lower() for x in quality)]
				filter += [i for i in result if i['SubLanguageID'] == lang]

			try: lang = xbmc.convertLanguage(filter[0]['SubLanguageID'], xbmc.ISO_639_1)
			except: lang = filter[0]['SubLanguageID']

			content = [filter[0]['IDSubtitleFile'],]
			content = server.DownloadSubtitles(token, content)
			content = base64.b64decode(content['data'][0]['data'])
			content = gzip.GzipFile(fileobj=StringIO(content)).read()

			subtitle = control.transPath('special://temp/')
			subtitle = control.joinPath(subtitle, 'TemporarySubs.%s.srt' % lang)

			codepage = codePageDict.get(lang, '')
			if codepage and control.setting('subtitles.utf') == 'true':
				try:
					content_encoded = codecs.decode(content, codepage) # check for kodi 19?
					content = codecs.encode(content_encoded, 'utf-8') # check for kodi 19?
				except: pass

			file = control.openFile(subtitle, 'w')
			file.write(str(content))
			file.close()
			xbmc.sleep(1000)
			xbmc.Player().setSubtitles(subtitle)
		except:
			log_utils.error()


class Bookmarks:
	def get(self, name, imdb=None, tmdb=None, tvdb=None, season=None, episode=None, year='0', runtime=None, ck=False):
		offset = '0'
		if not runtime or runtime == 'None': return offset # TMDB sometimes return None as string
		scrobbble = 'Local Bookmark'
		if control.setting('bookmarks') != 'true': return offset
		if control.setting('trakt.scrobble') == 'true' and control.setting('resume.source') == '1':
			try:
				scrobbble = 'Trakt Scrobble'
				from resources.lib.database import traktsync
				progress = float(traktsync.fetch_bookmarks(imdb, tmdb, tvdb, season, episode))
				offset = float(progress / 100) * int(float(runtime)) # runtime vs. media_length can differ resulting in 10-30sec difference using Trakt scrobble, meta providers report runtime in full minutes
				seekable = (2 <= progress <= 85)
				if not seekable: return '0'
			except:
				log_utils.error()
				return '0'
		else:
			try:
				dbcon = database.connect(control.bookmarksFile)
				dbcur = dbcon.cursor()
				dbcur.execute('''CREATE TABLE IF NOT EXISTS bookmark (idFile TEXT, timeInSeconds TEXT, Name TEXT, year TEXT, UNIQUE(idFile));''')
				if not year or year == 'None': return offset
				years = [str(year), str(int(year)+1), str(int(year)-1)]
				match = dbcur.execute('''SELECT * FROM bookmark WHERE Name="%s" AND year IN (%s)''' % (name, ','.join(i for i in years))).fetchone() # helps fix random cases where trakt and imdb, or tvdb, differ by a year for eps
			except:
				log_utils.error()
				return offset
			finally:
				dbcur.close() ; dbcon.close()
			if not match: return offset
			offset = str(match[1])

		if ck: return offset
		minutes, seconds = divmod(float(offset), 60)
		hours, minutes = divmod(minutes, 60)
		label = '%02d:%02d:%02d' % (hours, minutes, seconds)
		label = control.lang(32502) % label
		if control.setting('bookmarks.auto') == 'false':
			if control.yesnoDialog(label, scrobbble, '', str(name), control.lang(32503), control.lang(32501)): offset = '0'
		return offset


	def reset(self, current_time, media_length, name, year='0'):
		try:
			from resources.lib.database import cache
			cache.clear_local_bookmarks()
			if control.setting('bookmarks') != 'true' or media_length == 0 or current_time == 0: return
			timeInSeconds = str(current_time)

			seekable = (int(current_time) > 180 and (current_time / media_length) <= .85)
			idFile = md5()
			try: [idFile.update(str(i)) for i in name]
			except: [idFile.update(str(i).encode('utf-8')) for i in name]
			try: [idFile.update(str(i)) for i in year]
			except: [idFile.update(str(i).encode('utf-8')) for i in year]
			idFile = str(idFile.hexdigest())
			control.makeFile(control.dataPath)
			dbcon = database.connect(control.bookmarksFile)
			dbcur = dbcon.cursor()
			dbcur.execute('''CREATE TABLE IF NOT EXISTS bookmark (idFile TEXT, timeInSeconds TEXT, Name TEXT, year TEXT, UNIQUE(idFile));''')
			years = [str(year), str(int(year)+1), str(int(year)-1)]
			dbcur.execute('''DELETE FROM bookmark WHERE Name="%s" AND year IN (%s)''' % (name, ','.join(i for i in years))) #helps fix random cases where trakt and imdb, or tvdb, differ by a year for eps

			if seekable:
				dbcur.execute('''INSERT INTO bookmark Values (?, ?, ?, ?)''', (idFile, timeInSeconds, name, year))
				minutes, seconds = divmod(float(timeInSeconds), 60)
				hours, minutes = divmod(minutes, 60)
				label = ('%02d:%02d:%02d' % (hours, minutes, seconds))
				message = control.lang(32660)
				control.notification(title=name, message=message + '(' + label + ')')
			dbcur.connection.commit()
			try: dbcur.close ; dbcon.close()
			except: pass
		except:
			log_utils.error()


	def set_scrobble(self, current_time, media_length, media_type, imdb='', tmdb='', tvdb='', season='', episode=''):
		try:
			percent = float((current_time / media_length)) * 100
			seekable = (int(current_time) > 180 and (percent <= 85))
			if seekable:
				trakt.scrobbleMovie(imdb, tmdb, percent) if media_type == 'movie' else trakt.scrobbleEpisode(imdb, tmdb, tvdb, season, episode, percent)
			if percent > 85:
				trakt.scrobbleReset(imdb, tvdb, season, episode, refresh=False)
		except:
			log_utils.error()