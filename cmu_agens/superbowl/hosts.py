import os
from ips.load_ips import *

commercial_hosts = {
    'netflix':'netflix753.as.nflximg.com.edgesuite.net',
    'cbssports':'www.cbssports.com',
    'doubleclick': 'ad.doubleclick.net',
    'doubleclick-stat': 'stats.l.doubleclick.net',
    'google-tag-manager':'www.googletagmanager.com',
    'papajohns':'www.papajohns.com',
    'lube':'quakersteakandlube.alohaorderonline.com'
}

commercial_urls = {
    'cbssport':'http://www.cbssports.com/nfl/superbowl/live/player',
    'pizzahut':'https://order.pizzahut.com/home',
    'lube':'https://quakersteakandlube.alohaorderonline.com/',
    'papajohns':'https://www.papajohns.com/',
    'twSuperbowl':'https://twitter.com/SuperBowl',
    'twHashSuperbowl':'https://twitter.com/search?q=%23superbowl'
}

cache_ips, cache_urls = load_cache_ips()