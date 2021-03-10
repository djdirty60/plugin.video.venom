# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

import re
import requests
from resources.lib.modules import control
from resources.lib.modules import cache
from resources.lib.modules import metacache
from resources.lib.modules import py_tools
from resources.lib.modules import workers
from resources.lib.modules import log_utils

API_key = control.setting('tmdb.api.key')
if API_key == '' or API_key is None:
	API_key = '3320855e65a9758297fec4f7c9717698'

disable_fanarttv = control.setting('disable.fanarttv')
base_link = 'https://api.themoviedb.org/3/'
poster_path = 'https://image.tmdb.org/t/p/w300'
fanart_path = 'https://image.tmdb.org/t/p/w1280'


def get_request(url):
	try:
		try:
			response = requests.get(url)
		except requests.exceptions.SSLError:
			response = requests.get(url, verify=False)
	except requests.exceptions.ConnectionError:
		control.notification(message=32024)
		return
	if '200' in str(response):
		return response.json()
	elif 'Retry-After' in response.headers:
		# API REQUESTS ARE BEING THROTTLED, INTRODUCE WAIT TIME (removed 12-6-20)
		throttleTime = response.headers['Retry-After']
		control.notification(message='TMDB Throttling Applied, Sleeping for %s seconds' % throttleTime)
		control.sleep((int(throttleTime) + 1) * 1000)
		return get_request(url)
	else:
		log_utils.log('Get request failed to TMDB URL: %s\n                       msg : TMDB Response: %s' %
			(url, response.text), __name__, log_utils.LOGDEBUG)
		return None


def userlists(url):
	try:
		result = get_request(url % API_key)
		items = result['results']
		next = ''
		list = []
	except:
		return

	try: # This is actual wrong but may not be used so look into 
		page = int(result['page'])
		total = int(result['total_pages'])
		if page >= total: raise Exception()
		if 'page=' not in url: raise Exception()
		next = '%s&page=%s' % (url.split('&page=', 1)[0], page+1)
	except:
		next = ''

	for item in items:
		media_type = item.get('list_type')
		name = item.get('name')
		list_id =  item.get('id')
		url = 'https://api.themoviedb.org/4/list/%s?api_key=%s&sort_by=%s&page=1' % (list_id, API_key, tmdb_sort())
		item = {'media_type': media_type, 'name': name, 'list_id': list_id, 'url': url, 'context': url, 'next': next}
		list.append(item)
	return list


def popular_people(url):
	url = '%s%s' % (base_link, 'person/popular?api_key=%s&language=en-US&page=1' % API_key)


def tmdb_sort():
	sort = int(control.setting('sort.movies.type'))
	tmdb_sort = 'original_order'
	if sort == 1: tmdb_sort = 'title'
	if sort in [2, 3]: tmdb_sort = 'vote_average'
	if sort in [4, 5, 6]: tmdb_sort = 'release_date'
	tmdb_sort_order = '.asc' if int(control.setting('sort.movies.order')) == 0 else '.desc'
	sort_string = tmdb_sort + tmdb_sort_order
	return sort_string


class Movies:
	def __init__(self):
		self.list = []
		self.meta = []
		self.lang = control.apiLanguage()['trakt']
		self.details_link = base_link + 'movie/%s?api_key=%s&language=%s&append_to_response=credits,release_dates,videos' % ('%s', API_key, self.lang)
		# self.details_link = base_link + 'movie/%s?api_key=%s&language=%s&append_to_response=credits,release_dates,videos,alternative_titles' % ('%s', API_key, self.lang)
###                                                                             other "append_to_response" options                             external_ids,alternative_titles,images,content_ratings
		self.art_link = base_link + 'movie/%s/images?api_key=%s&include_image_language=en,%s,null' % ('%s', API_key, self.lang)
		self.external_ids = base_link + 'movie/%s/external_ids?api_key=%s' % ('%s', API_key)


	def tmdb_list(self, url):
		try:
			result = get_request(url % API_key)
			items = result['results']
		except: return

		self.list = [] ; sortList = []
		try:
			page = int(result['page'])
			total = int(result['total_pages'])
			if page >= total: raise Exception()
			if 'page=' not in url: raise Exception()
			next = '%s&page=%s' % (url.split('&page=', 1)[0], page+1)
		except: next = ''

		for item in items:
			try:
				title = py_tools.ensure_str(item.get('title'))
				originaltitle = title

				premiered = item.get('release_date', '0')
				try: year = str(premiered[:4])
				except: year = '0'

				tmdb = str(item.get('id'))
				sortList.append(tmdb)

				poster = '%s%s' % (poster_path, item['poster_path']) if item['poster_path'] else '0'
				fanart = '%s%s' % (fanart_path, item['backdrop_path']) if item['backdrop_path'] else '0'

				rating = str(item.get('vote_average', '0'))
				votes = str(format(int(item.get('vote_count', '0')),',d'))

				plot = item.get('overview')

				values = {'next': next, 'title': title, 'originaltitle': originaltitle, 'year': year, 'tmdb': tmdb, 'poster': poster, 'fanart': fanart,
								'premiered': premiered, 'rating': rating, 'votes': votes, 'plot': plot, 'metacache': False}
				self.list.append(values)
			except:
				log_utils.error()

		def items_list(i):
			if i['metacache']: return
			try:
				next, title, originaltitle, year, tmdb, poster, fanart, premiered, rating, votes, plot = \
					i['next'], i['title'], i['originaltitle'], i['year'], i['tmdb'], i['poster'], i['fanart'], i['premiered'], i['rating'], i['votes'], i['plot']
				url = self.details_link % tmdb
				item = get_request(url)

				imdb = item.get('imdb_id', '0')
				if not imdb or imdb == 'None': imdb = '0'

				# try: studio = item.get('production_companies', None)[0]['name']
				# except: studio = '0'

				genre = []
				for x in item['genres']: genre.append(x.get('name'))
				if genre == []: genre = 'NA'

				duration = str(item.get('runtime', '0'))
				if duration == 'None': duration = '0'

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

				credits = item['credits']
				director = writer = '0'
				for person in credits['crew']:
					if 'Director' in person['job']:
						# director = ', '.join([director['name'].encode('utf-8') for director in credits['crew'] if director['job'].lower() == 'director'])
						director = ', '.join([director['name'] for director in credits['crew'] if director['job'].lower() == 'director'])
					if person['job'] in ['Writer', 'Screenplay', 'Author', 'Novel']:
						# writer = ', '.join([writer['name'].encode('utf-8') for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])
						writer = ', '.join([writer['name'] for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])

				castandart = []
				for person in item['credits']['cast']:
					try:
						# try: castandart.append({'name': person['name'].encode('utf-8'), 'role': person['character'].encode('utf-8'), 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						# except: castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
					except: castandart = []
					if len(castandart) == 150: break

				try:
					trailer = [i for i in item['videos']['results'] if i['site'] == 'YouTube' and i['type'] == 'Trailer'][0]['key']
					trailer = control.trailer % trailer
				except: trailer = ''

				values = {'content': 'movie', 'title': title, 'originaltitle': originaltitle, 'year': year, 'premiered': premiered,
							'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer,
							'castandart': castandart, 'plot': plot, 'code': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': poster,
							'poster2': '0', 'poster3': '0', 'banner': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0',
							'landscape': fanart, 'mediatype': 'movie', 'trailer': trailer, 'metacache': False, 'next': next}
				meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': API_key, 'item': values}

				if disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = cache.get(fanarttv.get_movie_art, 168, imdb, tmdb)
					if extended_art:
						values.update(extended_art)
						meta.update(values)

				values = dict((k,v) for k, v in control.iteritems(values) if v and v != '0')
				for i in range(0, len(self.list)):
					if str(self.list[i]['tmdb']) == str(tmdb):
						self.list[i].update(values)

				if 'next' in meta.get('item'): del meta['item']['next']

				self.meta.append(meta)
				metacache.insert(self.meta)
			except:
				log_utils.error()

		self.list = metacache.fetch(self.list, self.lang, API_key)
		items = self.list[:len(self.list)]

		threads = []
		for i in items:
			threads.append(workers.Thread(items_list, i))
		[i.start() for i in threads]
		[i.join() for i in threads]

		sorted_list = []
		for i in sortList:
			sorted_list += [item for item in self.list if str(item['tmdb']) == str(i)]
		return sorted_list


	def tmdb_collections_list(self, url):
		try:
			result = get_request(url)
			if '/3/' in url: items = result['items']
			else: items = result['results']
		except: return

		self.list = []
		try:
			page = int(result['page'])
			total = int(result['total_pages'])
			if page >= total: raise Exception()
			if 'page=' not in url: raise Exception()
			next = '%s&page=%s' % (url.split('&page=', 1)[0], page+1)
		except: next = ''

		for item in items:
			try:
				media_type = item.get('media_type', '0')
				if media_type == 'tv': continue

				title = py_tools.ensure_str(item.get('title'))
				originaltitle = title

				premiered = item.get('release_date', '0')
				try: year = str(premiered[:4])
				except: year = '0'

				tmdb = str(item.get('id'))

				poster = '%s%s' % (poster_path, item['poster_path']) if item['poster_path'] else '0'
				fanart = '%s%s' % (fanart_path, item['backdrop_path']) if item['backdrop_path'] else '0'

				rating = str(item.get('vote_average', '0'))
				votes = str(format(int(item.get('vote_count', '0')),',d'))

				plot = item.get('overview')

				values = {'next': next, 'title': title, 'originaltitle': originaltitle, 'year': year, 'tmdb': tmdb, 'poster': poster, 'fanart': fanart,
								'premiered': premiered, 'rating': rating, 'votes': votes, 'plot': plot, 'metacache': False}
				self.list.append(values)
			except:
				log_utils.error()

		def items_list(i):
			if i['metacache']: return
			try:
				next, title, originaltitle, year, tmdb, poster, fanart, premiered, rating, votes, plot = \
					i['next'], i['title'], i['originaltitle'], i['year'], i['tmdb'], i['poster'], i['fanart'], i['premiered'], i['rating'], i['votes'], i['plot']
				url = self.details_link % tmdb
				item = get_request(url)

				imdb = item.get('imdb_id', '0')
				if not imdb or imdb == 'None': imdb = '0'

				# try: studio = item.get('production_companies', None)[0]['name']
				# except: studio = '0'

				genre = []
				for x in item['genres']: genre.append(x.get('name'))
				if genre == []: genre = 'NA'

				duration = str(item.get('runtime', '0'))
				if duration == 'None': duration = '0'

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

				credits = item['credits']
				director = writer = '0'
				for person in credits['crew']:
					if 'Director' in person['job']:
						# director = ', '.join([director['name'].encode('utf-8') for director in credits['crew'] if director['job'].lower() == 'director'])
						director = ', '.join([director['name'] for director in credits['crew'] if director['job'].lower() == 'director'])
					if person['job'] in ['Writer', 'Screenplay', 'Author', 'Novel']:
						# writer = ', '.join([writer['name'].encode('utf-8') for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])
						writer = ', '.join([writer['name'] for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])

				castandart = []
				for person in item['credits']['cast']:
					try:
						# try: castandart.append({'name': person['name'].encode('utf-8'), 'role': person['character'].encode('utf-8'), 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						# except: castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
					except: castandart = []
					if len(castandart) == 150: break

				try:
					trailer = [i for i in item['videos']['results'] if i['site'] == 'YouTube' and i['type'] == 'Trailer'][0]['key']
					trailer = control.trailer % trailer
				except: trailer = ''

				values = {'content': 'movie', 'title': title, 'originaltitle': originaltitle, 'year': year, 'premiered': premiered,
							'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer,
							'castandart': castandart, 'plot': plot, 'code': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': poster,
							'poster2': '0', 'poster3': '0', 'banner': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0',
							'landscape': fanart, 'mediatype': 'movie', 'trailer': trailer, 'metacache': False, 'next': next}
				meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': API_key, 'item': values}

				if disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = cache.get(fanarttv.get_movie_art, 168, imdb, tmdb)
					if extended_art:
						values.update(extended_art)
						meta.update(values)

				values = dict((k,v) for k, v in control.iteritems(values) if v and v != '0')
				for i in range(0, len(self.list)):
					if str(self.list[i]['tmdb']) == str(tmdb):
						self.list[i].update(values)

				if 'next' in meta.get('item'): del meta['item']['next']

				self.meta.append(meta)
				metacache.insert(self.meta)
			except:
				log_utils.error()

		self.list = metacache.fetch(self.list, self.lang, API_key)
		items = self.list[:len(self.list)]

		threads = []
		for i in items:
			threads.append(workers.Thread(items_list, i))
		[i.start() for i in threads]
		[i.join() for i in threads]
		return self.list


	def get_details(self, tmdb, imdb):
		item = None
		if tmdb != '0': item = get_request(self.details_link % tmdb)
		if not item:
			if imdb != '0': item = get_request(self.details_link % imdb) # api claims int rq'd.  But imdb_id works for movies but not looking like it does for shows
		return item


	def get_external_ids(self, tmdb, imdb):
		item = None
		if tmdb != '0': items = get_request(self.external_ids % tmdb)
		if not item:
			if imdb != '0': item = get_request(self.external_ids % imdb)
		return item


	def get_art(self, tmdb):
		if API_key == '' or (not tmdb or tmdb == '0' or tmdb == 'None'): return None
		art3 = get_request(self.art_link % tmdb)
		if not art3: return None
		try:
			poster3 = art3['posters']
			poster3 = [(x['width'], x['file_path']) for x in poster3]
			poster3 = [x[1] for x in poster3]
			poster3 = poster_path + poster3[0]
		except:
			poster3 = '0'
		try:
			fanart3 = art3['backdrops']
			fanart3 = [(x['width'], x['file_path']) for x in fanart3]
			fanart3 = [x[1] for x in fanart3]
			fanart3 = fanart_path + fanart3[0]
		except:
			fanart3 = '0'
		extended_art = {'extended': True, 'poster3': poster3, 'fanart3': fanart3}
		return extended_art


	def get_credits(self, tmdb):
		if API_key == '' or (not tmdb or tmdb == '0' or tmdb == 'None'): return None
		url = base_link + 'movie/%s/credits?api_key=%s' % ('%s', API_key)
		people = get_request(url % tmdb)
		if not people: return None
		return people


class TVshows:
	def __init__(self):
		self.list = []
		self.meta = []
		self.lang = control.apiLanguage()['tvdb']
		self.details_link = base_link + 'tv/%s?api_key=%s&language=%s&append_to_response=credits,content_ratings,external_ids' % ('%s', API_key, self.lang)
###                                                                                  other "append_to_response" options                                           alternative_titles,videos,images
		self.art_link = base_link + 'tv/%s/images?api_key=%s&include_image_language=en,%s,null' % ('%s', API_key, self.lang)
		self.tvdb_key = control.setting('tvdb.api.key')
		self.imdb_user = control.setting('imdb.user').replace('ur', '')
		self.user = str(self.imdb_user) + str(self.tvdb_key)


	def tmdb_list(self, url):
		try:
			result = get_request(url % API_key)
			items = result['results']
		except:
			return

		list = [] ; sortList = []
		try:
			page = int(result['page'])
			total = int(result['total_pages'])
			if page >= total: raise Exception()
			if 'page=' not in url: raise Exception()
			next = '%s&page=%s' % (url.split('&page=', 1)[0], page+1)
		except: next = ''

		for item in items:
			title = py_tools.ensure_str(item.get('name'))

			tmdb = str(item.get('id'))
			sortList.append(tmdb)

			poster = '%s%s' % (poster_path, item['poster_path']) if item['poster_path'] else '0'
			fanart = '%s%s' % (fanart_path, item['backdrop_path']) if item['backdrop_path'] else '0'

			premiered = item.get('first_air_date', '0')
			try: year = str(premiered[:4])
			except: year = '0'

			rating = str(item.get('vote_average', '0'))
			votes = str(format(int(item.get('vote_count', '0')),',d'))
			plot = py_tools.ensure_str(item.get('overview'))

			values = {'next': next, 'title': title, 'year': year, 'tmdb': tmdb, 'poster': poster, 'fanart': fanart,
							'premiered': premiered, 'rating': rating, 'votes': votes, 'plot': plot}
			list.append(values)

		def items_list(i):
			# if i['metacache']: return
			try:
				next, title, year, tmdb, poster, fanart, premiered, rating, votes, plot = \
					i['next'], i['title'], i['year'], i['tmdb'], i['poster'], i['fanart'], i['premiered'], i['rating'], i['votes'], i['plot']
				url = self.details_link % tmdb
				item = get_request(url)

				tvdb = str(item.get('external_ids').get('tvdb_id', '0'))
				if not tvdb or tvdb == 'None': tvdb = '0'

				imdb = item.get('external_ids').get('imdb_id', '0')
				if not imdb or imdb == 'None': imdb = '0'

				genre = []
				for x in item['genres']: genre.append(x.get('name'))
				if genre == []: genre = 'NA'

				try: duration = str(item.get('episode_run_time', '0')[0])
				except: duration = '0'
				if duration == 'None': duration = '0'

				try: mpaa = [x['rating'] for x in item['content_ratings']['results'] if x['iso_3166_1'] == 'US'][0]
				except: 
					try: mpaa = item['content_ratings'][0]['rating']
					except: mpaa = 'NR'

				status = item.get('status', '0')

				try: studio = item.get('networks', None)[0]['name']
				except: studio = '0'

				try: total_seasons = int(item.get('number_of_seasons', ''))
				except: total_seasons = 0

				credits = item['credits']
				director = writer = '0'
				for person in credits['crew']:
					if 'Director' in person['job']:
						# director = ', '.join([director['name'].encode('utf-8') for director in credits['crew'] if director['job'].lower() == 'director'])
						director = ', '.join([director['name'] for director in credits['crew'] if director['job'].lower() == 'director'])
					if person['job'] in ['Writer', 'Screenplay', 'Author', 'Novel']:
						# writer = ', '.join([writer['name'].encode('utf-8') for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])
						writer = ', '.join([writer['name'] for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])

				castandart = []
				for person in item['credits']['cast']:
					try:
						# try: castandart.append({'name': person['name'].encode('utf-8'), 'role': person['character'].encode('utf-8'), 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						# except: castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
					except: castandart = []
					if len(castandart) == 150: break

				values = {'content': 'tvshow', 'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating,
								'votes': votes, 'mpaa': mpaa, 'status': status, 'director': director, 'writer': writer, 'castandart': castandart, 'plot': plot, 'code': tmdb, 'imdb': imdb,
								'tmdb': tmdb, 'tvdb': tvdb, 'poster': poster, 'poster2': '0', 'poster3': '0', 'banner': '0', 'banner2': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0',
								'landscape': fanart, 'total_seasons': total_seasons, 'metacache': False, 'next': next}
				meta = {'tmdb': tmdb, 'imdb': imdb, 'tvdb': tvdb, 'lang': self.lang, 'user': self.user, 'item': values}

				if disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = cache.get(fanarttv.get_tvshow_art, 168, tvdb)
					if extended_art:
						values.update(extended_art)
						meta.update(values)

				values = dict((k,v) for k, v in control.iteritems(values) if v and v != '0')
				self.list.append(values)
				if 'next' in meta.get('item'): del meta['item']['next']
				self.meta.append(meta)
				metacache.insert(self.meta)
			except:
				log_utils.error()

		items = list[:len(list)]
		threads = []
		for i in items:
			threads.append(workers.Thread(items_list, i))
		[i.start() for i in threads]
		[i.join() for i in threads]

		sorted_list = []
		for i in sortList:
			sorted_list += [item for item in self.list if item['tmdb'] == i]
		return sorted_list


	def tmdb_collections_list(self, url):
		try:
			result = get_request(url)
			if '/3/' in url: items = result['items']
			else: items = result['results']
		except:
			log_utils.error()
			return

		list = [] ; sortList = []
		try:
			page = int(result['page'])
			total = int(result['total_pages'])
			if page >= total: raise Exception()
			if 'page=' not in url: raise Exception()
			next = '%s&page=%s' % (url.split('&page=', 1)[0], page+1)
		except: next = ''

		for item in items:
			media_type = item.get('media_type', '0')
			if media_type == 'movie': 	continue

			# try: title = item.get('name').encode('utf-8')
			# except: title = item.get('name')
			title = item.get('name')

			tmdb = str(item.get('id'))
			sortList.append(tmdb)

			poster = '%s%s' % (poster_path, item['poster_path']) if item['poster_path'] else '0'
			fanart = '%s%s' % (fanart_path, item['backdrop_path']) if item['backdrop_path'] else '0'

			premiered = item.get('first_air_date', '0')
			try: year = str(premiered[:4])
			except: year = '0'

			rating = str(item.get('vote_average', '0'))
			votes = str(format(int(item.get('vote_count', '0')),',d'))

			plot = item.get('overview')

			values = {'next': next, 'title': title, 'year': year, 'tmdb': tmdb, 'poster': poster, 'fanart': fanart,
							'premiered': premiered, 'rating': rating, 'votes': votes, 'plot': plot}
			list.append(values)

		def items_list(i):
			# if i['metacache']: return
			try:
				next, title, year, tmdb, poster, fanart, premiered, rating, votes, plot = \
					i['next'], i['title'], i['year'], i['tmdb'], i['poster'], i['fanart'], i['premiered'], i['rating'], i['votes'], i['plot']
				url = self.details_link % tmdb
				item = get_request(url)

				tvdb = str(item.get('external_ids').get('tvdb_id', '0'))
				if not tvdb or tvdb == 'None': tvdb = '0'

				imdb = item.get('external_ids').get('imdb_id', '0')
				if not imdb or imdb == 'None': imdb = '0'

				genre = []
				for x in item['genres']: genre.append(x.get('name'))
				if genre == []: genre = 'NA'

				try: duration = str(item.get('episode_run_time', '0')[0])
				except: duration = '0'
				if duration == 'None': duration = '0'

				try: mpaa = [x['rating'] for x in item['content_ratings']['results'] if x['iso_3166_1'] == 'US'][0]
				except: 
					try: mpaa = item['content_ratings'][0]['rating']
					except: mpaa = 'NR'

				status = item.get('status', '0')

				try: studio = item.get('networks', None)[0]['name']
				except: studio = '0'

				try: total_seasons = int(item.get('number_of_seasons', ''))
				except: total_seasons = 0

				credits = item['credits']
				director = writer = '0'
				for person in credits['crew']:
					if 'Director' in person['job']:
						# director = ', '.join([director['name'].encode('utf-8') for director in credits['crew'] if director['job'].lower() == 'director'])
						director = ', '.join([director['name'] for director in credits['crew'] if director['job'].lower() == 'director'])
					if person['job'] in ['Writer', 'Screenplay', 'Author', 'Novel']:
						# writer = ', '.join([writer['name'].encode('utf-8') for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])
						writer = ', '.join([writer['name'] for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])

				castandart = []
				for person in item['credits']['cast']:
					try:
						# try: castandart.append({'name': person['name'].encode('utf-8'), 'role': person['character'].encode('utf-8'), 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						# except: castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((poster_path + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
					except: castandart = []
					if len(castandart) == 150: break

				values = {'content': 'tvshow', 'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating,
								'votes': votes, 'mpaa': mpaa, 'status': status, 'director': director, 'writer': writer, 'castandart': castandart, 'plot': plot, 'code': tmdb, 'imdb': imdb,
								'tmdb': tmdb, 'tvdb': tvdb, 'poster': poster, 'poster2': '0', 'poster3': '0', 'banner': '0', 'banner2': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0',
								'landscape': fanart, 'total_seasons': total_seasons, 'metacache': False, 'next': next}
				meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'lang': self.lang, 'user': self.user, 'item': values}

				if disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = cache.get(fanarttv.get_tvshow_art, 168, tvdb)
					if extended_art:
						values.update(extended_art)
						meta.update(values)

				values = dict((k,v) for k, v in control.iteritems(values) if v and v != '0')
				self.list.append(values)
				if 'next' in meta.get('item'): del meta['item']['next']
				self.meta.append(meta)
				metacache.insert(self.meta)
			except:
				log_utils.error()

		items = list[:len(list)]
		threads = []
		for i in items:
			threads.append(workers.Thread(items_list, i))
		[i.start() for i in threads]
		[i.join() for i in threads]

		sorted_list = []
		for i in sortList:
			sorted_list += [item for item in self.list if item['tmdb'] == i]
		return sorted_list


	def get_details(self, tmdb, imdb):
		item = None
		if tmdb != '0': item = get_request(self.details_link % tmdb)
		if not item:
			if imdb != '0': item = get_request(self.details_link % imdb) # api claims int rq'd.  But imdb_id works for movies but not looking like it does for shows
		return item


	def get_seasons(self, tmdb, imdb, season):
		item = None
		url = '%s%s' % (base_link, 'tv/%s/season/%s?api_key=%s&language=%s,en-US&append_to_response=credits' % ('%s', season, API_key, self.lang))
		if tmdb != '0': item = get_request(url % tmdb)
		if not item:
			if imdb != '0': item = get_request(url % imdb) # api claims int rq'd.  But imdb_id works for movies but not looking like it does for shows
		return item


	def get_art(self, tmdb):
		if API_key == '' or (not tmdb or tmdb == '0' or tmdb == 'None'): return None
		art3 = get_request(self.art_link % tmdb)
		if not art3: return None
		try:
			poster3 = art3['posters']
			poster3 = [(x['width'], x['file_path']) for x in poster3]
			poster3 = [x[1] for x in poster3]
			poster3 = poster_path + poster3[0]
		except:
			poster3 = '0'
		try:
			fanart3 = art3['backdrops']
			fanart3 = [(x['width'], x['file_path']) for x in fanart3]
			fanart3 = [x[1] for x in fanart3]
			fanart3 = fanart_path + fanart3[0]
		except:
			fanart3 = '0'
		extended_art = {'extended': True, 'poster3': poster3, 'fanart3': fanart3}
		return extended_art


	def get_credits(self, tmdb):
		if API_key == '' or (not tmdb or tmdb == '0' or tmdb == 'None'): return None
		url = base_link + 'tv/%s/credits?api_key=%s' % ('%s', API_key)
		people = get_request(url % tmdb)
		if not people: return None
		return people


class Auth:
	def __init__(self):
		# self.auth_base_link = 'https://api.themoviedb.org/3/authentication'
		self.auth_base_link = '%s%s' % (base_link, 'authentication')


	def create_session_id(self):
		try:
			if control.setting('tmdb.username') == '' or control.setting('tmdb.password') == '':
				control.notification(message='TMDb Account info missing', icon='ERROR')
				return
			url = self.auth_base_link + '/token/new?api_key=%s' % API_key
			result = requests.get(url).json()
			# token = result.get('request_token').encode('utf-8')
			token = result.get('request_token')
			url2 = self.auth_base_link + '/token/validate_with_login?api_key=%s' % API_key
			post2 = {"username": "%s" % control.setting('tmdb.username'),
							"password": "%s" % control.setting('tmdb.password'),
							"request_token": "%s" % token}
			result2 = requests.post(url2, data=post2).json()
			url3 = self.auth_base_link + '/session/new?api_key=%s' % API_key
			post3 = {"request_token": "%s" % token}
			result3 = requests.post(url3, data=post3).json()
			if result3.get('success') is True:
				session_id = result3.get('session_id')
				msg = '%s' % ('username =' + username + '[CR]password =' + password + '[CR]token = ' + token + '[CR]confirm?')
				if control.yesnoDialog(msg, '', ''):
					control.setSetting('tmdb.session_id', session_id)
					control.notification(message='TMDb Successfully Authorized')
				else:
					control.notification(message='TMDb Authorization Cancelled')
		except:
			log_utils.error()


	def revoke_session_id(self):
		try:
			if control.setting('tmdb.session_id') == '':
				return
			url = self.auth_base_link + '/session?api_key=%s' % API_key
			post = {"session_id": "%s" % control.setting('tmdb.session_id')}
			result = requests.delete(url, data=post).json()
			if result.get('success') is True:
				control.setSetting('tmdb.session_id', '')
				control.notification(message='TMDb session_id successfully deleted')
			else:
				control.notification(message='TMDb session_id deletion FAILED', icon='ERROR')
		except:
			log_utils.error()
