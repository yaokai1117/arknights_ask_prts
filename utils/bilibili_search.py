import re

from bilibili_api import search
from typing import List


MAX_NUMBER_OF_RESUTLS = 5
HTML_TAGS = re.compile('<.*?>')
BILI_SEARCH_RESPONSE_HEADER = '在哔哩哔哩上搜索[{keywords}]的结果：\n{results}'
NO_IDEA_RESPONSE = '不知道诶。。。'


async def bilibili_search(keywords:str) -> str:
    try:
        search_response = await search.search_by_type(keywords, search_type=search.SearchObjectType.VIDEO,
                                                      order_type=search.OrderVideo.TOTALRANK, page=1, debug_param_func=print)
    except Exception as e:
        bili_result = NO_IDEA_RESPONSE
    results: List[str] = []
    for search_result in search_response['result'][:MAX_NUMBER_OF_RESUTLS]:
        results.append(re.sub(HTML_TAGS, '', search_result['title']) + ' ' + search_result['arcurl'] + '\n')
    raw_result = '\n'.join(results)
    bili_result = BILI_SEARCH_RESPONSE_HEADER.format(keywords=keywords, results=raw_result)
    return bili_result

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(bilibili_search('领主的攻击范围是什么样的')))
