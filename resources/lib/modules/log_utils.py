# -*- coding: utf-8 -*-
"""
	Venom Add-on
"""

from datetime import datetime
import inspect
from string import printable
import unicodedata
import xbmc
from resources.lib.modules import control
from resources.lib.modules import py_tools

# # only prints when venom logging set to "Debug" (LOGINFO ads to list if Leia(18))
LOGDEBUG = xbmc.LOGDEBUG #0
# ###--from here down methods print when Venom logging set to "Normal".
LOGINFO = xbmc.LOGINFO #1 (doesn't print unless Venom logging set to "Debug" in Leia(18))
LOGNOTICE = xbmc.LOGNOTICE if control.getKodiVersion() < 19 else xbmc.LOGINFO #(2 in 18, deprecated in 19 use LOGINFO(1))
LOGWARNING = xbmc.LOGWARNING #(3 in 18, 2 in 19)
LOGERROR = xbmc.LOGERROR #(4 in 18, 3 in 19)
LOGSEVERE = xbmc.LOGSEVERE if control.getKodiVersion() < 19 else xbmc.LOGFATAL #(5 in 18, deprecated in 19 use LOGFATAL(4))
LOGFATAL = xbmc.LOGFATAL #(6 in 18, 4 in 19)
LOGNONE = xbmc.LOGNONE #(7 in 18, 5 in 19)-not used but listed for int value
if py_tools.isPY2:
	debug_list = ['DEBUG', 'INFO', 'NOTICE', 'WARNING', 'ERROR', 'SEVERE', 'FATAL']
	from io import open #py2 open() does not support encoding param
else:
	debug_list = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL']
DEBUGPREFIX = '[COLOR red][ Venom: %s ][/COLOR]'
LOGPATH = control.transPath('special://logpath/')


def log(msg, caller=None, level=LOGNOTICE):
	debug_enabled = control.setting('debug.enabled') == 'true'
	if not debug_enabled: return
	debug_level = control.setting('debug.level')
	if level == LOGDEBUG and debug_level != '1': return
	debug_location = control.setting('debug.location')
	if isinstance(msg, int): msg = control.lang(msg) # for strings.po translations
	try:
		if py_tools.isPY3:
			if not msg.isprintable(): # ex. "\n" is not a printable character so returns False on those sort of cases
				msg = '%s (NORMALIZED by log_utils.log())' % normalize(msg)
			if isinstance(msg, py_tools.binary_type):
				msg = '%s (ENCODED by log_utils.log())' % (py_tools.ensure_str(msg, errors='replace'))
		else:
			if not isprintable(msg): # if not all(c in printable for c in msg): # .isprintable() not available in py2
				msg = normalize(msg)
			if isinstance(msg, py_tools.binary_type):
				msg = '%s (ENCODED by log_utils.log())' % (py_tools.ensure_text(msg))

		if caller is not None and level != LOGERROR:
			func = inspect.currentframe().f_back.f_code
			line_number = inspect.currentframe().f_back.f_lineno
			caller = "%s.%s()" % (caller, func.co_name)
			msg = 'From func name: %s Line # :%s\n                       msg : %s' % (caller, line_number, msg)
		elif caller is not None and level == LOGERROR:
			msg = 'From func name: %s.%s() Line # :%s\n                       msg : %s' % (caller[0], caller[1], caller[2], msg)

		if debug_location == '1':
			log_file = control.joinPath(LOGPATH, 'venom.log')
			if not control.existsPath(log_file):
				f = open(log_file, 'w')
				f.close()
			with open(log_file, 'a', encoding='utf-8') as f:
				line = '[%s %s] %s: %s' % (datetime.now().date(), str(datetime.now().time())[:8], DEBUGPREFIX % debug_list[level], msg)
				f.write(line.rstrip('\r\n') + '\n')
				# f.writelines([line1, line2]) ## maybe an option for the 2 lines without using "\n"
		else:
			xbmc.log('%s: %s' % (DEBUGPREFIX % debug_list[level], msg, level))
	except Exception as e:
		import traceback
		traceback.print_exc()
		xbmc.log('[ plugin.video.venom ] log_utils.log() Logging Failure: %s' % (e), LOGERROR)

def error(message=None, exception=True):
	try:
		import sys
		if exception:
			type, value, traceback = sys.exc_info()
			addon = 'plugin.video.venom'
			filename = (traceback.tb_frame.f_code.co_filename)
			filename = filename.split(addon)[1]
			name = traceback.tb_frame.f_code.co_name
			linenumber = traceback.tb_lineno
			errortype = type.__name__
			if py_tools.isPY3: errormessage = value
			else: errormessage = value.message or value # sometimes value.message is null while value is not
			if str(errormessage) == '': return
			if message: message += ' -> '
			else: message = ''
			message += str(errortype) + ' -> ' + str(errormessage)
			caller = [filename, name, linenumber]
		else:
			caller = None
		del(type, value, traceback) # So we don't leave our local labels/objects dangling
		log(msg=message, caller=caller, level=LOGERROR)
	except Exception as e:
		xbmc.log('[ plugin.video.venom ] log_utils.error() Logging Failure: %s' % (e), LOGERROR)

def isprintable(s, codec='utf8'):
	try: s.decode(codec)
	except UnicodeDecodeError: return False
	else: return True

def normalize(title):
	try:
		return ''.join(c for c in unicodedata.normalize('NFKD', py_tools.ensure_text(py_tools.ensure_str(title))) if unicodedata.category(c) != 'Mn')
	except:
		error()
		return title

def strip_non_ascii_and_unprintable(text):
	try:
		result = ''.join(char for char in text if char in printable)
		return result.encode('ascii', errors='ignore').decode('ascii', errors='ignore')
	except:
		error()
		return text