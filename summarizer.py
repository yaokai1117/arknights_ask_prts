import json

from langchain.chains.base import Chain
from langchain_core.callbacks import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.few_shot import FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI

from data_model import LogEntry, Message, SessionStatus
from typing import List, Dict, Any, Optional, ClassVar

QUESTION_1 = '请介绍新干员仇白'
QUERIES_1 = ['{\n\
  characters(filter: {name: "仇白"}) {\n\
    name\n\
    description\n\
    tagList\n\
    position\n\
    profession\n\
    subProfession\n\
    traits\n\
    rarity\n\
    skills(index: null) {\n\
      skillName\n\
      levels(index: -1) {\n\
        description\n\
      }\n\
    }\n\
    phases(index: -1) {\n\
      attributesKeyFrames(index: -1) {\n\
        level\n\
        maxHp\n\
        atk\n\
        physicalDef\n\
        magicResistance\n\
      }\n\
    }\n\
    talents\n\
  }\n\
}']
QUERY_RESULTS_1 = [
    {
        "data": {
            "characters": [
                {
                    "name": "仇白",
                    "description": "行走江湖的炎国剑客仇白，为不平之事停下脚步。\n她出生时正遇一场大雪，这本是一场难得的相逢。",
                    "tagList": [
                        "输出",
                        "控场"
                    ],
                    "position": "近战",
                    "profession": "近卫",
                    "subProfession": "领主",
                    "traits": "可以进行远程攻击，但此时攻击力降低至80%",
                    "rarity": 6,
                    "skills": [
                        {
                            "skillName": "留羽",
                            "levels": [
                              {
                                  "description": "下次攻击使目标束缚3秒，该次束缚结束时对目标和附近的所有敌人造成相当于攻击力300%的法术伤害"
                              }
                            ]
                        },
                        {
                            "skillName": "承影",
                            "levels": [
                                {
                                    "description": "对前方范围内的地面敌人造成攻击力300%的法术伤害；攻击范围改变，攻击力+140%，攻击范围内的地面敌人停顿；技能结束时对范围内的地面敌人造成攻击力300%的物理伤害"
                                }
                            ]
                        },
                        {
                            "skillName": "问雪",
                            "levels": [
                                {
                                    "description": "攻击范围扩大，攻击力+55%，伤害类型变为法术，额外攻击2个目标，第一天赋的伤害提升至2倍，远程攻击不再降低伤害，每次攻击使自身攻击速度+13（最多叠加8次）"
                                }
                            ]
                        }
                    ],
                    "phases": [
                        {
                            "attributesKeyFrames": [
                                {
                                    "level": 90,
                                    "maxHp": 2480,
                                    "atk": 718,
                                    "physicalDef": 402,
                                    "magicResistance": 10
                                }
                            ]
                        }
                    ],
                    "talents": [
                        "入隙: 攻击处于停顿、束缚的敌人时，额外造成相当于攻击力43%（+3%）的法术伤害",
                        "落英: 攻击时有23%（+3%）的几率使目标束缚1.5秒"
                    ],
                }
            ]
        }
    }
]
THOUGHTS_1 = '根据游戏数据的查询结果，可以列出干员仇白的属性，技能，在最高精英阶段时的数值（生命值，攻击力）等等。'
FINAL_RESPONSE_1 = '仇白\n\
描述：行走江湖的炎国剑客仇白，为不平之事停下脚步。她出生时正遇一场大雪，这本是一场难得的相逢。\n\
标签：输出，控场 位置：近战\n\
职业：近卫　分支职业：领主 特性：可以进行远程攻击，但此时攻击力降低至80%\n\
稀有度：六星\n\
技能一：留羽 下次攻击使目标束缚3秒，该次束缚结束时对目标和附近的所有敌人造成相当于攻击力300%的法术伤害\n\
技能二：承影 对前方范围内的地面敌人造成攻击力300%的法术伤害；攻击范围改变，攻击力+140%，攻击范围内的地面敌人停顿；技能结束时对范围内的地面敌人造成攻击力300%的物理伤害\n\
技能三：问雪 攻击范围扩大，攻击力+55%，伤害类型变为法术，额外攻击2个目标，第一天赋的伤害提升至2倍，远程攻击不再降低伤害，每次攻击使自身攻击速度+13（最多叠加8次）\n\
最高精英等级时的数值：\n\
等级：90\n\
生命值：2480\n\
攻击力：718\n\
防御力：402\n\
法术抗性：10\n\
天赋一：入隙: 攻击处于停顿、束缚的敌人时，额外造成相当于攻击力43%（+3%）的法术伤害\n\
天赋二：落英: 攻击时有23%（+3%）的几率使目标束缚1.5秒\n\
'

QUESTION_2 = '黄昏专三的专精材料是什么'
QUERIES_2 = '[{\n\
  skill(filter: {skillName: "黄昏"}) {\n\
    skillRequirements {\n\
      character {\n\
        name\n\
      }\n\
      proficientRequirements {\n\
        timeCost\n\
        materialCost {\n\
          materialName\n\
          count\n\
        }\n\
      }\n\
    }\n\
  }\n\
}]'
QUERY_RESULTS_2 = [{
    "data": {
        "skill": {
            "skillRequirements": [
                {
                    "character": {
                        "name": "史尔特尔"
                    },
                    "proficientRequirements": [
                        {
                            "timeCost": 28800,
                            "materialCost": [
                                {
                                    "materialName": "技巧概要·卷3",
                                    "count": 8
                                },
                                {
                                    "materialName": "提纯源岩",
                                    "count": 4
                                },
                                {
                                    "materialName": "研磨石",
                                    "count": 7
                                }
                            ]
                        },
                        {
                            "timeCost": 57600,
                            "materialCost": [
                                {
                                    "materialName": "技巧概要·卷3",
                                    "count": 12
                                },
                                {
                                    "materialName": "五水研磨石",
                                    "count": 4
                                },
                                {
                                    "materialName": "白马醇",
                                    "count": 9
                                }
                            ]
                        },
                        {
                            "timeCost": 86400,
                            "materialCost": [
                                {
                                    "materialName": "技巧概要·卷3",
                                    "count": 15
                                },
                                {
                                    "materialName": "D32钢",
                                    "count": 6
                                },
                                {
                                    "materialName": "聚合凝胶",
                                    "count": 6
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }
}]
THOUGHTS_2 = '”黄昏“是一个技能名字。专精(或专一,专二,专三)指的是干员的技能在升至7级之后进一步强化的过程。\n\
这里的游戏数据查询结果包含全部的专精需求，因为我们只需要”专三“的材料，我们只需要用到列表中第三个数据。'
FINAL_RESPONSE_2 = '“黄昏”是干员史尔特尔的技能，它专三需要的材料是：\n\
技巧概要·卷3 * 15\n\
D32钢 * 6\n\
聚合凝胶 * 6\n\
'

SYSTEM_PROMPT = f'\注意请不要使用你已有的关于《明日方舟》信息,仅仅考虑上下文提供的信息进行回答.\n\
你是一名了解游戏《明日方舟》,并且精通Graph QL的专家。我们现有一个可以查询明日方舟游戏数据（如干员，技能信息）的Graph QL API。针对用户的问题，我们已经编写了query，并且获得了query results。\n\
明日方舟中的干员可以有多个精英阶段,分别为未精英(精0),精一,精二.除非用户特别指明需要低等级信息,我们只返回干员的最高精英阶段(index=-1).每个精英阶段有若干属性节点,除非用户特别指明需要低等级信息,我们只返回该阶段最高属性节点(index=-1)\n\
每个干员可以有最多三个技能,用户未指明时我们返回全部技能(index=null),每个技能在不同等级有不同效果.除非用户特别指明需要低等级信息,我们只返回技能最高等级(index为-1)的信息.\n\
现在，提供给你用户的问题，query list， results list，请分析query result并使用它来回答用户的问题。\n\
Think step by step.\n\
'
EXAMPLES = [{'question': QUESTION_1, 'queries': str(QUERIES_1),
             'query_results': json.dumps(QUERY_RESULTS_1, ensure_ascii=False),
             'thoughts': THOUGHTS_1, 'response': FINAL_RESPONSE_1},
            {'question': QUESTION_2, 'queries': str(QUERIES_2),
             'query_results': json.dumps(QUERY_RESULTS_2, ensure_ascii=False),
             'thoughts': THOUGHTS_2, 'response': FINAL_RESPONSE_2},]

OUTPUT_INDICATOR = 'Final output:'


class Summarizer(Chain):
    output_key: ClassVar[str] = 'response'
    question_key: ClassVar[str] = 'question'
    graphql_query_key: ClassVar[str] = 'graphql_queries'
    graphql_result_key: ClassVar[str] = 'graphql_results'

    chain: Chain = None
    log_entry: LogEntry = None

    def __init__(self, log_entry: LogEntry) -> None:
        super().__init__(log_entry=log_entry)
        example_prompt = ChatPromptTemplate.from_messages(
            [('user', 'Question: {question} \n\nQueries: {queries} \n\nQuery Results: {query_results}'),
             ('ai', 'Thoughts: {thoughts} \n\nFinal output: {response}')])

        few_shot_prompt = FewShotChatMessagePromptTemplate(
            examples=EXAMPLES,
            # This is a prompt template used to format each individual example.
            example_prompt=example_prompt,
        )

        final_prompt = ChatPromptTemplate.from_messages([
            ('system', SYSTEM_PROMPT),
            few_shot_prompt,
            ('user', 'User: {question} \nQueries: {graphql_queries} \nQuery Results: {graphql_results}'),
        ])

        llm = ChatOpenAI(temperature=0.3)

        self.chain = (
            {
                'question': lambda x: x[Summarizer.question_key],
                'graphql_queries': lambda x: x[Summarizer.graphql_query_key],
                'graphql_results': lambda x: x[Summarizer.graphql_result_key],
            }
            | final_prompt
            | llm
            | StrOutputParser()
        )

    @property
    def input_keys(self) -> List[str]:
        return [Summarizer.question_key, Summarizer.graphql_query_key, Summarizer.graphql_result_key]

    @property
    def output_keys(self) -> List[str]:
        return [Summarizer.output_key]

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        question = inputs[Summarizer.question_key]
        self.log_entry.messages.extend([
            Message(role='user', content=question),
        ])

        try:
            response = self.chain.invoke(inputs)
        except Exception as e:
            self.log_entry.status = SessionStatus.fail
            self.log_entry.error = f'Summarizer error: Exception when calling LLM: {e}'

        self.log_entry.status = SessionStatus.success
        return self._parse_llm_response(response)

    async def _acall(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        question = inputs[Summarizer.question_key]
        self.log_entry.messages.extend([
            Message(role='user', content=question),
        ])

        try:
            response = await self.chain.ainvoke(inputs)
        except Exception as e:
            self.log_entry.status = SessionStatus.fail
            self.log_entry.error = f'Summarizer error: Exception when calling LLM: {e}'
            return ''

        self.log_entry.status = SessionStatus.success
        return self._parse_llm_response(response)

    def _parse_llm_response(self, response: str) -> Dict[str, str]:
        self.log_entry.messages.append(Message(role='agent', content=response))

        result_json_idx = response.find(OUTPUT_INDICATOR)
        if result_json_idx != -1:
            response = response[result_json_idx + len(OUTPUT_INDICATOR):]
        return {Summarizer.output_key: response.strip()}


if __name__ == '__main__':
    from utils import start_session
    summarizer = Summarizer(start_session('test'))
    question = '山是什么职业的干员,他的二天赋是什么?'
    queries = ['{\
        characters(filter: {name: "山"}) {\n\
        name\n\
        profession\n\
        talents\n\
        }\n\
    }\n\
    ']
    query_results = [
        {
            "data": {
                "characters": [
                    {
                        "name": "山",
                        "profession": "近卫",
                        "talents": [
                                "巨力重拳: 攻击时有20%的几率攻击力提升至165%（+5%），并在3秒内使目标攻击力降低15%（不可叠加）",
                                "强壮肉体: 防御力+10%，获得15%的物理闪避"
                        ]
                    }
                ]
            }
        }
    ]

    print(summarizer.invoke({'question': question, 'graphql_queries': queries, 'graphql_results': query_results}))
