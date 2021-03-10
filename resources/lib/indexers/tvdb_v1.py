# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from datetime import datetime, timedelta
import time
import re
import requests # seems faster than urlli2.urlopen
import zipfile
try: # Py2
	# from urllib2 import urlopen
	from urllib import quote_plus
	from cStringIO import StringIO
except ImportError: # Py3
	# from urllib.request import urlopen
	from urllib.parse import quote_plus
	from io import BytesIO as StringIO

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import py_tools


lang = control.apiLanguage()['tvdb']
api_key = control.setting('tvdb.api.key')

imdb_user = control.setting('imdb.user').replace('ur', '')
user = str(imdb_user) + str(api_key)

baseUrl = 'https://thetvdb.com'
info_link = '%s/api/%s/series/%s/%s.xml' % (baseUrl, api_key, '%s', '%s')
all_info_link = '%s/api/%s/series/%s/all/%s.xml' % (baseUrl, api_key, '%s', '%s')
zip_link = '%s/api/%s/series/%s/all/%s.zip' % (baseUrl, api_key, '%s', '%s')

by_imdb = '%s/api/GetSeriesByRemoteID.php?imdbid=%s' % (baseUrl, '%s')
by_seriesname = '%s/api/GetSeries.php?seriesname=%s' % (baseUrl, '%s')
imageUrl = '%s/banners/' % baseUrl
tvdb_poster = '%s/banners/_cache/' % baseUrl

date_time = (datetime.utcnow() - timedelta(hours=5))
today_date = (date_time).strftime('%Y-%m-%d')

showunaired = control.setting('showunaired') or 'true'


def getZip(tvdb, art_xml=None, actors_xml=None):
	url = zip_link % (tvdb, lang)
	try:
		# data = urlopen(url, timeout=30).read()
		data = requests.get(url, timeout=30, verify=True).content # test .content vs. .text
		zip = zipfile.ZipFile(StringIO(data))
		result = py_tools.six_decode(zip.read('%s.xml' % lang))
		if not art_xml and not actors_xml:
			zip.close()
			return result
		elif art_xml and not actors_xml:
			artwork = py_tools.six_decode(zip.read('banners.xml'))
			zip.close()
			return (result, artwork)
		elif actors_xml and not art_xml:
			actors = py_tools.six_decode(zip.read('actors.xml'))
			zip.close()
			return (result, actors)
		else:
			artwork = py_tools.six_decode(zip.read('banners.xml'))
			actors = py_tools.six_decode(zip.read('actors.xml'))
			zip.close()
			return (result, artwork, actors)
	except:
		log_utils.error()
		return None


def parseAll(tvdb, limit):
	try:
		dupe = client.parseDOM(result, 'SeriesName')[0]
		dupe = re.compile(r'[***]Duplicate (\d*)[***]').findall(dupe)
		if len(dupe) > 0:
			tvdb = str(dupe[0])
			result, artwork, actors = cache.get(getZip, 96, tvdb, True, True)

		# if lang != 'en':
			# url = zip_link % (tvdb, lang)
			# # data = urlopen(url, timeout=30).read()
			# data = requests.get(url, timeout=30).content # test .content vs. .text
			# zip = zipfile.ZipFile(StringIO(data))
			# result2 = zip.read('%s.xml' % lang)
			# zip.close()
		# else: result2 = result

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
		counts = seasonCountParse(seasons = seasons, episodes = episodes)
		# locals = [i for i in result2 if '<EpisodeNumber>' in i]

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
				if showunaired != 'true': continue
				pass
			elif int(re.sub(r'[^0-9]', '', str(premiered))) > int(re.sub(r'[^0-9]', '', str(self.today_date))):
				unaired = 'true'
				if showunaired != 'true': continu

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

			list.append({'season': season, 'tvshowtitle': tvshowtitle, 'label': label, 'year': year, 'premiered': premiered,
							'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes,
							'mpaa': mpaa, 'castandart': castandart, 'plot': plot, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb,
							'tvshowid': imdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb,
							'unaired': unaired, 'seasoncount': seasoncount, 'total_seasons': total_seasons})
			list = sorted(self.list, key=lambda k: int(k['season'])) # fix for TVDb new sort by ID
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
				if showunaired != 'true': continue
				pass
			elif int(re.sub(r'[^0-9]', '', str(premiered))) > int(re.sub(r'[^0-9]', '', str(self.today_date))):
				unaired = 'true'
				if showunaired != 'true': continue

			season = client.parseDOM(item, 'SeasonNumber')[0]
			season = '%01d' % int(season)
			episode = client.parseDOM(item, 'EpisodeNumber')[0]
			episode = re.sub(r'[^0-9]', '', '%01d' % int(episode))

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


			list.append({'title': title, 'label': label, 'season': season, 'episode': episode, 'tvshowtitle': tvshowtitle, 'year': year,
								'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating,
								'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'castandart': castandart, 'plot': episodeplot,
								'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb,
								'season_poster': season_poster, 'unaired': unaired, 'seasoncount': seasoncount, 'counts': counts,
								'total_seasons': total_seasons, 'is_airing': is_airing, 'episodeIDS': episodeIDS})
			list = sorted(list, key=lambda k: (int(k['season']), int(k['episode']))) # fix for TVDb new sort by ID
			# meta = {}
			# meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'lang': lang, 'user': user, 'item': item}
			# list.append(item)
			# metacache.insert(meta)
		except:
			log_utils.error()
	return list


def parseSeasonPoster(artwork, season):
	try:
		season_poster = [x for x in artwork if client.parseDOM(x, 'Season')[0] == season]
		season_poster = client.parseDOM(season_poster[0], 'BannerPath')[0]
		season_poster = imageUrl + season_poster or None
		season_poster = client.replaceHTMLCodes(season_poster)
		# season_poster = season_poster.encode('utf-8')
		return season_poster
	except:
		log_utils.error()
		return None


def getSeries_by_id(tvdb):
	url = info_link % (tvdb, lang)
	items = []

	try:
		item = client.request(url, timeout='10', error = True)
		if item is None: raise Exception()
		imdb = client.parseDOM(item, 'IMDB_ID')[0]

		title = client.replaceHTMLCodes(client.parseDOM(item, 'SeriesName')[0])
		title = py_tools.ensure_str(title)

		year = client.parseDOM(item, 'FirstAired')[0]
		year = re.compile(r'(\d{4})').findall(year)[0]
		premiered = client.parseDOM(item, 'FirstAired')[0]

		studio = client.parseDOM(item, 'Network')[0]

		genre = client.parseDOM(item, 'Genre')[0]
		genre = [x for x in genre.split('|') if x != '']
		genre = ' / '.join(genre)

		duration = client.parseDOM(item, 'Runtime')[0]
		rating = client.parseDOM(item, 'Rating')[0]
		votes = client.parseDOM(item, 'RatingCount')[0]
		mpaa = client.parseDOM(item, 'ContentRating')[0]

		plot = client.replaceHTMLCodes(client.parseDOM(item, 'Overview')[0])
		plot = py_tools.ensure_str(plot)

		status = client.parseDOM(item, 'Status')[0]
		if not status: status = 'Ended'

		poster = client.parseDOM(item, 'poster')[0]
		if poster and poster != '': poster = imageUrl + poster
		else: poster = '0'

		banner = client.parseDOM(item, 'banner')[0]
		if banner and banner != '': banner = imageUrl + banner
		else: banner = '0'

		fanart = client.parseDOM(item, 'fanart')[0]
		if fanart and fanart != '': fanart = imageUrl + fanart
		else: fanart = '0'

		items.append({'extended': True, 'title': title, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration,
					'rating': rating, 'votes': votes, 'mpaa': mpaa, 'castandart': castandart, 'plot': plot, 'status': status, 'poster': poster, 'poster2': '0', 'poster3': '0', 'banner': banner,
					'banner2': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0', 'landscape': fanart, 'metacache': False})
		# meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'lang': lang, 'user': user, 'item': item}
		return items
	except:
		log_utils.error()
		return None


def getBanners(tvdb):
	url = info_link % (tvdb, 'banners')
	try:
		artwork = client.request(url, timeout='10', error=True)
		if artwork is None: raise Exception()
		artwork = artwork.split('<Banner>')
		artwork = [i for i in artwork if '<Language>en</Language>' in i and '<BannerType>season</BannerType>' in i]
		artwork = [i for i in artwork if not 'seasonswide' in re.findall(r'<BannerPath>(.+?)</BannerPath>', i)[0]]
		return artwork
	except:
		log_utils.error()
		return None


# def parseBanners(artwork):


def getActors(tvdb):
	url = info_link % (tvdb, 'actors')
	try:
		actors = client.request(url, timeout='10', error=True)
		if actors is None: raise Exception()
		return actors
	except:
		log_utils.error()
		return None


def parseActors(actors):
	castandart = []
	try:
		if not actors: return castandart
		import xml.etree.ElementTree as ET
		tree = ET.ElementTree(ET.fromstring(actors))
		root = tree.getroot()
		for actor in root.iter('Actor'):
			person = [name.text for name in actor]
			image = person[1]
			name = py_tools.ensure_str(client.replaceHTMLCodes(person[2])) or ''
			role = py_tools.ensure_str(client.replaceHTMLCodes(person[3])) or ''
			try:
				castandart.append({'name': name, 'role': role, 'thumbnail': ((imageUrl + image) if image is not None else '0')})
			except: pass
			if len(castandart) == 150: break # cast seems to have a limit and a show like "Survivor" has 500+ actors and breaks
		return castandart
	except:
		log_utils.error()
		return []


def getSeries_ByIMDB(title, year, imdb):
	try:
		url = by_imdb % imdb
		result = client.request(url, timeout='10')
		# result = requests.get(url, timeout=10).content # test .content vs. .text
		# result = py_tools.six_decode(result)
		result = re.sub(r'[^\x00-\x7F]+', '', result)
		result = client.replaceHTMLCodes(result)
		result = client.parseDOM(result, 'Series')
		result = [(client.parseDOM(x, 'SeriesName'), client.parseDOM(x, 'FirstAired'), client.parseDOM(x, 'seriesid'), client.parseDOM(x, 'AliasNames')) for x in result]
		years = [str(year), str(int(year)+1), str(int(year)-1)]
		item = [(x[0], x[1], x[2], x[3]) for x in result if cleantitle.get(title) == cleantitle.get(str(x[0][0])) and any(y in str(x[1][0]) for y in years)]
		if item == []:
			item = [(x[0], x[1], x[2], x[3]) for x in result if cleantitle.get(title) == cleantitle.get(str(x[3][0]))]
		if item == []:
			item = [(x[0], x[1], x[2], x[3]) for x in result if cleantitle.get(title) == cleantitle.get(str(x[0][0]))]
		if item == []: return '0'
		tvdb = item[0][2]
		tvdb = tvdb[0] or '0'
		return tvdb
	except:
		log_utils.error()
	return '0'


def getSeries_ByName(title, year):
	try:
		url = by_seriesname % (quote_plus(title))
		result = client.request(url, timeout='10')
		# result = requests.get(url, timeout=10).content # test .content vs. .text
		# result = py_tools.six_decode(result)
		result = re.sub(r'[^\x00-\x7F]+', '', result)
		result = client.replaceHTMLCodes(result)
		result = client.parseDOM(result, 'Series')
		result = [(client.parseDOM(x, 'SeriesName'), client.parseDOM(x, 'FirstAired'), client.parseDOM(x, 'seriesid'), client.parseDOM(x, 'IMDB_ID'), client.parseDOM(x, 'AliasNames')) for x in result]
		years = [str(year), str(int(year)+1), str(int(year)-1)]
		item = [(x[0], x[1], x[2], x[3], x[4]) for x in result if cleantitle.get(title) == cleantitle.get(str(x[0][0])) and any(y in str(x[1][0]) for y in years)]
		if item == []:
			item = [(x[0], x[1], x[2], x[3], x[4]) for x in result if cleantitle.get(title) == cleantitle.get(str(x[4][0]))]
		if item == []:
			item = [(x[0], x[1], x[2], x[3], x[4]) for x in result if cleantitle.get(title) == cleantitle.get(str(x[0][0]))]
		if item == []: return None
		tvdb = item[0][2]
		tvdb = tvdb[0] or '0'
		imdb = item[0][3]
		imdb = imdb[0] or '0'
		return {'tvdb': tvdb, 'imdb': imdb}
	except:
		log_utils.error()


def get_is_airing(tvdb, season):
	url = all_info_link % (tvdb, lang)
	try:
		# result = client.request(url, timeout='10', as_bytes=True)
		result = client.request(url, timeout='10')
		result = result.split('<Episode>')
		episodes = [i for i in result if '<EpisodeNumber>' in i]
		if control.setting('tv.specials') == 'true':
			episodes = [i for i in episodes]
		else:
			episodes = [i for i in episodes if not '<SeasonNumber>0</SeasonNumber>' in i]
			episodes = [i for i in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in i]
		# season still airing check for pack scraping
		premiered_eps = [i for i in episodes if not '<FirstAired></FirstAired>' in i]
		unaired_eps = [i for i in premiered_eps if int(re.sub(r'[^0-9]', '', str(client.parseDOM(i, 'FirstAired')))) > int(re.sub(r'[^0-9]', '', str(today_date)))]
		if unaired_eps: still_airing = client.parseDOM(unaired_eps, 'SeasonNumber')[0]
		else: still_airing = None
		if still_airing:
			if int(still_airing) == int(season): is_airing = True
			else: is_airing = False
		else: is_airing = False
		return is_airing
	except:
		log_utils.error()


def get_counts(tvdb):
	url = all_info_link % (tvdb, lang)
	try:
		result = client.request(url, timeout='10')
		# result = requests.get(url, timeout=10).content # test .content vs. .text
		# result = py_tools.six_decode(result)
		result = result.split('<Episode>')
		episodes = [i for i in result if '<EpisodeNumber>' in i]
		if control.setting('tv.specials') == 'true':
			episodes = [i for i in episodes]
		else:
			episodes = [i for i in episodes if not '<SeasonNumber>0</SeasonNumber>' in i]
			episodes = [i for i in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in i]
		seasons = [i for i in episodes if '<EpisodeNumber>1</EpisodeNumber>' in i]
		counts = seasonCountParse(seasons=seasons, episodes=episodes)
		# log_utils.log('counts = %s' % str(counts), __name__, log_utils.LOGDEBUG)
		return counts
	except:
		log_utils.error()


def seasonCountParse(season = None, items = None, seasons = None, episodes = None):
	# Determine the number of episodes per season to estimate season pack episode sizes.
	index = season
	counts = {} # Do not use a list, since not all seasons are labeled by number. Eg: MythBusters
	if episodes is None:
		episodes = [i for i in items if '<EpisodeNumber>' in i]
		if control.setting('tv.specials') == 'true':
			episodes = [i for i in episodes]
		else:
			episodes = [i for i in episodes if not '<SeasonNumber>0</SeasonNumber>' in i]
			episodes = [i for i in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in i]
		seasons = [i for i in episodes if '<EpisodeNumber>1</EpisodeNumber>' in i]
	for s in seasons:
		season = client.parseDOM(s, 'SeasonNumber')[0]
		season = '%01d' % int(season)
		counts[season] = 0
	for e in episodes:
		try:
			season = client.parseDOM(e, 'SeasonNumber')[0]
			season = '%01d' % int(season)
			counts[season] += 1
		except: pass
	try:
		if index is None: return counts
		else: return counts[index]
	except: return None