import os
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

from data_model import Message, PlannerOutput, PlannerOutputType, ToolType, ToolInput, LogEntry
from typing import List, Dict, Any, Optional, ClassVar

# Determint the intention of user's input and decide which
# worker should be called next.

schema_path = os.getenv("GRAPHQL_SCHEMA_PATH")
with open(schema_path) as file:
    schema = file.read()

SYSTEM_PROMPT = '''
你是一个关于手机游戏《明日方舟》(Arknights)的AI助手, 熟练掌握GraphQL, 并且熟悉embedding database的使用方法. 你能够通过使用一些工具来解答用户的问题。
你的任务是根据用户的提问, 判断该问题是否与《明日方舟》有关. 如果有关, 选取需要的工具, 并且准备好这些工具需要的输入数据。每个工具可以被使用多次。

## 你可以使用的工具

1. 游戏数据GraphQL API
一个包含干员信息,技能信息的GraphQL API,schema如下:
--- Begin GraphQL API schema ---
{schema}
--- End GraphQL API schema ---
在编写游戏数据GraphQL的query时需要注意:
明日方舟中的干员可以有多个精英阶段,分别为未精英(精0),精一,精二.除非用户特别指明需要低等级信息,我们只返回干员的最高精英阶段(index=-1).每个精英阶段有若干属性节点,除非用户特别指明需要低等级信息,我们只返回该阶段最高属性节点(index=-1)
每个干员可以有最多三个技能,用户未指明时我们返回全部技能(index=null),每个技能在不同等级有不同效果.除非用户特别指明需要低等级信息,我们只返回技能最高等级(index为-1)的信息
游戏数据Graph QL API的输入数据的格式是一个列表, 包含一个合法的GraphQL query string, 符合上述的schema。

2. 视频网站Bilibili的搜索API
对于与明日方舟有关,但是无法用之前的工具回答的问题,可以通过搜索一些关键词来返回一些有关视频. 
搜索API的输入数据格式是一个包含多个关键词的string, 关键词之间用空格分开。

3. 存储在一个Embedding Database中的游戏剧情文本
剧情文本都是人物对话的格式. 你可以通过embedding similarity来搜索与用户问题接近的剧情文本。
游戏剧情文本embedding database的输入数据格式是用于similarity search的用户query string

注意请不要使用你已有的关于《明日方舟》信息,仅仅考虑上下文提供的信息进行回答.
《明日方舟》是一款由中国游戏公司鹰角Hypergryph开发并运营的策略类手机游戏.游戏的故事背景是一个科幻世界,玩家需要管理一支特殊团队,招募不同技能和特点的干员(游戏中的角色),并通过策略性的战斗来应对各种挑战.

## 输出格式
你的回复必须为以下的format
--- Result format ---
Thoughts: 
Step by step thinking.

Final output:
{{FINAL_OUTPUT_JSON}}
--- End Result format ---
确保你的回复包含"Final output:" 以及之后的JSON. 其中FINAL_OUTPUT_JSON必须符合如下的schema:
{{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "$id": "https://example.com/employee.schema.json",
    "title": "Final output of AI planner",
    "description": "This document is the output of an AI planner, including tools to use and their inputs",
    "type": "object",
    "properties": {{
        "result_type": {{
            "description": "Whether this question is related to game Arknights",
            "type": "string"
            "enum": ["related", "unrelated"]
        }},
        "tools": {{
            "type": "array",
            "items": {{
                "description": "The name of a tool to call, and the input for the tool",
                "type": "object",
                "properties": {{
                    "tool_name": {{
                        "type": "string",
                        "enum": ["game_data_graph_ql", "bilibili_search", "stroy_database"]
                    }},
                    "tool_input": {{
                        "description": "Input for the tool, can be a GraphQL query, a keyword, or a query for similarity search",
                        "type": "string",
                    }}
                }}
            }}
        }}
    }}
}}
'''

QUESTION_1 = '玛恩纳的三技能的在专二时的效果是什么？该技能的专精材料是什么?'
THOUGHTS_1 = '''玛恩纳是一个干员的名字，这里的"三技能"指的是干员玛恩纳的第三个技能,我们可以使用Character的skills字段来获取技能的信息.
关于第一个问题:专二时的效果: 字段levels包含技能在每个等级的效果,技能有最多10个等级,当用户指明1到7级时我们返回对应1到7级的技能信息,而专精一,二,三分别对应第8,9,10级. 这里用户指明了专二,对应第9级. 注意,在query时index从0开始
关于第二个问题:该技能的专精材料:可以通过skillRequirements字段获取'''
RESPONSE_1 = '{\n\
    "result_type": "related",\n\
    "tools": [\n\
        {\n\
            "tool_name": "game_data_graph_ql",\n\
            "tool_input": \"{\\n\
                characters(filter: {name: \\"玛恩纳\\"}) {\\n\
                    name\\n\
                    skills(index: 2) {\\n\
                        skillName\\n\
                        levels(index: 8) {\\n\
                            description\\n\
                            skillType\\n\
                            durationType\\n\
                            duration\\n\
                            spType\\n\
                            spCost\\n\
                            initialSp\\n\
                            maxCharge\\n\
                        }\\n\
                        skillRequirements {\\n\
                            proficientRequirements  {\\n\
                                timeCost\\n\
                                materialCost {\\n\
                                    id\\n\
                                    count\\n\
                                }\\n\
                            }\\n\
                        }\\n\
                    }\\n\
                }\\n\
            }\"\n\
        }\n\
    ]\n\
}'

QUESTION_2 = '黄昏专三的专精材料是什么?'
THOUGHTS_2 = '专精(或专一,专二,专三)指的是干员的技能在升至7级之后进一步强化的过程.由此可见,\\"黄昏\\"可能是一个技能名字.当技能名字存在时,我们可以直接query skills,不用通过character进行query.'
RESPONSE_2 = '{\n\
    "result_type": "related",\n\
    "tools": [\n\
        {\n\
            "tool_name": "game_data_graph_ql",\n\
            "tool_input": \"{\\n\
                skill(filter: {skillName: \\"黄昏\\"}) {\\n\
                    skillRequirements {\\n\
                        character {\\n\
                            name\\n\
                        }\\n\
                        proficientRequirements(index: null)  {\\n\
                            timeCost\\n\
                            materialCost {\\n\
                                materialName\\n\
                                count\\n\
                            }\\n\
                        }\\n\
                    }\\n\
                }\\n\
            }\"\n\
        }\n\
    ]\n\
}'

QUESTION_3 = '有哪些六星的秘术师干员'
THOUGHTS_3 = '''首先我们需要唯一确认“秘术师“对应的字段，它可能是位置(position)、职业(profession)、分支职业(subProfession). 可以通过以下步骤来确定:
位置(position)的全部值为: [高台、地面、近战、远程]. “秘术师“不在其中,所以它不是一个位置.
职业(profession)的全部值: [先锋,近卫,术师(=术士),狙击,重装,医疗,辅助,特种],“秘术师“不在其中,所以它不是一个职业(profession)
因此，“秘术师“只可能是一个分支职业.应该使用subProfession字段.
'''
RESPONSE_3 = '{\n\
    "result_type": "related",\n\
    "tools": [\n\
        {\n\
            "tool_name": "game_data_graph_ql",\n\
            "tool_input": \"{\\n\
                characters(filter: {subProfession: \\"秘术师\\", rarity: 6}) {\\n\
                    name\\n\
                }\\n\
            }\"\n\
        }\n\
    ]\n\
}'

QUESTION_4 = '银灰和史尔特尔谁的攻击力更高?'
THOUGHTS_4 = '我们需要发送两个query分别获取这两个干员的攻击力'
RESPONSE_4 = '{\n\
    "result_type": "related",\n\
    "tools": [\n\
        {\n\
            "tool_name": "game_data_graph_ql",\n\
            "tool_input": \"{\\n\
                characters(filter: {name: \\"银灰\\"}) {\\n\
                    name\\n\
                    phases(index: -1) {\\n\
                        attributesKeyFrames(index: -1) {\\n\
                            atk\\n\
                        }\\n\
                    }\\n\
                }\\n\
            }\"\n\
        },\n\
        {\n\
            "tool_name": "game_data_graph_ql",\n\
            "tool_input": \"{\\n\
                characters(filter: {name: \\"史尔特尔\\"}) {\\n\
                    name\\n\
                    phases(index: -1) {\\n\
                        attributesKeyFrames(index: -1) {\\n\
                            atk\\n\
                        }\\n\
                    }\\n\
                }\\n\
            }\"\n\
        }\n\
    ]\n\
}'

QUESTION_5 = '明日方舟中最强术士是谁?'
THOUGHTS_5 = '排行榜,梯度等等问题需要考虑多个方面,且包含一定主观因素,难以通过游戏数据API获取全部信息.可以在Bilibili视频网站上搜索.关键词为"明日方舟", "术士", "干员测评"'
RESPONSE_5 = '{\n\
    "result_type": "related",\n\
    "tools": [\n\
        {\n\
            "tool_name": "bilibili_search",\n\
            "tool_input": "明日方舟 术士 干员测评"\n\
        }\n\
    ]\n\
}'

QUESTION_6 = '土拨鼠的叫声是什么样子的?'
THOUGHTS_6 = '该问题与明日方舟无关。我们仍然需要返回一个JSON的结果'
RESPONSE_6 = '{\n\
    "result_type": "unrelated"\n\
}'

EXAMPLES = [
    {'question': QUESTION_1, 'thoughts': THOUGHTS_1, 'response': RESPONSE_1},
    {'question': QUESTION_2, 'thoughts': THOUGHTS_2, 'response': RESPONSE_2},
    {'question': QUESTION_3, 'thoughts': THOUGHTS_3, 'response': RESPONSE_3},
    {'question': QUESTION_4, 'thoughts': THOUGHTS_4, 'response': RESPONSE_4},
    {'question': QUESTION_5, 'thoughts': THOUGHTS_5, 'response': RESPONSE_5},
    {'question': QUESTION_6, 'thoughts': THOUGHTS_6, 'response': RESPONSE_6},
]

OUTPUT_INDICATOR = 'Final output:'


class Planner(Chain):
    input_key: ClassVar[str] = 'question'
    chain: Chain = None
    log_entry: LogEntry = None

    def __init__(self, log_entry: LogEntry) -> None:
        super().__init__(log_entry=log_entry)
        example_prompt = ChatPromptTemplate.from_messages(
            [('user', '{question}'), ('ai', 'Thoughts: {thoughts} \n\nFinal output: {response}')])

        few_shot_prompt = FewShotChatMessagePromptTemplate(
            examples=EXAMPLES,
            # This is a prompt template used to format each individual example.
            example_prompt=example_prompt,
        )

        final_prompt = ChatPromptTemplate.from_messages([
            ('system', SYSTEM_PROMPT),
            few_shot_prompt,
            ('user', '{question}'),
        ])

        llm = ChatOpenAI(temperature=0.3)

        self.chain = (
            {
                'schema': lambda _: schema,
                'question': lambda x: x[Planner.input_key],
            }
            | final_prompt
            | llm
            | StrOutputParser()
            | self._parse_llm_response_and_log
            | self._pydantic_to_dict
        )

    @property
    def input_keys(self) -> List[str]:
        return [Planner.input_key]

    @property
    def output_keys(self) -> List[str]:
        return PlannerOutput.model_fields.keys()

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        question = inputs[Planner.input_key]
        self.log_entry.messages.extend([
            Message(role='user', content=question),
        ])

        try:
            result = self.chain.invoke(inputs)
        except Exception as e:
            return self._create_failed_output(f'Exception when calling LLM: {e}').model_dump()
        return result

    async def _acall(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        question = inputs[Planner.input_key]
        self.log_entry.messages.extend([
            Message(role='user', content=question),
        ])

        try:
            result = await self.chain.ainvoke(inputs)
        except Exception as e:
            return self._create_failed_output(f'Exception when calling LLM: {e}').model_dump()

        return result
    
    def _parse_llm_response_and_log(self, response: str) -> PlannerOutput:
        self.log_entry.messages.append(Message(role='agent', content=response))
        result = self._parse_llm_response(response)
        self.log_entry.planner_output = result
        return result

    def _parse_llm_response(self, response: str) -> PlannerOutput:
        result_json_idx = response.find(OUTPUT_INDICATOR)
        if result_json_idx == -1:
            return self._create_failed_output('No final output returned from Planner.')
        result_json = response[result_json_idx + len(OUTPUT_INDICATOR):]

        try:
            result = json.loads(result_json)
        except Exception as e:
            return self._create_failed_output(f'Exception when parsing result json: {e}')

        output_type: PlannerOutputType
        if result.get('result_type') == 'unrelated':
            output_type = PlannerOutputType.unrelated
            return PlannerOutput(succeeded=True, type=output_type)
        elif result.get('result_type') == 'related':
            output_type = PlannerOutputType.solvable_by_tool
        else:
            return self._create_failed_output('Unknown result type.')
        
        planer_output = PlannerOutput(succeeded=True, type=output_type)
        if isinstance(result.get('tools'), list):
            for input in result.get('tools'):
                if input.get('tool_name') in [e.value for e in ToolType]:
                    tool_type = ToolType[input['tool_name']]
                    tool_input = input['tool_input']
                    planer_output.inputs.append(ToolInput(tool_type=tool_type, tool_input=tool_input))
                else:
                    return self._create_failed_output('Unknown tool type.')

        return planer_output

    def _create_failed_output(self, error: str) -> PlannerOutput:
        return PlannerOutput(succeeded=False, error=error)

    def _pydantic_to_dict(self, response: PlannerOutput) -> Dict[str, Any]:
        return response.model_dump()


if __name__ == '__main__':
    from utils import start_session

    some_log_entry = start_session('test')
    planer = Planner(some_log_entry)
    # print(planer.process('明日方舟中4.5周年什么时候开?', log_entry))
    # print(planer.process('仇白和山哪个生命值更高,攻击力、防御力、法抗呢？他们的技能又对比如何？', log_entry))
    # print(planer.process('明日天气怎么样?', log_entry))
    # print(planer.process('山的二技能在一级时候是什么?', log_entry))
    # print(planer.process('山的二技能在专一时候是什么?', log_entry))
    # print(planer.process('山是什么职业的干员,他的二天赋是什么?', log_entry))
    # print(planer.invoke({'question': '请介绍新干员仇白'}))
    # print(planer.process('仇白三技能需要的材料是什么', log_entry))
    # print(planer.process('技能”你须愧悔“需要哪些专精材料', log_entry))
    # print(planer.process('干员”山“的攻击力和生命值如何', log_entry))
    print(planer.invoke({'question': '有哪些六星的术士'}))
    # print(planer.process('有哪些5星的远卫干员', log_entry))
    # print(planer.invoke({'question': '临光家有哪些干员'}))
