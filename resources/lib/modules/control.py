# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from datetime import datetime
from json import dumps as jsdumps, loads as jsloads
import os.path
import re
from string import printable
from sys import version_info
import time
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
import xml.etree.ElementTree as ET

def getKodiVersion(full=False):
	if full: return xbmc.getInfoLabel("System.BuildVersion")
	else: return int(xbmc.getInfoLabel("System.BuildVersion")[:2])

pythonVersion = '{}.{}.{}'.format(version_info[0], version_info[1], version_info[2])
isPY2 = version_info[0] == 2
isPY3 = version_info[0] == 3

addon = xbmcaddon.Addon
AddonID = xbmcaddon.Addon().getAddonInfo('id')
addonInfo = xbmcaddon.Addon().getAddonInfo
addonName = addonInfo('name')
addonVersion = addonInfo('version')
getLangString = xbmcaddon.Addon().getLocalizedString
# setting = xbmcaddon.Addon().getSetting
# setSetting = xbmcaddon.Addon().setSetting

dialog = xbmcgui.Dialog()
getCurrentDialogId = xbmcgui.getCurrentWindowDialogId()
homeWindow = xbmcgui.Window(10000)
item = xbmcgui.ListItem
progressDialog = xbmcgui.DialogProgress()
progressDialogBG = xbmcgui.DialogProgressBG()

addItem = xbmcplugin.addDirectoryItem
content = xbmcplugin.setContent
directory = xbmcplugin.endOfDirectory
property = xbmcplugin.setProperty
resolve = xbmcplugin.setResolvedUrl

condVisibility = xbmc.getCondVisibility
execute = xbmc.executebuiltin
infoLabel = xbmc.getInfoLabel
jsonrpc = xbmc.executeJSONRPC
keyboard = xbmc.Keyboard
legalFilename = xbmc.makeLegalFilename if getKodiVersion() < 19 else xbmcvfs.makeLegalFilename
log = xbmc.log
monitor_class = xbmc.Monitor
monitor = monitor_class()
player = xbmc.Player()
player2 = xbmc.Player
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
skin = xbmc.getSkinDir()
transPath = xbmc.translatePath if getKodiVersion() < 19 else xbmcvfs.translatePath

deleteDir = xbmcvfs.rmdir
deleteFile = xbmcvfs.delete
existsPath = xbmcvfs.exists
listDir = xbmcvfs.listdir
makeFile = xbmcvfs.mkdir
makeDirs = xbmcvfs.mkdirs
openFile = xbmcvfs.File

joinPath = os.path.join
isfilePath = os.path.isfile

SETTINGS_PATH = transPath(joinPath(addonInfo('path'), 'resources', 'settings.xml'))
try: dataPath = transPath(addonInfo('profile')).decode('utf-8')
except: dataPath = transPath(addonInfo('profile'))

settingsFile = joinPath(dataPath, 'settings.xml')
viewsFile = joinPath(dataPath, 'views.db')
bookmarksFile = joinPath(dataPath, 'bookmarks.db')
providercacheFile = joinPath(dataPath, 'providers.db')
metacacheFile = joinPath(dataPath, 'metadata.db')
searchFile = joinPath(dataPath, 'search.db')
libcacheFile = joinPath(dataPath, 'library.db')
cacheFile = joinPath(dataPath, 'cache.db')
traktSyncFile = joinPath(dataPath, 'traktSync.db')
trailer = 'plugin://plugin.video.youtube/play/?video_id=%s'

if isPY3:
	def iteritems(d, **kw):
		return iter(d.items(**kw))
else:
	def iteritems(d, **kw):
		return d.iteritems(**kw)

def syncMyAccounts(silent=False):
	import myaccounts
	all_acct = myaccounts.getAll()
	trakt_acct = all_acct.get('trakt')
	if setting('trakt.username') != trakt_acct.get('username'):
		setSetting('trakt.isauthed', 'true')
		setSetting('trakt.token', trakt_acct.get('token'))
		setSetting('trakt.username', trakt_acct.get('username'))
		setSetting('trakt.refresh', trakt_acct.get('refresh'))
		setSetting('trakt.expires', trakt_acct.get('expires'))
	ad_acct = all_acct.get('alldebrid')
	if setting('alldebrid.username') != ad_acct.get('username'):
		setSetting('alldebrid.token', ad_acct.get('token'))
		setSetting('alldebrid.username', ad_acct.get('username'))
	pm_acct = all_acct.get('premiumize')
	if setting('premiumize.username') != pm_acct.get('username'):
		setSetting('premiumize.token', pm_acct.get('token'))
		setSetting('premiumize.username', pm_acct.get('username'))
	rd_acct = all_acct.get('realdebrid')
	if setting('realdebrid.username') != rd_acct.get('username'):
		setSetting('realdebrid.token', rd_acct.get('token'))
		setSetting('realdebrid.username', rd_acct.get('username'))
		setSetting('realdebrid.client_id', rd_acct.get('client_id'))
		setSetting('realdebrid.refresh', rd_acct.get('refresh'))
		setSetting('realdebrid.secret', rd_acct.get('secret'))
	fanart_acct = all_acct.get('fanart_tv')
	if setting('fanart.tv.api.key') != fanart_acct.get('api_key'):
		setSetting('fanart.tv.api.key', fanart_acct.get('api_key'))
	tmdb_acct = all_acct.get('tmdb')
	if setting('tmdb.api.key') != tmdb_acct.get('api_key'):
		setSetting('tmdb.api.key', tmdb_acct.get('api_key'))
	if setting('tmdb.username') != tmdb_acct.get('username'):
		setSetting('tmdb.username', tmdb_acct.get('username'))
	if setting('tmdb.password') != tmdb_acct.get('password'):
		setSetting('tmdb.password', tmdb_acct.get('password'))
	if setting('tmdb.session_id') != tmdb_acct.get('session_id'):
		setSetting('tmdb.session_id', tmdb_acct.get('session_id'))
	tvdb_acct = all_acct.get('tvdb')
	if setting('tvdb.api.key') != tvdb_acct.get('api_key'):
		setSetting('tvdb.api.key', tvdb_acct.get('api_key'))
	imdb_acct = all_acct.get('imdb')
	if setting('imdb.user') != imdb_acct.get('user'):
		setSetting('imdb.user', imdb_acct.get('user'))
	fu_acct = all_acct.get('furk')
	if setting('furk.username') != fu_acct.get('username'):
		setSetting('furk.username', fu_acct.get('username'))
		setSetting('furk.password', fu_acct.get('password'))
	if fu_acct.get('api_key', None):
		if setting('furk.api') != fu_acct.get('api_key'):
			setSetting('furk.api', fu_acct.get('api_key'))
	if not silent:
		notification(message=32114)

def setting(id, fallback=None):
	try: settings_dict = jsloads(homeWindow.getProperty('venom_settings'))
	except: settings_dict = make_settings_dict()
	if settings_dict is None: settings_dict = settings_fallback(id)
	value = settings_dict.get(id, '')
	if fallback is None: return value
	if value == '': return fallback
	return value

def settings_fallback(id):
	return {id: xbmcaddon.Addon().getSetting(id)}

def setSetting(id, value):
	from xbmcaddon import Addon
	Addon().setSetting(id, value)

def make_settings_dict(): # service runs upon a setting change
	try:
		root = ET.parse(settingsFile).getroot()
		settings_dict = {}
		for item in root:
			dict_item = {}
			setting_id = item.get('id')
			if getKodiVersion() >= 18: setting_value = item.text
			else: setting_value = item.get('value')
			if setting_value is None: setting_value = ''
			dict_item = {setting_id: setting_value}
			settings_dict.update(dict_item)
		homeWindow.setProperty('venom_settings', jsdumps(settings_dict))
		# log('settings_dict = %s' % settings_dict, 2)
		refresh_playAction()
		return settings_dict
	except:
		return None

def refresh_playAction(): # for venom global CM play actions
	playAction = setting('hosts.mode')
	autoPlay = 'true' if playAction == '2' else ''
	homeWindow.setProperty('plugin.video.venom.autoPlay', autoPlay)

def lang(language_id):
	text = getLangString(language_id)
	if getKodiVersion() < 19:
		text = text.encode('utf-8', 'replace')
	return str(text)

def strip_non_ascii_and_unprintable(text):
	try:
		result = ''.join(char for char in text if char in printable)
		return result.encode('ascii', errors='ignore').decode('ascii', errors='ignore')
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def sleep(time):  # Modified `sleep`(in milli secs) that honors a user exit request
	while time > 0 and not monitor.abortRequested():
		xbmc.sleep(min(100, time))
		time = time - 100

def getCurrentViewId():
	win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
	return str(win.getFocusId())

def check_version_numbers(current, new):
	# Compares version numbers and return True if new version is newer
	current = current.split('.')
	new = new.split('.')
	step = 0
	for i in current:
		if int(new[step]) > int(i): return True
		if int(i) > int(new[step]): return False
		if int(i) == int(new[step]):
			step += 1
			continue
	return False

def getVenomVersion():
	return xbmcaddon.Addon('plugin.video.venom').getAddonInfo('version')

def addonVersion(addon):
	return xbmcaddon.Addon(addon).getAddonInfo('version')

def addonId():
	return addonInfo('id')

def addonName():
	return addonInfo('name')

# addonPath = transPath(addonInfo('path'))
def addonPath(addon):
	try: addonID = xbmcaddon.Addon(addon)
	except: addonID = None
	if addonID is None: return ''
	else:
		try: return transPath(addonID.getAddonInfo('path').decode('utf-8'))
		except: return transPath(addonID.getAddonInfo('path'))

def artPath():
	theme = appearance()
	return joinPath(xbmcaddon.Addon('plugin.video.venom').getAddonInfo('path'), 'resources', 'artwork', theme)
	# return joinPath(addonPath('plugin.video.venom'), 'resources', 'artwork', theme)

def appearance():
	appearance = setting('appearance.1').lower()
	return appearance

def addonIcon():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']): return joinPath(art, 'icon.png')
	return addonInfo('icon')

def addonThumb():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']): return joinPath(art, 'poster.png')
	elif theme == '-': return 'DefaultFolder.png'
	return addonInfo('icon')

def addonPoster():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']): return joinPath(art, 'poster.png')
	return 'DefaultVideo.png'

def addonBanner():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']): return joinPath(art, 'banner.png')
	return 'DefaultVideo.png'

def addonFanart():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']): return joinPath(art, 'fanart.jpg')
	return addonInfo('fanart')

def addonNext():
	theme = appearance()
	art = artPath()
	if not (art is None and theme in ['-', '']): return joinPath(art, 'next.png')
	return 'DefaultVideo.png'

def metadataClean(metadata):
	if not metadata: return metadata
	allowed = ['genre', 'country', 'year', 'episode', 'season', 'sortepisode', 'sortseason', 'episodeguide', 'showlink',
					'top250', 'setid', 'tracknumber', 'rating', 'userrating', 'watched', 'playcount', 'overlay', 'cast',
					'castandrole', 'director', 'mpaa', 'plot', 'plotoutline', 'title', 'originaltitle', 'sorttitle',
					'duration', 'studio', 'tagline', 'writer', 'tvshowtitle', 'premiered', 'status', 'set', 'setoverview',
					'tag', 'imdbnumber', 'code', 'aired', 'credits', 'lastplayed', 'album', 'artist', 'votes', 'path',
					'trailer', 'dateadded', 'mediatype', 'dbid']
	return {k: v for k, v in iteritems(metadata) if k in allowed}

####################################################
# --- Dialogs
####################################################
def notification(title=None, message=None, icon=None, time=3000, sound=(setting('notification.sound') == 'true')):
	if title == 'default' or title is None: title = addonName()
	if isinstance(title, int): heading = lang(title)
	else: heading = str(title)
	if isinstance(message, int): body = lang(message)
	else: body = str(message)
	if icon is None or icon == '' or icon == 'default': icon = addonIcon()
	elif icon == 'INFO': icon = xbmcgui.NOTIFICATION_INFO
	elif icon == 'WARNING': icon = xbmcgui.NOTIFICATION_WARNING
	elif icon == 'ERROR': icon = xbmcgui.NOTIFICATION_ERROR
	return dialog.notification(heading, body, icon, time, sound)

def yesnoDialog(line1, line2, line3, heading=addonInfo('name'), nolabel='', yeslabel=''):
	if isPY3:
		message = line1 + line2 + line3
		return dialog.yesno(heading, message, nolabel, yeslabel)
	else: return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel)

def selectDialog(list, heading=addonInfo('name')):
	return dialog.select(heading, list)

def okDialog(title=None, message=None):
	if title == 'default' or title is None: title = addonName()
	if isinstance(title, int): heading = lang(title)
	else: heading = str(title)
	if isinstance(message, int): body = lang(message)
	else: body = str(message)
	return dialog.ok(heading, body)

def context(items=None, labels=None):
	if items:
		labels = [i[0] for i in items]
		choice = dialog.contextmenu(labels)
		if choice >= 0: return items[choice][1]()
		else: return False
	else: return dialog.contextmenu(labels)

def busy():
	if getKodiVersion() >= 18: return execute('ActivateWindow(busydialognocancel)')
	else: return execute('ActivateWindow(busydialog)')

def hide():
	execute('Dialog.Close(busydialog)')
	if getKodiVersion() >= 18: execute('Dialog.Close(busydialognocancel)')

def closeAll():
	return execute('Dialog.Close(all,true)')

def closeOk():
	return execute('Dialog.Close(okdialog,true)')
########################

def cancelPlayback():
	try:
		from sys import argv
		playlist.clear()
		resolve(int(argv[1]), False, item(offscreen=True))
		closeOk()
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def refresh():
	return execute('Container.Refresh')

def queueItem():
	return execute('Action(Queue)')

def openSettings(query=None, id=addonInfo('id')):
	try:
		hide()
		execute('Addon.OpenSettings(%s)' % id)
		if not query: return
		c, f = query.split('.')
		if getKodiVersion() >= 18:
			execute('SetFocus(%i)' % (int(c) - 100))
			execute('SetFocus(%i)' % (int(f) - 80))
		else:
			execute('SetFocus(%i)' % (int(c) + 100))
			execute('SetFocus(%i)' % (int(f) + 200))
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def apiLanguage(ret_name=None):
	langDict = {'Bulgarian': 'bg', 'Chinese': 'zh', 'Croatian': 'hr', 'Czech': 'cs', 'Danish': 'da', 'Dutch': 'nl', 'English': 'en', 'Finnish': 'fi',
					'French': 'fr', 'German': 'de', 'Greek': 'el', 'Hebrew': 'he', 'Hungarian': 'hu', 'Italian': 'it', 'Japanese': 'ja', 'Korean': 'ko',
					'Norwegian': 'no', 'Polish': 'pl', 'Portuguese': 'pt', 'Romanian': 'ro', 'Russian': 'ru', 'Serbian': 'sr', 'Slovak': 'sk',
						'Slovenian': 'sl', 'Spanish': 'es', 'Swedish': 'sv', 'Thai': 'th', 'Turkish': 'tr', 'Ukrainian': 'uk'}
	trakt = ['bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'fi', 'fr', 'he', 'hr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sr', 'sv', 'th', 'tr', 'uk', 'zh']
	tvdb = ['en', 'sv', 'no', 'da', 'fi', 'nl', 'de', 'it', 'es', 'fr', 'pl', 'hu', 'el', 'tr', 'ru', 'he', 'ja', 'pt', 'zh', 'cs', 'sl', 'hr', 'ko']
	youtube = ['gv', 'gu', 'gd', 'ga', 'gn', 'gl', 'ty', 'tw', 'tt', 'tr', 'ts', 'tn', 'to', 'tl', 'tk', 'th', 'ti', 'tg', 'te', 'ta', 'de', 'da', 'dz', 'dv', 'qu', 'zh', 'za', 'zu',
					'wa', 'wo', 'jv', 'ja', 'ch', 'co', 'ca', 'ce', 'cy', 'cs', 'cr', 'cv', 'cu', 'ps', 'pt', 'pa', 'pi', 'pl', 'mg', 'ml', 'mn', 'mi', 'mh', 'mk', 'mt', 'ms',
					'mr', 'my', 've', 'vi', 'is', 'iu', 'it', 'vo', 'ii', 'ik', 'io', 'ia', 'ie', 'id', 'ig', 'fr', 'fy', 'fa', 'ff', 'fi', 'fj', 'fo', 'ss', 'sr', 'sq', 'sw', 'sv', 'su', 'st', 'sk',
					'si', 'so', 'sn', 'sm', 'sl', 'sc', 'sa', 'sg', 'se', 'sd', 'lg', 'lb', 'la', 'ln', 'lo', 'li', 'lv', 'lt', 'lu', 'yi', 'yo', 'el', 'eo', 'en', 'ee', 'eu', 'et', 'es', 'ru',
					'rw', 'rm', 'rn', 'ro', 'be', 'bg', 'ba', 'bm', 'bn', 'bo', 'bh', 'bi', 'br', 'bs', 'om', 'oj', 'oc', 'os', 'or', 'xh', 'hz', 'hy', 'hr', 'ht', 'hu', 'hi', 'ho',
					'ha', 'he', 'uz', 'ur', 'uk', 'ug', 'aa', 'ab', 'ae', 'af', 'ak', 'am', 'an', 'as', 'ar', 'av', 'ay', 'az', 'nl', 'nn', 'no', 'na', 'nb', 'nd', 'ne', 'ng',
					'ny', 'nr', 'nv', 'ka', 'kg', 'kk', 'kj', 'ki', 'ko', 'kn', 'km', 'kl', 'ks', 'kr', 'kw', 'kv', 'ku', 'ky']
	tmdb = ['bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'fi', 'fr', 'he', 'hr', 'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sr', 'sv', 'th', 'tr', 'uk', 'zh']
	name = None
	name = setting('api.language')
	if not name: name = 'AUTO'
	if name[-1].isupper():
		try: name = xbmc.getLanguage(xbmc.ENGLISH_NAME).split(' ')[0]
		except: pass
	try: name = langDict[name]
	except: name = 'en'
	lang = {'trakt': name} if name in trakt else {'trakt': 'en'}
	lang['tvdb'] = name if name in tvdb else 'en'
	lang['youtube'] = name if name in youtube else 'en'
	lang['tmdb'] = name if name in tmdb else 'en'
	if ret_name:
		lang['trakt'] = [i[0] for i in iteritems(langDict) if i[1] == lang['trakt']][0]
		lang['tvdb'] = [i[0] for i in iteritems(langDict) if i[1] == lang['tvdb']][0]
		lang['youtube'] = [i[0] for i in iteritems(langDict) if i[1] == lang['youtube']][0]
		lang['tmdb'] = [i[0] for i in iteritems(langDict) if i[1] == lang['tmdb']][0]
	return lang

def autoTraktSubscription(tvshowtitle, year, imdb, tvdb): #---start adding TMDb to params
	from resources.lib.modules import libtools
	libtools.libtvshows().add(tvshowtitle, year, imdb, tvdb)

def getSettingDefault(id):
	try:
		settings = open(SETTINGS_PATH, 'r')
		value = ' '.join(settings.readlines())
		value.strip('\n')
		settings.close()
		value = re.findall(r'id=\"%s\".*?default=\"(.*?)\"' % (id), value)[0]
		return value
	except:
		return None

def getColor(n):
	colorChart = ['blue', 'red', 'yellow', 'deeppink', 'cyan', 'lawngreen', 'gold', 'magenta', 'yellowgreen',
						'skyblue', 'lime', 'limegreen', 'deepskyblue', 'white', 'whitesmoke', 'nocolor']
	if not n: n = '8'
	color = colorChart[int(n)]
	return color

def getMenuEnabled(menu_title):
	is_enabled = setting(menu_title).strip()
	if (is_enabled == '' or is_enabled == 'false'): return False
	return True

def trigger_widget_refresh():
	import time
	timestr = time.strftime("%Y%m%d%H%M%S", time.gmtime())
	homeWindow.setProperty("widgetreload", timestr)
	homeWindow.setProperty('widgetreload-tvshows', timestr)
	homeWindow.setProperty('widgetreload-episodes', timestr)
	homeWindow.setProperty('widgetreload-movies', timestr)
# should prob make this run only on "isVenom_widget"
	# execute('UpdateLibrary(video,/fake/path/to/force/refresh/on/home)') # make sure this is ok coupled with above

def get_video_database_path():
	database_path = os.path.abspath(joinPath(dataPath, '..', '..', 'Database', ))
	kodi_version = getKodiVersion()
	if kodi_version == 17: database_path = joinPath(database_path, 'MyVideos107.db')
	elif kodi_version == 18: database_path = joinPath(database_path, 'MyVideos116.db')
	elif kodi_version == 19: database_path = joinPath(database_path, 'MyVideos119.db')
	return database_path

def datetime_workaround(string_date, format="%Y-%m-%d", date_only=True):
	sleep(200)
	try:
		if string_date == '': return None
		try:
			if date_only: res = datetime.strptime(string_date, format).date()
			else: res = datetime.strptime(string_date, format)
		except TypeError:
			if date_only: res = datetime(*(time.strptime(string_date, format)[0:6])).date()
			else: res = datetime(*(time.strptime(string_date, format)[0:6]))
		return res
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def add_source(source_name, source_path, source_content, source_thumbnail, type='video'):
	xml_file = transPath('special://profile/sources.xml')
	if not os.path.exists(xml_file):
		with open(xml_file, 'w') as f:
			f.write(
'''
<sources>
	<programs>
		<default pathversion="1"/>
	</programs>
	<video>
		<default pathversion="1"/>
	</video>
	<music>
		<default pathversion="1"/>
	</music>
	<pictures>
		<default pathversion="1"/>
	</pictures>
	<files>
		<default pathversion="1"/>
	</files>
	<games>
		<default pathversion="1"/>
	</games>
</sources>
''')
	existing_source = _get_source_attr(xml_file, source_name, 'path', type=type)
	if existing_source and existing_source != source_path and source_content != '':
		_remove_source_content(existing_source)
	if _add_source_xml(xml_file, source_name, source_path, source_thumbnail, type=type) and source_content != '':
		_remove_source_content(source_path) # Added to also rid any remains because manual delete sources and kodi leaves behind a record in MyVideos*.db
		_set_source_content(source_content)

def _add_source_xml(xml_file, name, path, thumbnail, type='video'):
	tree = ET.parse(xml_file)
	root = tree.getroot()
	sources = root.find(type)
	existing_source = None
	for source in sources.findall('source'):
		xml_name = source.find('name').text
		xml_path = source.find('path').text
		if source.find('thumbnail') is not None:
			xml_thumbnail = source.find('thumbnail').text
		else:
			xml_thumbnail = ''
		if xml_name == name or xml_path == path:
			existing_source = source
			break
	if existing_source is not None:
		xml_name = source.find('name').text
		xml_path = source.find('path').text
		if source.find('thumbnail') is not None:
			xml_thumbnail = source.find('thumbnail').text
		else:
			xml_thumbnail = ''
		if xml_name == name and xml_path == path and xml_thumbnail == thumbnail:
			return False
		elif xml_name == name:
			source.find('path').text = path
			source.find('thumbnail').text = thumbnail
		elif xml_path == path:
			source.find('name').text = name
			source.find('thumbnail').text = thumbnail
		else:
			source.find('path').text = path
			source.find('name').text = name
	else:
		new_source = ET.SubElement(sources, 'source')
		new_name = ET.SubElement(new_source, 'name')
		new_name.text = name
		new_path = ET.SubElement(new_source, 'path')
		new_thumbnail = ET.SubElement(new_source, 'thumbnail')
		new_allowsharing = ET.SubElement(new_source, 'allowsharing')
		new_path.attrib['pathversion'] = '1'
		new_thumbnail.attrib['pathversion'] = '1'
		new_path.text = path
		new_thumbnail.text = thumbnail
		new_allowsharing.text = 'true'
	_indent_xml(root)
	tree.write(xml_file)
	return True

def _indent_xml(elem, level=0):
	i = '\n' + level*'\t'
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + '\t'
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			_indent_xml(elem, level+1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i

def _get_source_attr(xml_file, name, attr, type='video'):
	tree = ET.parse(xml_file)
	root = tree.getroot()
	sources = root.find(type)
	for source in sources.findall('source'):
		xml_name = source.find('name').text
		if xml_name == name:
			return source.find(attr).text
	return None

def _db_execute(db_name, command):
	databaseFile = _get_database(db_name)
	if not databaseFile: return False
	try: from sqlite3 import dbapi2
	except ImportError: from pysqlite2 import dbapi2
	dbcon = dbapi2.connect(databaseFile)
	dbcur = dbcon.cursor()
	dbcur.execute(command)
	dbcon.commit()
	dbcur.close ; dbcon.close()
	return True

def _get_database(db_name):
	from glob import glob
	path_db = 'special://profile/Database/%s' % db_name
	filelist = glob(transPath(path_db))
	if filelist: return filelist[-1]
	return None

def _remove_source_content(path):
	q = 'DELETE FROM path WHERE strPath LIKE "%{0}%"'.format(path)
	return _db_execute('MyVideos*.db', q)

def _set_source_content(content):
	q = 'INSERT OR REPLACE INTO path (strPath,strContent,strScraper,strHash,scanRecursive,useFolderNames,strSettings,noUpdate,exclude,dateAdded,idParentPath) VALUES '
	q += content
	return _db_execute('MyVideos*.db', q)

def clean_settings():
	def _make_content(dict_object):
		if kodi_version >= 18:
			content = '<settings version="2">'
			for item in dict_object:
				if item['id'] in active_settings:
					if 'default' in item and 'value' in item: content += '\n    <setting id="%s" default="%s">%s</setting>' % (item['id'], item['default'], item['value'])
					elif 'default' in item: content += '\n    <setting id="%s" default="%s"></setting>' % (item['id'], item['default'])
					elif 'value' in item: content += '\n    <setting id="%s">%s</setting>' % (item['id'], item['value'])
					else: content += '\n    <setting id="%s"></setting>'
				else: removed_settings.append(item)
		else:
			content = '<settings>'
			for item in dict_object:
				if item['id'] in active_settings:
					if 'value' in item: content += '\n    <setting id="%s" value="%s" />' % (item['id'], item['value'])
					else: content += '\n    <setting id="%s" value="" />' % item['id']
				else: removed_settings.append(item)
		content += '\n</settings>'
		return content
	kodi_version = getKodiVersion()
	for addon_id in ('plugin.video.venom', 'script.module.fenomscrapers'):
		try:
			removed_settings = []
			active_settings = []
			current_user_settings = []
			addon = xbmcaddon.Addon(id=addon_id)
			addon_name = addon.getAddonInfo('name')
			addon_dir = transPath(addon.getAddonInfo('path'))
			profile_dir = transPath(addon.getAddonInfo('profile'))
			active_settings_xml = joinPath(addon_dir, 'resources', 'settings.xml')
			root = ET.parse(active_settings_xml).getroot()
			for item in root.findall('./category/setting'):
				setting_id = item.get('id')
				if setting_id:
					active_settings.append(setting_id)
			settings_xml = joinPath(profile_dir, 'settings.xml')
			root = ET.parse(settings_xml).getroot()
			for item in root:
				dict_item = {}
				setting_id = item.get('id')
				setting_default = item.get('default')
				if kodi_version >= 18:
					setting_value = item.text
				else: setting_value = item.get('value')
				dict_item['id'] = setting_id
				if setting_value:
					dict_item['value'] = setting_value
				if setting_default:
					dict_item['default'] = setting_default
				current_user_settings.append(dict_item)
			new_content = _make_content(current_user_settings)
			nfo_file = openFile(settings_xml, 'w')
			nfo_file.write(new_content)
			nfo_file.close()
			sleep(200)
			notification(title=addon_name, message=lang(32084).format(str(len(removed_settings))))
		except:
			from resources.lib.modules import log_utils
			log_utils.error()
			notification(title=addon_name, message=32115)

def set_reuselanguageinvoker():
	if getKodiVersion() < 18:
		notification(message=32116)
		return
	try:
		addon_xml = joinPath(addonPath('plugin.video.venom'), 'addon.xml')
		tree = ET.parse(addon_xml)
		root = tree.getroot()
		for item in root.iter('reuselanguageinvoker'):
			current_value = str(item.text)
		if current_value:
			new_value = 'true' if current_value == 'false' else 'false'
			if not yesnoDialog(lang(33018) % (current_value, new_value), '', ''):
				return openSettings(query='12.6')
			if new_value == 'true':
				if not yesnoDialog(lang(33019), '', ''): return
			item.text = new_value
			hash_start = gen_file_hash(addon_xml)
			tree.write(addon_xml)
			hash_end = gen_file_hash(addon_xml)
			if hash_start != hash_end:
				setSetting('reuse.languageinvoker', new_value)
				okDialog(message='%s\n%s' % (lang(33017) % new_value, lang(33020)))
			else:
				return okDialog(message=33021)
			current_profile = infoLabel('system.profilename')
			execute('LoadProfile(%s)' % current_profile)
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def gen_file_hash(file):
	try:
		from hashlib import md5
		md5_hash = md5()
		with open(file, 'rb') as afile:
			buf = afile.read()
			md5_hash.update(buf)
			return md5_hash.hexdigest()
	except:
		from resources.lib.modules import log_utils
		log_utils.error()

def copy2clip(txt):
	from sys import platform as sys_platform
	platform = sys_platform
	if platform == "win32":
		try:
			from subprocess import check_call
			cmd = "echo " + txt.strip() + "|clip"
			return check_call(cmd, shell=True)
		except:
			from resources.lib.modules import log_utils
			log_utils.error('Failure to copy to clipboard')
	elif platform == "linux2":
		try:
			from subprocess import Popen, PIPE
			p = Popen(["xsel", "-pi"], stdin=PIPE)
			p.communicate(input=txt)
		except:
			from resources.lib.modules import log_utils
			log_utils.error('Failure to copy to clipboard')

def cleanPlot(plot):
	if not plot: return
	try:
		index = plot.rfind('See full summary')
		if index == -1: index = plot.rfind("It's publicly available on")
		if index >= 0: plot = plot[:index]
		plot = plot.strip()
		if re.match(r'[a-zA-Z\d]$', plot): plot += ' ...'
		return plot
	except:
		from resources.lib.modules import log_utils
		log_utils.error()