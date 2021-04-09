"""
DuckIt - Get search results from DuckDuckGo. If you can't DuckIt... 
"""

import supybot
import supybot.world as world

__version__ = "0.1"

__author__ = supybot.Author("nvz", "enveezee", "https://github.com/enveezee")
__maintainer__ = getattr(
    supybot.authors,
    "nvz",
    supybot.Author("nvz", "enveezee", "https://github.com/enveezee"),
)

__contributors__ = {}

__url__ = "https://github.com/enveezee/"

from . import config
from . import plugin
from imp import reload

reload(plugin)
reload(config)

if world.testing:
    from . import test

Class = plugin.Class
configure = config.configure
