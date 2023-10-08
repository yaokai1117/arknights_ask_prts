import os
import json

from utils import llm_client
from data_model import Message, PlannerOutput, PlannerOutputType, ToolType, LogEntry
from dotenv import load_dotenv

# Determint the intention of user's input and decide which
# worker should be called next.

load_dotenv()
schema_path = os.getenv("GRAPHQL_SCHEMA_PATH")
with open(schema_path) as file:
    schema = file.read()

SYSTEM_PROMPT = f'注意请不要使用你已有的关于《明日方舟》信息,仅仅考虑上下文提供的信息进行回答.\n\
《明日方舟》是一款由中国游戏公司鹰角Hypergryph开发并运营的策略类手机游戏.游戏的故事背景是一个科幻世界,玩家需要管理一支特殊团队,招募不同技能和特点的干员(游戏中的角色),并通过策略性的战斗来应对各种挑战.\n\
明日方舟中的干员可以有多个精英阶段,分别为未精英(精0),精一,精二.除非用户特别指明需要低等级信息,我们只返回干员的最高精英阶段(index=-1).每个精英阶段有若干属性节点,除非用户特别指明需要低等级信息,我们只返回该阶段最高属性节点(index=-1)\n\
每个干员可以有最多三个技能,用户未指明时我们返回全部技能(index=null),每个技能在不同等级有不同效果.除非用户特别指明需要低等级信息,我们只返回技能最高等级(index为-1)的信息.\n\
你是一名了解游戏《明日方舟》,并且会编写Graph QL query的专家,现在你可以使用一些有关《明日方舟》的工具,包括:\n\
1. 一个包含干员信息,技能信息的GraphQL API,schema如下: \n\
--- Begin GraphQL API schema ---\n\
{schema}\
--- End GraphQL API schema ---\n\
\n\
2. 视频网站Bilibili的搜索API,对于与明日方舟有关,但是无法用之前的工具回答的问题,可以通过搜索一些关键词来返回一些有关视频. \n\
\n\
你将对用户提出的问题进行分类,首先确认它是否与《明日方舟》有关,如果有关,尝试选择一个工具,并提供使用这个工具的输入信息.\
你的回复必须为以下的format\n\
--- Result format --- \n\
Thoughts: Step by step analysis. \n\
\n\
Final output:\n\
{{\n\
    "result_type": "related", # String, whether this question is related \n\
    "tool_name": "game_data_graph_ql", # Can be one of "game_data_graph_ql", "bilibili_search" \n\
    "tool_input": ["..."], # List of string, can be a list of Graph QL query strings, or a list of keyword strings \n\
}}\n\
--- End Result format --- \n\
参照以下示例,一步一步进行思考并记录在"Thoughts:"后面.\n\
确保你的回复包含"Final output:" 以及之后的JSON\n\
\n\
--- Begin Examplers: ---\n\
\n\
Exampler 1:\n\
User: "玛恩纳的三技能的在专二时的效果是什么？该技能的专精材料是什么" \n\
Agent: "Thoughts: 玛恩纳是一个干员的名字，这里的"三技能"指的是干员玛恩纳的第三个技能,我们可以使用Character的skills字段来获取技能的信息.\n\
关于第一个问题:专二时的效果:\n\
字段levels包含技能在每个等级的效果,技能有最多10个等级,当用户指明1到7级时我们返回对应1到7级的技能信息,而专精一,二,三分别对应第8,9,10级.\n\
这里用户指明了专二,对应第9级.\n\
注意,在query时index从0开始\n\
关于第二个问题:该技能的专精材料:可以通过skillRequirements字段获取\n\
Final output: \n\
{{\n\
    "result_type": "related",\n\
    "tool_name": "game_data_graph_ql",\n\
    "tool_input": [\n\
        \"{{\\n\
        characters(filter: {{name: \\"玛恩纳\\"}}) {{\\n\
            name\\n\
            skills(index: 2) {{\\n\
                skillName\\n\
                levels(index: 8) {{\\n\
                    description\\n\
                    skillType\\n\
                    durationType\\n\
                    duration\\n\
                    spType\\n\
                    spCost\\n\
                    initialSp\\n\
                    maxCharge\\n\
                }}\\n\
                skillRequirements {{\\n\
                    proficientRequirements  {{\\n\
                        timeCost\\n\
                        materialCost {{\\n\
                            id\\n\
                            count\\n\
                        }}\\n\
                    }}\\n\
                }}\\n\
            }}\\n\
        }}\\n\
        }}\"\n\
    ]\n\
}}\n\
\n\
Exampler 2:\n\
User: "黄昏专三的专精材料是什么？" \n\
Agent: "Thoughts: 专精(或专一,专二,专三)指的是干员的技能在升至7级之后进一步强化的过程.由此可见,\\"黄昏\\"可能是一个技能名字.当技能名字存在时,我们可以直接query skills,不用通过character进行query.\n\
Final output: \n\
{{\n\
    "result_type": "related",\n\
    "tool_name": "game_data_graph_ql",\n\
    "tool_input": [\n\
        \"{{\\n\
        skill(filter: {{skillName: \\"黄昏\\"}}) {{\\n\
            skillRequirements {{\\n\
                character {{\\n\
                    name\\n\
                }}\\n\
                proficientRequirements(index: null)  {{\\n\
                    timeCost\\n\
                    materialCost {{\\n\
                        materialName\\n\
                        count\\n\
                    }}\\n\
                }}\\n\
            }}\\n\
        }}\\n\
        }}\"\n\
    ]\n\
}}\n\
\n\
Exampler 3:\n\
User: "有哪些六星的秘术师干员" \n\
Agent: "Thoughts: 首先我们需要唯一确认“秘术师“对应的字段，它可能是位置(position)、职业(profession)、分支职业(subProfession). 可以通过以下步骤来确定:\n\
位置(position)的全部值为: [高台、地面、近战、远程]. “秘术师“不在其中,所以它不是一个位置.\n\
职业(profession)的全部值: [先锋,近卫,术师(=术士),狙击,重装,医疗,辅助,特种],“秘术师“不在其中,所以它不是一个职业(profession)\n\
因此，“秘术师“只可能是一个分支职业.应该使用subProfession字段.\n\
Final output: \n\
{{\n\
    "result_type": "related",\n\
    "tool_name": "game_data_graph_ql",\n\
    "tool_input": [\n\
        \"{{\\n\
        characters(filter: {{subProfession: \\"秘术师\\", rarity: 6}}) {{\\n\
            name\\n\
        }}\\n\
        }}\"\n\
    ]\n\
}}\n\
\n\
Exampler 4:\n\
User: "银灰和史尔特尔谁的攻击力更高？" \n\
Agent: "Thoughts: 我们需要发送两个query分别获取这两个干员的攻击力。\n\
Final output: \n\
{{\n\
    "result_type": "related",\n\
    "tool_name": "game_data_graph_ql",\n\
    "tool_input": [\n\
        \"{{\\n\
        characters(filter: {{name: \\"银灰\\"}}) {{\\n\
            name\\n\
            phases(index: -1) {{\n\
                attributesKeyFrames(index: -1) {{\n\
                    atk\n\
                }}\n\
            }}\n\
        }}\\n\
        }}\",\n\
        \"{{\\n\
        characters(filter: {{name: \\"史尔特尔\\"}}) {{\\n\
            name\\n\
            phases(index: -1) {{\n\
                attributesKeyFrames(index: -1) {{\n\
                    atk\n\
                }}\n\
            }}\n\
        }}\\n\
        }}\"\n\
    ]\n\
}}\n\
\n\
Exampler 5:\n\
User: "明日方舟中最强术士是谁?" \n\
Agent: "Thoughts: 干员强弱,排行榜,梯度等等问题需要考虑多个方面,且包含一定主观因素,难以通过游戏数据API获取全部信息.可以在Bilibili视频网站上搜索.关键词为"明日方舟", "术士", "干员测评"\n\
Final output: \n\
{{\n\
    "result_type": "related",\n\
    "tool_name": "bilibili_search",\n\
    "tool_input": ["明日方舟", "术士", "干员测评"]\n\
}}\n\
\n\
Exampler 6:\n\
User: "土拨鼠的叫声是什么样子的?" \n\
Agent: "Thoughts: 该问题与明日方舟无关。我们仍然需要返回一个JSON的结果\n\
Final output: \n\
{{\n\
    "result_type": "unrelated",\n\
}}\n\
\n\
--- End examplers ---\n\
'

class Planner():
    OUTPUT_INDICATOR = 'Final output:'

    def process(self, message_content: str, log_entry: LogEntry) -> PlannerOutput:
        messages = [
            Message(role='system', content=SYSTEM_PROMPT),
            Message(role='user', content=message_content),
        ]
        log_entry.messages.extend(messages)
        try:
            response = llm_client.send(messages)
        except Exception as e:
            return self._create_failed_output(f'Exception when calling LLM: {e}')

        log_entry.messages.append(Message(role='agent', content=response))

        result_json_idx = response.find(Planner.OUTPUT_INDICATOR)
        if result_json_idx == -1:
            return self._create_failed_output('No final output returned from Planner.')
        result_json = response[result_json_idx + len(Planner.OUTPUT_INDICATOR):]

        try:
            result = json.loads(result_json)
        except Exception as e:
            return self._create_failed_output(f'Exception when pasing result json: {e}')

        output_type: PlannerOutputType
        if result.get('result_type') == 'unrelated':
            output_type = PlannerOutputType.unrelated
            return PlannerOutput(succeeded=True, type=output_type)
        elif result.get('result_type') == 'related':
            output_type = PlannerOutputType.solvable_by_tool
        else:
            return self._create_failed_output('Unknown result type.')
        
        tool_type: ToolType
        if result.get('tool_name') in [e.value for e in ToolType]:
            tool_type = ToolType[result['tool_name']]
        else:
            return self._create_failed_output('Unknown tool type.')

        return PlannerOutput(succeeded=True, type=output_type, tool_type=tool_type, tool_input=result.get('tool_input'))
    
    def _create_failed_output(self, error: str) -> PlannerOutput:
        return PlannerOutput(succeeded=False, error=error)

if __name__ ==  '__main__':
    from utils import start_session

    planer = Planner()
    log_entry = start_session('test')
    # print(planer.process('明日方舟中4.5周年什么时候开?', log_entry))
    # print(planer.process('仇白和山哪个生命值更高,攻击力、防御力、法抗呢？他们的技能又对比如何？', log_entry))
    # print(planer.process('明日天气怎么样?', log_entry))
    # print(planer.process('山的二技能在一级时候是什么?', log_entry))
    # print(planer.process('山的二技能在专一时候是什么?', log_entry))
    # print(planer.process('山是什么职业的干员,他的二天赋是什么?', log_entry))
    # print(planer.process('请介绍新干员仇白', log_entry))
    # print(planer.process('仇白三技能需要的材料是什么', log_entry))
    # print(planer.process('技能”你须愧悔“需要哪些专精材料', log_entry))
    # print(planer.process('干员”山“的攻击力和生命值如何', log_entry))
    # print(planer.process('有哪些六星的术士', log_entry))
    # print(planer.process('有哪些5星的远卫干员', log_entry))
    print(planer.process('苇草的技能专精需要用到三水锰矿吗', log_entry))

