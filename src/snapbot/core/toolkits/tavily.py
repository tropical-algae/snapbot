from tavily import TavilyClient

from snapbot.common.configs import settings

tavily_client = TavilyClient(api_key=settings.toolkits.tavily_key)
