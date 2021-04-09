###
# Copyright (c) 2021, nvz <https://github.com/enveezee>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###
from bs4 import BeautifulSoup
from sys import argv
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.utils as utils
import supybot.ircdb as ircdb
import supybot.log as log
import supybot.conf as conf

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("DuckIt")
except ImportError:
    _ = lambda x: x

DEFAULT_USER_AGENT='Mozilla/5.0'

# Extrapolate matching information should the format of the site change.
match = {
    # Main search results body identifier.
    'searchResults': {'id': 'links'},
    # Individual search results identifier.
    'result': {'class': 'links_main links_deep result__body'},
    # Link and description identifier.
    'link': {'class': 'result__snippet'}
}

# Plain HTML Search URL.
searchURL = 'https://html.duckduckgo.com/html/?q='

class DuckIt(callbacks.Plugin):
    '''Return search results from DuckDuckGo, if you can't DuckIt...'''
    def __init__(self, irc):
        self.__parent = super(DuckIt, self)
        self.__parent.__init__(irc)


    def request(self, url, headers=None):
        # Form request for url.
        request = Request(url)

        # Add headers if supplied, or defaults.
        if headers:
            # Supplied headers.
            for header in headers:
                request.add_header(header, headers[header])
        else:
            # Default headers.
            request.add_header('User-Agent', DEFAULT_USER_AGENT)

        try:
            response = urlopen(request)
        except HTTPError as e:
            # e.code, HTTP Error code.
            #   404
            # e.msg, HTTP Error message.
            #   Not Found
            # e.hdr, HTTP Response headers.
            #   Content-Type: text/html; charset=UTF-8
            #   Referrer-Policy: no-referrer
            #   Content-Length: 1567
            #   Date: Thu, 01 Apr 2021 04:31:31 GMT
            #   Connection: close
            # e.fp, pointer to the http.client.HTTPResponse object.
            code = e.code      # HTTPError code
            error = e.msg      # HTTPError message
            headers = e.hdr    # HTTPError headers
            response = e.fp   # HTTPResponse object
            return e

        # Set HTTPResponse status code.
        code = response.status

        # Set error to None, to know we succeeded in making request
        error = None

        # Set HTTPResponse headers.
        headers = dict(response.getheaders())

        if url != response.url:
            redirect = True

        return response


    def makeSoup(self, html):
        try:
            soup = BeautifulSoup(html, 'lxml')
            return soup
        except Exception as e:
            print(e)
            return ''


    def parseLink(self, link):
        url = urlparse(link)
        link = unquote(url.query[5:])
        return link


    def search(self, query):
        # Quote the query string.
        query = quote(''.join(query))

        # Make search request.
        response = self.request(f'{searchURL}{query}')

        # Parse response html.
        soup = self.makeSoup(response)

        # Select the <div id='links'>.
        searchResults = soup.find('div', match['searchResults'])

        # Parse out each search result from the <div id='links'>
        searchResults = searchResults.find_all('div', match['result'])


        results = []
        # Parse descritpion, link from the searchResults list.
        for result in searchResults:
            anch = result.find('a', match['link'])
            desc = anch.text
            link = self.parseLink(anch['href'])
            url = urlparse(link)
            if 'duckduckgo.com' in url.netloc:
                continue
            results.append({'desc': desc, 'link':link})

        return results


    def di(self, irc, msg, args, query):
        '''di <query>
        
        Search the web with DuckDuckGo, if you can't DuckIt...
        '''
        searchResults = self.search(query)
        results = []
        for result in searchResults:
            results.append(f"{result['link']} {result['desc']}")
        irc.reply(results, prefixNick=False)

    di = wrap(di, ['text'])


Class = DuckIt
