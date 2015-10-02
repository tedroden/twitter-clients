#!/usr/bin/env python
#

import os, logging
import webapp2
import jinja2
import twitter
from requests_oauthlib import OAuth1Session
import settings # set your CONSUMER_KEY and CONSUMER_SECRET in there.

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def get_statuses(token, secret):
    api = twitter.Api(consumer_key=settings.CONSUMER_KEY,
                      consumer_secret=settings.CONSUMER_SECRET,
                      access_token_key=token,
                      access_token_secret=secret,
    )
    page = 0
    clients = {}
    max_id = 0
    while page < 3:
        page += 1
        for x in api.GetHomeTimeline(count=200, max_id=max_id):
            max_id = x.id
            if x.source not in clients.keys():
                clients[x.source] = 0
            clients[x.source] += 1
    sortable = []
    for x in clients.keys():
        sortable.append({ 'source': x,
                          'cnt': clients.get(x) })
    sortable = sorted(sortable, key=lambda x: x['cnt'])
    return reversed(sortable)
    
class MainHandler(webapp2.RequestHandler):
    def get(self):
        callback_url = "https://" + self.request.host + "/callback"
        oauth_client = OAuth1Session(settings.CONSUMER_KEY, client_secret=settings.CONSUMER_SECRET, callback_uri=callback_url)
        
        values = { 'ok': True }

        if self.request.get('oauth_token'):
            secret = self.request.get('oauth_token_secret')
            logging.info(self.request.uri)
            oauth_client.parse_authorization_response(self.request.uri)
            oauth_token = oauth_client.fetch_access_token(ACCESS_TOKEN_URL, self.request.get('oauth_verifier'))
            values['results'] = get_statuses(oauth_token.get('oauth_token'), oauth_token.get('oauth_token_secret'))
            logging.info(values)
        else:
            try: 
                resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
                self.response.set_cookie("oauth_token_secret",value=resp.get("oauth_token_secret"), path="/")
                print resp
                url = oauth_client.authorization_url(AUTHORIZATION_URL, oauth_callback=callback_url)
                values['auth_url'] = url
            except:
                logging.exception("Something went wrong")
                values['ok'] = False

        template = JINJA_ENVIRONMENT.get_template('page.html')
        self.response.write(template.render(values))
        

class CallbackHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("ok=true")

app = webapp2.WSGIApplication([
    ('/.*?', MainHandler),

], debug=True)
