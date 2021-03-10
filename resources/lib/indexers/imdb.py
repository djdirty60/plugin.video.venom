# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from datetime import datetime, timedelta
from json import loads as jsloads
import re
try: #Py2
	from urlparse import urlparse
except ImportError: #Py3
	from urllib.parse import urlparse
from resources.lib.modules import cache
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import metacache
from resources.lib.modules import py_tools
from resources.lib.modules import trakt


class movies:
	def __init__(self):
		self.count = 40
		self.list = []
		self.meta = []
		disable_fanarttv = control.setting('disable.fanarttv')
		# self.date_time = (datetime.utcnow() - timedelta(hours=5))
		self.date_time = datetime.utcnow()
		self.lang = control.apiLanguage()['trakt']

		self.imdb_user = control.setting('imdb.user').replace('ur', '')
		self.tmdb_key = control.setting('tmdb.api.key')
		if not self.tmdb_key:
			self.tmdb_key = '3320855e65a9758297fec4f7c9717698'
		self.user = str(self.imdb_user) + str(self.tmdb_key)

		self.tmdb_poster = 'https://image.tmdb.org/t/p/w500'
		self.tmdb_fanart = 'https://image.tmdb.org/t/p/w1280'
		self.tmdb_info_link = 'https://api.themoviedb.org/3/movie/%s?api_key=%s&language=%s&append_to_response=credits,release_dates,external_ids' % ('%s', self.tmdb_key, self.lang)
																	# other	"append_to_response"options		alternative_titles,videos,images
		self.tmdb_art_link = 'https://api.themoviedb.org/3/movie/%s/images?api_key=%s&include_image_language=en,%s,null' % ('%s', self.tmdb_key, self.lang)


	def imdb_list(self, url, isRatinglink=False):
		list = []
		try:
			for i in re.findall(r'date\[(\d+)\]', url):
				url = url.replace('date[%s]' % i, (self.date_time - timedelta(days=int(i))).strftime('%Y-%m-%d'))
			def imdb_watchlist_id(url):
				return client.parseDOM(client.request(url), 'meta', ret='content', attrs = {'property': 'pageId'})[0]
				# return client.parseDOM(client.request(url).decode('iso-8859-1').encode('utf-8'), 'meta', ret='content', attrs = {'property': 'pageId'})[0]
			if url == self.imdbwatchlist_link:
				url = cache.get(imdb_watchlist_id, 8640, url)
				url = self.imdblist_link % url
			result = client.request(url)
			result = result.replace('\n', ' ')
			# result = result.decode('iso-8859-1').encode('utf-8')
			items = client.parseDOM(result, 'div', attrs = {'class': '.+? lister-item'}) + client.parseDOM(result, 'div', attrs = {'class': 'lister-item .+?'})
			items += client.parseDOM(result, 'div', attrs = {'class': 'list_item.+?'})
		except:
			log_utils.error()
			return

		next = ''
		try:
			# HTML syntax error, " directly followed by attribute name. Insert space in between. parseDOM can otherwise not handle it.
			result = result.replace('"class="lister-page-next', '" class="lister-page-next')
			# next = client.parseDOM(result, 'a', ret='href', attrs = {'class': '.+?ister-page-nex.+?'})
			next = client.parseDOM(result, 'a', ret='href', attrs = {'class': 'lister-page-next.+?'})
			if len(next) == 0:
				next = client.parseDOM(result, 'div', attrs = {'class': 'pagination'})[0]
				next = zip(client.parseDOM(next, 'a', ret='href'), client.parseDOM(next, 'a'))
				next = [i[0] for i in next if 'Next' in i[1]]
			next = url.replace(urlparse(url).query, urlparse(next[0]).query)
			next = client.replaceHTMLCodes(next)
		except:
			next = ''

		for item in items:
			try:
				title = client.replaceHTMLCodes(client.parseDOM(item, 'a')[1])
				title = py_tools.ensure_str(title)

				year = client.parseDOM(item, 'span', attrs = {'class': 'lister-item-year.+?'})
				try: year = re.findall(r'(\d{4})', year[0])[0]
				except: continue
				if int(year) > int((self.date_time).strftime('%Y')): continue

				try: show = '–'.decode('utf-8') in str(year).decode('utf-8') or '-'.decode('utf-8') in str(year).decode('utf-8') # check with Matrix
				except: show = False
				if show or 'Episode:' in item: raise Exception() # Some lists contain TV shows.

				try: genre = client.parseDOM(item, 'span', attrs = {'class': 'genre'})[0]
				except: genre = '0'
				genre = ' / '.join([i.strip() for i in genre.split(',')])
				genre = client.replaceHTMLCodes(genre)

				try: mpaa = client.parseDOM(item, 'span', attrs = {'class': 'certificate'})[0]
				except: mpaa = '0'
				if isRatinglink and 'Short' not in genre:
					if mpaa in ['TV-Y', 'TV-Y7', 'TV-G', 'TV-PG', 'TV-13', 'TV-14', 'TV-MA']:
						raise Exception()
				if mpaa == '' or mpaa == 'NOT_RATED': mpaa = '0'
				mpaa = mpaa.replace('_', '-')
				mpaa = client.replaceHTMLCodes(mpaa)

				imdb = client.parseDOM(item, 'a', ret='href')[0]
				imdb = re.findall(r'(tt\d*)', imdb)[0]

				try: # parseDOM cannot handle elements without a closing tag.
					from bs4 import BeautifulSoup
					html = BeautifulSoup(item, "html.parser")
					poster = html.find_all('img')[0]['loadlate']
				except: poster = '0'

				if '/nopicture/' in poster: poster = '0'
				poster = re.sub(r'(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.', '_SX500.', poster)
				poster = client.replaceHTMLCodes(poster)

				try: duration = re.findall(r'(\d+?) min(?:s|)', item)[-1]
				except: duration = '0'

				rating = '0'
				try: rating = client.parseDOM(item, 'span', attrs = {'class': 'rating-rating'})[0]
				except:
					try: rating = client.parseDOM(rating, 'span', attrs = {'class': 'value'})[0]
					except:
						try: rating = client.parseDOM(item, 'div', ret='data-value', attrs = {'class': '.*?imdb-rating'})[0]
						except: pass
				if rating == '' or rating == '-': rating = '0'
				if rating == '0':
					try:
						rating = client.parseDOM(item, 'span', attrs = {'class': 'ipl-rating-star__rating'})[0]
						if rating == '' or rating == '-': rating = '0'
					except: pass
				rating = client.replaceHTMLCodes(rating)

				votes = '0'
				try: votes = client.parseDOM(item, 'span', attrs = {'name': 'nv'})[0]
				except:
					try: votes = client.parseDOM(item, 'div', ret='title', attrs = {'class': '.*?rating-list'})[0]
					except:
						try: votes = re.findall(r'\((.+?) vote(?:s|)\)', votes)[0]
						except: pass
				votes = client.replaceHTMLCodes(votes)

				try: director = re.findall(r'Director(?:s|):(.+?)(?:\||</div>)', item)[0]
				except: director = '0'
				director = client.parseDOM(director, 'a')
				director = ' / '.join(director)
				director = client.replaceHTMLCodes(director) # check if this needs ensure_str()

				plot = '0'
				try: plot = client.parseDOM(item, 'p', attrs = {'class': 'text-muted'})[0]
				except:
					try: plot = client.parseDOM(item, 'div', attrs = {'class': 'item_description'})[0]
					except: pass
				plot = plot.rsplit('<span>', 1)[0].strip()
				plot = re.sub(r'<.+?>|</.+?>', '', plot)
				if plot == '': plot = '0'
				if plot == '0':
					try:
						plot = client.parseDOM(item, 'div', attrs = {'class': 'lister-item-content'})[0] # not sure on this, check html
						plot = re.sub(r'<p\s*class="">', '<p class="plot_">', plot)
						plot = client.parseDOM(plot, 'p', attrs = {'class': 'plot_'})[0]
						plot = re.sub(r'<.+?>|</.+?>', '', plot)
						if plot == '': plot = '0'
					except: pass
				plot = client.cleanHTML(plot)

				item = {}
				item = {'content': 'movie', 'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered,
						'studio': '0', 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa,
						'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'code': tmdb,
						'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': poster, 'poster2': '0', 'poster3': '0', 'banner': '0',
						'fanart': '0', 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0', 'landscape': '0',
						'metacache': False, 'next': next}
				meta = {}
				meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.tmdb_key, 'item': item}

				if disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = cache.get(fanarttv.get_movie_art, 168, imdb, tmdb)
					if extended_art:
						item.update(extended_art)
						meta.update(item)

				self.list.append(item)
				self.meta.append(meta)
				metacache.insert(self.meta)
			except:
				pass
		return self.list


	def imdb_person_list(self, url):
		list = []
		try:
			result = client.request(url)
			items = client.parseDOM(result, 'div', attrs = {'class': '.+?etail'})
		except:
			log_utils.error()
			return

		for item in items:
			try:
				name = client.parseDOM(item, 'img', ret='alt')[0]
				# name = name.encode('utf-8')
				url = client.parseDOM(item, 'a', ret='href')[0]
				url = re.findall(r'(nm\d*)', url, re.I)[0]
				url = self.person_link % url
				url = client.replaceHTMLCodes(url)
				image = client.parseDOM(item, 'img', ret='src')[0]
				image = re.sub(r'(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.', '_SX500.', image)
				image = client.replaceHTMLCodes(image)
				list.append({'name': name, 'url': url, 'image': image})
			except:
				log_utils.error()
		return list


	def imdb_user_list(self, url):
		list = []
		try:
			result = client.request(url) # test .content vs. .text
			items = client.parseDOM(result, 'li', attrs = {'class': 'ipl-zebra-list__item user-list'})
			# Gaia uses this but seems to break the user list
			# items = client.parseDOM(result, 'div', attrs = {'class': 'list_name'})
		except: pass

		for item in items:
			try:
				name = client.parseDOM(item, 'a')[0]
				name = client.replaceHTMLCodes(name)
				# name = name.encode('utf-8')
				url = client.parseDOM(item, 'a', ret='href')[0]
				url = url.split('/list/', 1)[-1].strip('/')
				# url = url.split('/list/', 1)[-1].replace('/', '')
				url = self.imdblist_link % url
				url = client.replaceHTMLCodes(url)
				# url = url.encode('utf-8')
				list.append({'name': name, 'url': url, 'context': url})
			except:
				pass
		list = sorted(self.list, key=lambda k: re.sub(r'(^the |^a |^an )', '', k['name'].lower()))
		return self.list


	def super_info(self, i):
		try:
			if self.list[i]['metacache']: 	return
			imdb = self.list[i]['imdb'] or '0'
			tmdb = self.list[i]['tmdb'] or '0'
			try:
				item = tmdb_indexer.Movies().get_details(tmdb, imdb)  # api claims int rq'd.  But imdb_id works for movies but not looking like it does for shows
				if not item and (tmdb == '0' and imdb != '0'):
					trakt_ids = trakt.IdLookup('imdb', imdb, 'movie')
					if trakt_ids:
						tmdb = str(trakt_ids.get('tmdb', '0'))
						if not tmdb or tmdb == 'None': tmdb = '0'
						else:
							item = tmdb_indexer.Movies().get_details(tmdb, '0')
				if not item:
					results = trakt.SearchMovie(title=quote_plus(self.list[i]['title']), year=self.list[i]['year'], fields='title', full=False)[0]
					if results:
						if tmdb == '0': tmdb = str(results.get('movie').get('ids').get('tmdb', '0'))
						if imdb == '0': imdb = str(results.get('movie').get('ids').get('imdb', '0'))
						item = tmdb_indexer.Movies().get_details(tmdb, imdb)
						if not item: return
					else: return
			except:
				log_utils.error()
				return

			title = py_tools.ensure_str(item.get('title'))
			originaltitle = title

#add these so sources module may not have to make a trakt api request
			# aliases = item.get('alternative_titles').get('titles')
			# log_utils.log('aliases = %s' % str(aliases), __name__, log_utils.LOGDEBUG)

			if imdb == '0' or imdb is None:
				imdb = item.get('imdb_id', '0')
				if not imdb or imdb == 'None': imdb = '0'
			if tmdb == '0' or tmdb is None:
				tmdb = str(item.get('id'))

			if 'year' not in self.list[i] or self.list[i]['year'] == '0':
				year = str(item.get('release_date')[:4])
			else: year = self.list[i]['year'] or '0'

			if 'premiered' not in self.list[i] or self.list[i]['premiered'] == '0': # imdb and tmdb difffer often
				premiered = item.get('release_date')
			else: premiered = self.list[i]['premiered']

			if premiered and year not in premiered: # hack fix for imdb vs. tmdb mismatch without a new request.
				premiered = premiered.replace(premiered[:4], year)

			if 'genre' not in self.list[i] or self.list[i]['genre'] == '0' or self.list[i]['genre'] == 'NA':
				genre = []
				for x in item['genres']:
					genre.append(x.get('name'))
				if genre == []: genre = 'NA'
			else: genre = self.list[i]['genre']

			if 'duration' not in self.list[i] or self.list[i]['duration'] == '0':
				duration = str(item.get('runtime', '0'))
			else: duration = self.list[i]['duration']

			if 'rating' not in self.list[i] or self.list[i]['rating'] == '0':
				rating = str(item.get('vote_average', '0'))
			else: rating = self.list[i]['rating']

			if 'votes' not in self.list[i] or self.list[i]['votes'] == '0':
				votes = str(format(int(item.get('vote_count', '0')),',d'))
			else: votes = self.list[i]['votes']

			if 'mpaa' not in self.list[i] or self.list[i]['mpaa'] == '0' or self.list[i]['mpaa'] == 'NR':
				mpaa = item['release_dates']['results']
				mpaa = [x for x in mpaa if x['iso_3166_1'] == 'US']
				try:
					mpaa = mpaa[0].get('release_dates')[-1].get('certification')
					if not mpaa:
						mpaa = mpaa[0].get('release_dates')[0].get('certification')
						if not mpaa:
							mpaa = mpaa[0].get('release_dates')[1].get('certification')
					mpaa = str(mpaa)
				except: mpaa = '0'
			else: mpaa = self.list[i]['mpaa']

			if 'plot' not in self.list[i] or self.list[i]['plot'] == '0': plot = item.get('overview')
			else: plot = self.list[i]['plot']
			plot = py_tools.ensure_str(plot)

			try:
				trailer = [x for x in item['videos']['results'] if x['site'] == 'YouTube' and x['type'] == 'Trailer'][0]['key']
				trailer = control.trailer % trailer
			except: trailer = ''

			castandart = []
			director = writer = '0'
			poster3 = fanart3 = '0'

			for person in item['credits']['cast']:
				try:
					# try:
						# castandart.append({'name': person['name'].encode('utf-8'), 'role': person['character'].encode('utf-8'), 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
					# except:
						# castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
					castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
				except: castandart = []
				if len(castandart) == 150: break

			for person in item['credits']['crew']:
				if 'Director' in person['job']:
					# director = ', '.join([director['name'].encode('utf-8') for director in item['credits']['crew'] if director['job'].lower() == 'director'])
					director = ', '.join([director['name'] for director in item['credits']['crew'] if director['job'].lower() == 'director'])
				if person['job'] in ['Writer', 'Screenplay', 'Author', 'Novel']:
					# writer = ', '.join([writer['name'].encode('utf-8') for writer in item['credits']['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])
					writer = ', '.join([writer['name'] for writer in item['credits']['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])

			poster3 = '%s%s' % (self.tmdb_poster, item['poster_path']) if item['poster_path'] else '0'
			fanart3 = '%s%s' % (self.tmdb_fanart, item['backdrop_path']) if item['backdrop_path'] else '0'

			try:
				if self.lang == 'en' or self.lang not in item.get('available_translations', [self.lang]):
					raise Exception()
				trans_item = trakt.getMovieTranslation(imdb, self.lang, full=True)
				title = trans_item.get('title') or title
				plot = trans_item.get('overview') or plot
			except:
				log_utils.error()

			item = {'title': title, 'originaltitle': originaltitle, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'premiered': premiered,
						'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director,
						'writer': writer, 'castandart': castandart, 'plot': plot, 'poster2': '0', 'poster3': poster3,
						'banner': '0', 'banner2': '0', 'fanart2': '0', 'fanart3': fanart3, 'clearlogo': '0', 'clearart': '0', 'landscape': '0',
						'discart': '0', 'mediatype': 'movie', 'trailer': trailer, 'metacache': False}
			meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.user, 'item': item}

			if self.disable_fanarttv != 'true':
				from resources.lib.indexers import fanarttv
				extended_art = cache.get(fanarttv.get_movie_art, 168, imdb, tmdb)
				if extended_art:
					item.update(extended_art)
					meta.update(item)

			if item.get('landscape', '0') == '0':
				item.update({'landscape': fanart3})
				meta.update(item)
			item = dict((k, v) for k, v in control.iteritems(item) if v and v != '0')
			self.list[i].update(item)
			self.meta.append(meta)
		except:
			log_utils.error()


class tvshows:
	def __init__(self):
		self.count = 40
		self.list = []
		self.meta = []

		self.lang = control.apiLanguage()['tvdb']
		# self.date_time = (datetime.utcnow() - timedelta(hours=5))
		self.date_time = datetime.utcnow()

		self.fanart_tv_user = control.setting('fanart.tv.user')
		if not self.fanart_tv_user:
			self.fanart_tv_user = 'cf0ebcc2f7b824bd04cf3a318f15c17d'
		self.user = self.fanart_tv_user + str('')
		self.tvdb_key = control.setting('tvdb.api.key')

		# self.tvdb_info_link = 'https://thetvdb.com/api/%s/series/%s/%s.xml' % (self.tvdb_key.decode('base64'), '%s', self.lang)
		self.tvdb_info_link = 'https://thetvdb.com/api/%s/series/%s/%s.xml' % (self.tvdb_key, '%s', self.lang)
		self.tvdb_by_imdb = 'https://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid=%s'
		self.tvdb_by_query = 'https://thetvdb.com/api/GetSeries.php?seriesname=%s'
		self.tvdb_image = 'https://thetvdb.com/banners/'
