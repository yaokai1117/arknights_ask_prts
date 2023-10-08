import re

from bilibili_api import search
from typing import List


MAX_NUMBER_OF_RESUTLS = 5
HTML_TAGS = re.compile('<.*?>')

async def bilibili_search(keywords: List[str]) -> str:
    search_response = await search.search_by_type(' '.join(keywords), search_type=search.SearchObjectType.VIDEO,
                                       order_type=search.OrderVideo.TOTALRANK, page=1, debug_param_func=print)
    results: List[str] = []
    for search_result in search_response['result'][:MAX_NUMBER_OF_RESUTLS]:
        results.append(re.sub(HTML_TAGS, '', search_result['title']) + ' ' + search_result['arcurl'] + '\n')
    return '\n'.join(results)


if __name__ == '__main__':
    import asyncio
    print(asyncio.run(bilibili_search(['领主的攻击范围是什么样的'])))