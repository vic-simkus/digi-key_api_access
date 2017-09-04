#!/usr/bin/env python

#===============================================================================
#
#  Copyright 2017 VIDAS SIMKUS
# 
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
# 
#        http://www.apache.org/licenses/LICENSE-2.0
# 
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
#===============================================================================

#
# The state and configuration is kept in a file ~/.digi-key_api_state.json
# The file is expected to be in a valid JSON format and contain the following minimal contents on first execution 
#
# Expected format:
#
# 	{
# 	"API_CLIENT_ID": "<MAGIC STRING>",
# 	"API_SECRET": "<SUPER SECRET MAGIC STRING>",
# 	"API_REDIRECT_URI": "https://localhost",
# 	"LOGIN_PASSWORD" : "<SUPER SECRET PASSWORD>",
# 	"LOGIN_NAME" : "<LESS SECRET LOGIN NAME>",
# 	"CONTEXT": { }
# 	}



import requests
import os.path
import json
import sys
import datetime
import argparse
import traceback

from HTMLParser import HTMLParser

class MyHTMLParser(HTMLParser):
	"""
	We use this to dig out the 'FORM' element out of the login form that we need to get past in order to get initial magic tokens.
	"""
	
	def __init__(self):
		HTMLParser.__init__(self)		
		self.form_action = None		
		return
	
	def handle_starttag(self, tag, attrs):		
		if tag.upper() != "FORM":
			return
		for a in attrs:
			if a[0] == 'action':
				self.form_action = a[1]

"""
The file we keep our application state, configuration parameters, and super secret magic strings in.
"""
STATE_FILE = ".digi-key_api_state.json"

"""
The file we're going to be caching parametric information in.
"""
PARAMETRICS_FILE = ".digi-key_api_parametrics.json"

"""
The Digi-Key search API endpoint
"""
API_PART_SEARCH_URI = "https://api.digikey.com/services/basicsearch/v1/search"

"""
The host that we shuffle magic strings through in order to get access to the API
"""
SSO_HOST = "https://sso.digikey.com"

"""
Application state/context
"""
GLOBAL_CONTEXT = None

PARAMETRICS_CACHE = {}

"""
If set by config file or command line parameters we output humorous debug information
"""
DEBUG_FLAG = False

CK_API_CLIENT_ID = "API_CLIENT_ID"
CK_API_SECRET = "API_SECRET"
CK_API_REDIRECT = "API_REDIRECT_URI"
CK_LOGIN_PASSWORD = "LOGIN_PASSWORD"
CK_LOGIN_NAME = "LOGIN_NAME"
CK_VERSION = "VERSION"
CK_DEBUG = "DEBUG"
CK_CONTEXT = "CONTEXT"
CK_CONTEXT_REF_TOK = "REFRESH_TOKEN"
CK_CONTEXT_ACC_TOK = "ACCESS_TOKEN"
CK_CONTEXT_EXP = "EXPIRES"
CK_CONTEXT_TS = "GEN_TIMESTAMP"

PC_ID = "Id"

DBG_IN_FILE = ""

CMD_ARGS = None

def get_context_file_name():
	"""
	Returns the complete path to the program state and configuration file.
	@return: Full path to the state and configuration file
	"""
	
	return os.path.join(os.path.expanduser("~"), STATE_FILE)

def get_parametrics_cache_file_name():
	"""
	Returns the complete path to the parametrics cache file.
	@return: Full path to the parametrics cache file
	"""
	
	return os.path.join(os.path.expanduser("~"), PARAMETRICS_FILE)

def save_parametrics_cache():
	"""
	Saves the parametrics cache to a JSON file.
	@return: Nothing
	"""
	
	global PARAMETRICS_CACHE
	
	try:
		with open(get_parametrics_cache_file_name(), "wt") as ctx_file:
			json.dump(PARAMETRICS_CACHE, ctx_file, indent=4, sort_keys=True)			
	except Exception, e:
		print >> sys.stderr, "Failed to save parametrics cache: " + str(e)
		
	return 


def save_global_context():
	"""
	Saves the global program sstate and configuration to a JSON file.
	@return: Nothing
	"""
	
	global GLOBAL_CONTEXT
	
	try:
		with open(get_context_file_name(), "wt") as ctx_file:
			json.dump(GLOBAL_CONTEXT, ctx_file, indent=4, sort_keys=True)			
	except Exception, e:
		print >> sys.stderr, "Failed to save save/configuration: " + str(e)
		print >> sys.stderr, "Current state: " + str(GLOBAL_CONTEXT)
		
	return 

def load_parametrics_cache():
	"""
	Loads the parametrics cache from a JSON file.
	@raise Exception: Passes along any exceptions from the 'open' call. 
	@return: Nothing
	"""
	
	global PARAMETRICS_CACHE
	
	try:
		with open(get_parametrics_cache_file_name(), "rt") as ctx_file:
			PARAMETRICS_CACHE = json.load(ctx_file)
	except Exception, e:
		# Sink it quietly
		pass
	
	return
		
def load_global_context():
	"""
	Loads the global program state and configuration from a JSON file.
	The function also performs basic sanity checking and will throw an exception if something is thought to be hinky. 
	@raise ValueError: Raises a ValueError if a required bit is missing in the file.  Should only be of concern during the first invocation.
	@raise Exception: Passes along any exceptions from the 'open' call. 
	@return: Nothing
	"""
	
	global GLOBAL_CONTEXT
	global CONFIG_VERSION
	global DEBUG_FLAG
	
	try:
		with open(get_context_file_name(), "rt") as ctx_file:
			GLOBAL_CONTEXT = json.load(ctx_file)
	except Exception, e:
		print >> sys.stderr, "Failed to parse state/cofig file: " + str(e)
		raise e
	
	if not GLOBAL_CONTEXT.has_key(CK_API_CLIENT_ID):
		raise ValueError("State/config file is missing the API_CLIENT_ID key.  This is part of the API configuration on the Digi-Key API portal.")
	
	if not GLOBAL_CONTEXT.has_key(CK_API_SECRET):
		raise ValueError("State/config file is missing the API_SECRET key.  This is part of the API configuration on the Digi-Key API portal.")
	
	if not GLOBAL_CONTEXT.has_key(CK_API_REDIRECT):
		raise ValueError("State/config file is missing the API_REDIRECT_URI key.  This is part of the API configuration on the Digi-Key API portal.")
	
	if not GLOBAL_CONTEXT.has_key(CK_LOGIN_NAME):
		raise ValueError("State/config file is missing the LOGIN_NAME key.  This is the login name of your Digi-Key account that you use to buy parts.")
		
	if not GLOBAL_CONTEXT.has_key(CK_LOGIN_PASSWORD):
		raise ValueError("State/config file is missing the LOGIN_PASSWORD key.  This is the password of your Digi-Key account that you use to buy parts.")
	
	
	if not GLOBAL_CONTEXT.has_key(CK_CONTEXT):
		raise ValueError("State/config file is missing the CONTEXT.  This means that your file is corrupt/incomplete.  Please read documentation in this source file.")
	
	
	if not GLOBAL_CONTEXT.has_key(CK_DEBUG):
		GLOBAL_CONTEXT[CK_DEBUG] = "FALSE"
	
	if GLOBAL_CONTEXT[CK_DEBUG] == "TRUE":
		DEBUG_FLAG = True
	else:
		DEBUG_FLAG = False
	
	if DEBUG_FLAG:
		print "Successfully loaded application state/config."
		
	return

	
def create_api_auth_refresh_parms(_client_id, _api_secret, _refresh_token):
	"""
	Creates the request parameters necessary to refresh an authentication token.
	@param _client_id: Client ID magic string from the API setup.
	@param _api_secret: Super secret API secret from the API setup that you are never allowed to see past the initial creation of the application.
	@param _refresh_token: Last valid refresh token.  This is an important magic string.  This is usually stored in the application state/configuration.  
	@return: A map of parameters that may be useful in refreshing the auth token.
	"""
	
	ret = {}
	ret["refresh_token"] = _refresh_token
	ret["grant_type"] = "refresh_token"
	ret["client_id"] = _client_id
	ret["client_secret"] = _api_secret
	
	return ret

def create_api_call_headers(_client_id, _auth_token):
	"""
	Creates the necessary headers to invoke an API call.
	@param _client_id: Client ID magic string.
	@param _auth_token: Authentication token magic string.  This is usually stored in the application state/configuration.
	@return: A map of headers.
	"""
	
	ret = {}
	ret["accept"] = "application/json"
	ret["x-digikey-locale-language"] = "en"
	ret["x-digikey-locale-currency"] = "usd"
	ret["authorization"] = _auth_token
	ret["content-type"] = "application/json"
	ret["x-ibm-client-id"] = _client_id
	
	return ret

def create_api_part_search(_id, _qty):
	"""
	Creates the map containing the pertinent part search parameters.
	@param _id: Digi-Key part ID.
	@param _qty: Part quantity.  Should probably be more than zero. 
	@return: A map of the parameters.
	"""
	ret = {}
	ret["PartNumber"] = _id
	ret["Quantity"] = _qty
	
	return ret

def create_auth_magic_url_one():
	"""
	Cobbles together a URL for the first step of the authentication magic
	@see: https://api-portal.digikey.com/node/188
	@return: A URL with the magic bits specified in the application configuration
	"""
	
	return SSO_HOST + "/as/authorization.oauth2?response_type=code&client_id=" + GLOBAL_CONTEXT[CK_API_CLIENT_ID] + "&redirect_uri=" + GLOBAL_CONTEXT[CK_API_REDIRECT]

def create_auth_magic_url_two(_code):
	"""
	Cobbles together a URL for the second step of the authentication magic.
	@see: https://api-portal.digikey.com/node/188
	@return: A URL with the magic bits specified in the application configuration combined with magic bits produced by authentication magic step one.
	"""
	
	return SSO_HOST + "/as/token.oauth2?grant_type=authorization_code&code=" + _code + "&client_id=" + GLOBAL_CONTEXT[CK_API_CLIENT_ID] + "&client_secret=" + GLOBAL_CONTEXT[CK_API_SECRET] + "&redirect_uri=" + GLOBAL_CONTEXT[CK_API_REDIRECT] 

def invoke_auth_magic_one():
	"""
	Performs the first step of the authentication magic.
	@see: https://api-portal.digikey.com/node/188
	@return: Magic code to be used in step two of the authentication.
	"""
	
	if DEBUG_FLAG:
		print "Trying to perform first stage of magic: invoking a redirect so user has chance to approve us."
	
	https_session = requests.Session()
	magic_string = create_auth_magic_url_one()	
	r = https_session.post(magic_string)
		
	if r.status_code != 200:
		print >> sys.stderr, ("*" * 10) + " ERROR OUTPUT START " + ("*" * 10)
		print >> sys.stderr, "Failed in the first sub-step of the authentication magic step one."
		print >> sys.stderr, "Response code: " + r.status_code
		dump_response_headers(r, sys.stderr)
		print >> sys.stderr, r.text
		print >> sys.stderr, ("*" * 10) + " ERROR OUTPUT END " + ("*" * 10)
		raise RuntimeError("Failed to get new tokens in authentication magic step one.  See program output for details.")
			
	html_parser = MyHTMLParser()
	html_parser.feed(r.text)	
	
	if DEBUG_FLAG:
		print "Trying to perform second stage of magic: fudging login via form."
		
	https_session.headers.update({"Referer": magic_string, "Content-Type": "application/x-www-form-urlencoded"})
	
	r = https_session.post(SSO_HOST + html_parser.form_action, data={"pf.username": GLOBAL_CONTEXT[CK_LOGIN_NAME], "pf.pass":GLOBAL_CONTEXT[CK_LOGIN_PASSWORD], "pf.ok":"clicked"}, allow_redirects=False)
	
	#
	# XXX I guess here there could be another response.  If the session is expired there might be another clickthrough dialog.
	#
	if r.status_code != 302:
		print >> sys.stderr, ("*" * 10) + " ERROR OUTPUT START " + ("*" * 10)
		print >> sys.stderr, "Failed in the second sub-step of the authentication magic step one."
		print >> sys.stderr, "Response code: " + r.status_code
		dump_response_headers(r, sys.stderr)
		print >> sys.stderr, r.text
		print >> sys.stderr, ("*" * 10) + " ERROR OUTPUT END " + ("*" * 10)
		raise RuntimeError("Failed to get new tokens in authentication magic step one.  See program output for details.")
	
	magic_code = None
	
	try:
		#
		# What do you mean "robust"?
		#
		# On success the redirect header will look something like this:
		# Location: https://localhost?code=<MAGIC BEANS>
		# 
		# We extract the code parameter because that's really all we care about
		#
		
		magic_code = r.headers["Location"].split("?")[1].split("=")[1]
	except Exception, e:
		print >> sys.stderr, "Failed to extract code from the 'Location' response header: " + str(e)
		dump_response_headers(r, sys.stderr)
		raise RuntimeError("Failed to get new tokens in authentication magic step one.  See program output for details.")		
		
	if magic_code is None:
		raise RuntimeError("Failed to get new tokens in authentication magic step one.  Magic code seems to be None even though everything went well.")
	
	if DEBUG_FLAG:
		print "If we got this far we probably have a new code."
		
	return magic_code	
	
def invoke_auth_magic_two(_code):
	"""
	Performs the second step of the authentication magic.  Here we get the real-real authentication token and a refresh token.
	@param _code: Magic code from step one of the authentication process. 
	@see: https://api-portal.digikey.com/node/188
	
	"""
	if DEBUG_FLAG:
		print "Trying to collect more magic beans."
		
	global GLOBAL_CONTEXT
	
	magic_string = create_auth_magic_url_two(_code)	
	r = requests.post(magic_string)	
	
	if r.status_code < 200 or r.status_code >= 300:
		print >> sys.stderr, "Failed to get new tokens in authentication magic step two"
		print >> sys.stderr, "Response code: " + r.status_code
		dump_response_headers(r, sys.stderr)
		raise RuntimeError("Failed to get new tokens in authentication magic step two.  See program output for details.")
		
	d = json.loads(r.text)
	
	GLOBAL_CONTEXT[CK_CONTEXT][CK_CONTEXT_ACC_TOK] = d["access_token"] 
	GLOBAL_CONTEXT[CK_CONTEXT][CK_CONTEXT_REF_TOK] = d["refresh_token"]
	
	if DEBUG_FLAG:
		print "We should have enough magic beans to grow the bean stalk so that we can climb INTO THE CLOUD."
		
	return 

def new_auth():
	"""
	Performs the new authentication song and dance.  Waves the dead chicken in the air in just the right way.
	@see: https://api-portal.digikey.com/node/188
	"""
	magic_code = invoke_auth_magic_one()
	invoke_auth_magic_two(magic_code)
	
	return
	

def refresh_auth_token():
	"""
	Refreshes the authentication token.  This should be done less than every 24 hours unless you want to jump through hoops in getting another auth token.
	All of the necessary information is retreived from the application state/configuration.
	@return: Nothing
	"""
	
	global GLOBAL_CONTEXT
	
	if CK_CONTEXT_REF_TOK not in GLOBAL_CONTEXT[CK_CONTEXT]:
		# We don't have a refresh token so lets be robust and make one!
		if DEBUG_FLAG:
			print CK_CONTEXT_REF_TOK + " is missing.  Will try to perform new authentication magic."
			return new_auth()
	else:
		if DEBUG_FLAG:
			print CK_CONTEXT_REF_TOK + " exists."
			
	d = create_api_auth_refresh_parms(GLOBAL_CONTEXT[CK_API_CLIENT_ID], GLOBAL_CONTEXT[CK_API_SECRET], GLOBAL_CONTEXT[CK_CONTEXT][CK_CONTEXT_REF_TOK])
	r = requests.post(SSO_HOST + "/as/token.oauth2", data=d)

	jo = r.json();
	
	if r.status_code >= 200 and r.status_code < 300:
		# Everything honky-dory		
		GLOBAL_CONTEXT[CK_CONTEXT][CK_CONTEXT_REF_TOK] = jo["refresh_token"]
		GLOBAL_CONTEXT[CK_CONTEXT][CK_CONTEXT_ACC_TOK] = jo["access_token"]
		GLOBAL_CONTEXT[CK_CONTEXT][CK_CONTEXT_EXP] = jo["expires_in"]
		GLOBAL_CONTEXT[CK_CONTEXT][CK_CONTEXT_TS] = datetime.datetime.now().isoformat()
	else:
		# Uh oh number 2
		print >> sys.stderr, "Failed to refresh token: " + str(jo)
		raise RuntimeError("Failed to refresh token: " + str(jo))
	
	return 

def dump_response_headers(r, _target=sys.stdout):
	"""
	Dumps the response headers in a relatively useful fasion
	@param r: Response object
	@param _target: Where to dump the information.  Should be a file descriptor type object. 
	"""
	
	print >> _target, "\n" + ("*" * 10) + " RESPONSE HEADERS START " + ("*" * 10)
	
	for h in r.headers.keys():
		print >> _target, h + ": " + r.headers[h]	
	print >> _target, ("*" * 10) + " RESPONSE HEADERS END " + ("*" * 10) + "\n"
	
	return 
					
def get_part_data(_id, _qty):
	"""
	@raise RuntimeError: Raises a RuntimeError if the response code is not 2xx.  The search can fail for any number of reasons including an invalid part number.  A malformed request, auth error, an invalid search, they all return code 4xx. 
	@return: Search results in a fully formed Python object.
	"""
	
	head = create_api_call_headers(GLOBAL_CONTEXT[CK_API_CLIENT_ID], GLOBAL_CONTEXT[CK_CONTEXT][CK_CONTEXT_ACC_TOK])	

	payload = json.dumps(create_api_part_search(_id.strip(), int(_qty)))
		
	r = requests.post(API_PART_SEARCH_URI, data=payload, headers=head)
	
	if DEBUG_FLAG: 
		dump_response_headers(r)
		
	
	if r.status_code < 200 or r.status_code >= 300:
		raise RuntimeError("Remote call to search for parts failed for some reason.  Don't know why. Code: " + str(r.status_code) + ", Body: " + r.text)	  
		
	body = json.loads(r.text)
	
	if DEBUG_FLAG:
		print "\n" + ("*" * 10) + " RESULT START " + ("*" * 10)
		print json.dumps(body, indent=4)  
		print ("*" * 10) + " RESULT END " + ("*" * 10) + "\n"
	
	return body

def search_for_part(_part, _count, _compact):
	d = None
	
	ind = 2
	seps = (', ', ': ')
	
	if _compact:
		ind = None
		seps = (',', ':')
	
	try:
		d = get_part_data(_part, _count)
	except RuntimeError:
		#
		# This could be thrown by anything and everything.  We'll assume that just means that no results were found.
		#
		return json.dumps(None)
	
	global PARAMETRICS_CACHE
	for i in d["Parts"][0]["ParametricData"]:
		parm_text = i["Text"]
		parm_id = str(i["Id"])
		
		if parm_id not in PARAMETRICS_CACHE.keys():
			PARAMETRICS_CACHE[parm_id] = parm_text
	
	if len(d["Parts"]) == 1:
		d = d["Parts"][0]
	
	if CMD_ARGS.rmMl:
		d.pop("MediaLinks",None)
	if CMD_ARGS.rmPp:
		d.pop("PrimaryPhoto",None)
	if CMD_ARGS.rmPd:
		d.pop("PrimaryDatasheet",None)
	
	return json.dumps(d, indent=ind, ensure_ascii=True, separators=seps)
	
def dbg_1():	
	pass

def setup_argparse():
	parser = argparse.ArgumentParser()
	
	parser.add_argument("-d", action="store_true", help="Disable debug output even if enabled in state/config file.  Takes precedence over -D.")
	parser.add_argument("-D", action="store_true", help="Enable debug output even if disabled in state/config file.")
	parser.add_argument("-P", help="Parameter.  Usage depends on context.")
	parser.add_argument("-C", help="Part count. Used when searching for parts.  If omitted defaults to 1.", default=1, type=int)
	parser.add_argument("-Jc", action="store_true", help="Output search results in compact JSON.")
	parser.add_argument("-rmMl", action="store_true", help="Remove MediaLinks section from the results.")
	parser.add_argument("-rmPp", action="store_true", help="Remove PrimaryPhoto section from the results.")
	parser.add_argument("-rmPd", action="store_true", help="Remove PrimaryDatasheet section from the results.")
	parser.add_argument("CMD", choices=["INVOKE_M1", "INVOKE_M2", "STR_M1", "STR_M2", "AUTH_NEW", "AUTH_REFRESH", "PART_SEARCH", "DBG1"], help="Main command.")
	parser.add_argument("-dbgInFile", help="Input file for debug purposes.")

	return parser

def process_commands():
	global DEBUG_FLAG
	global DBG_IN_FILE
	global CMD_ARGS
	
	parser = setup_argparse()	
	args = parser.parse_args()
	CMD_ARGS = args
	
	if args.D:
		DEBUG_FLAG = True
				
	if args.d:
		DEBUG_FLAG = False	
	
	if DEBUG_FLAG == True:
		print "Debug output is enabled."
		
	if args.dbgInFile:		
		DBG_IN_FILE = args.dbgInFile 
	
	if args.CMD == "AUTH_REFRESH":
		refresh_auth_token()
	elif args.CMD == "AUTH_NEW":
		new_auth()		
	elif args.CMD == "STR_M1":
		print create_auth_magic_url_one()
	elif args.CMD == "STR_M2":
		if args.P == None:
			print >> sys.stderr, "Must specify the 'code' that was provided by the site in response to magic string 1."
		else:
			print create_auth_magic_url_two(args.P)
	elif args.CMD == "INVOKE_M1":
		print invoke_auth_magic_one()
	elif args.CMD == "INVOKE_M2":
		if args.P == None:
			print >> sys.stderr, "Must specify the 'code' that was provided by the site in response to magic string 1."
		else:
			invoke_auth_magic_two(args.P)			
	elif args.CMD == "PART_SEARCH":
		if args.P == None:
			print >> sys.stderr, "Must specify Digi-Key part number using the -P parameter when the command is PART_SEARCH."
		else:
			print search_for_part(args.P, args.C, args.Jc)
	elif args.CMD == "DBG1":
		dbg_1()
	else:
		raise RuntimeError("Invalid command specified.")		
	

def main():		
	#
	# We always load the state/config
	#
	try:
		load_global_context();
	except ValueError, e:
		print >> sys.stderr, "Failed to load state/config file: " + str(e)
		return
	
	load_parametrics_cache()
	#
	# Do magic
	#
	try:
		process_commands()
	except Exception, e:
		#
		# Magic failed
		#
		
		print >> sys.stderr, "Something went boom while processing magic: " + str(e)
		traceback.print_exc()
		exit(-1)
	
	#
	# We only save the state if nothing threw and exception
	#
	try:
		save_global_context();
	except ValueError, e:
		print >> sys.stderr, "Failed to load state/config file: " + str(e)
		return
	
	save_parametrics_cache()

if __name__ == '__main__':
	main()

