## arknights_ask_prts

A chat bot API for questions about game Arknights, leveraing the GraphQL game data API [arknights_data_api](https://github.com/yaokai1117/arknights_data_api)  

**Everything is still WIP.**

**Note**: currently only support Chinese version data set.  

Currently only support single turn question answering. The process flow is:
1. User send a question.
2. The question is proceessed by a [Planner](https://github.com/yaokai1117/arknights_ask_prts/blob/main/planner.py), which uses LLM to decide whether this question is related, which tool can be used, and more importantly, generate a valid input for the tool based on the schema we provide. In our case we **provdie the[ Graph QL schema](https://github.com/yaokai1117/arknights_data_api/blob/main/graphql_api/schema.graphql)** of the game data API.
3. The tool will be triggered with tht input returne by Planner.   
a. For the case that the question can be answerd by querying the game data API, we send the genrate queries and get a list of resutls.  
b. For the case that cannot be solve by querying game data, we search the keywords using Bilibili search API and return the top 5 results.  
4. (Optionally) for the graph ql results, we send them together with the query and the initial question to LLM again to summarize and give an answer. Though [Summarizer](https://github.com/yaokai1117/arknights_ask_prts/blob/main/summarizer.py).


## Example process flow
User send an initial question: 
```
玛恩纳的防御力在全部六星近卫干员中处于什么水平？请列出你的判断依据
```

This will send with our system prompt to the LLM to decide whether we can use the game data API to answer. The response of the LLM:

```
Thoughts: 首先，我们需要获取所有六星近卫干员的防御力信息，并对比玛恩纳的防御力。我们可以通过查询所有六星近卫干员的属性节点来获取防御力信息。

Final output:
{
    "result_type": "related",
    "tool_name": "game_data_graph_ql",
    "tool_input": [
        "{
          characters(filter: {profession: \"近卫\", rarity: 6}) {
            name      
            phases(index: -1) {
              attributesKeyFrames(index: -1) {
                physicalDef
              }
            }
          }
        }"
    ]
}
```

The Planner determines that this is related to Arknights, and can be solved by `game_data_graph_ql`, so we will send the generated `tool_input` to the game data API.

The results returned by the API are:
<details>
  <summary>Click me to expand full game data response.</summary>

```js
[
  {
    "data": {
      "characters": [
        {
          "name": "山",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 357
                }
              ]
            }
          ]
        },
        {
          "name": "重岳",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 363
                }
              ]
            }
          ]
        },
        {
          "name": "银灰",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 397
                }
              ]
            }
          ]
        },
        {
          "name": "棘刺",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 402
                }
              ]
            }
          ]
        },
        {
          "name": "仇白",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 402
                }
              ]
            }
          ]
        },
        {
          "name": "陈",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 352
                }
              ]
            }
          ]
        },
        {
          "name": "艾丽妮",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 349
                }
              ]
            }
          ]
        },
        {
          "name": "煌",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 370
                }
              ]
            }
          ]
        },
        {
          "name": "百炼嘉维尔",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 391
                }
              ]
            }
          ]
        },
        {
          "name": "史尔特尔",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 414
                }
              ]
            }
          ]
        },
        {
          "name": "赫拉格",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 334
                }
              ]
            }
          ]
        },
        {
          "name": "帕拉斯",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 455
                }
              ]
            }
          ]
        },
        {
          "name": "耀骑士临光",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 295
                }
              ]
            }
          ]
        },
        {
          "name": "圣约送葬人",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 461
                }
              ]
            }
          ]
        },
        {
          "name": "玛恩纳",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 502
                }
              ]
            }
          ]
        },
        {
          "name": "斯卡蒂",
          "phases": [
            {
              "attributesKeyFrames": [
                {
                  "physicalDef": 263
                }
              ]
            }
          ]
        }
      ]
    }
  }
]
```

</details>
<br/>
Then we send the initial question, the request, the response altogher to LLM again, then we get the final response:

```
根据查询结果，我们可以列出全部六星近卫干员的防御力，并判断玛恩纳的防御力在其中处于什么水平。

全部六星近卫干员的防御力如下：
山：357
重岳：363
银灰：397
棘刺：402
仇白：402
陈：352
艾丽妮：349
煌：370
百炼嘉维尔：391
史尔特尔：414
赫拉格：334
帕拉斯：455
耀骑士临光：295
圣约送葬人：461
玛恩纳：502
斯卡蒂：263

根据数据，玛恩纳的防御力为502，是全部六星近卫干员中防御力最高的。
```

From the end user's perspective, they will see a conversation:
```
User: 玛恩纳的防御力在全部六星近卫干员中处于什么水平？请列出你的判断依据
Agent: 
全部六星近卫干员的防御力如下：
山：357
重岳：363
银灰：397
棘刺：402
仇白：402
陈：352
艾丽妮：349
煌：370
百炼嘉维尔：391
史尔特尔：414
赫拉格：334
帕拉斯：455
耀骑士临光：295
圣约送葬人：461
玛恩纳：502
斯卡蒂：263

根据数据，玛恩纳的防御力为502，是全部六星近卫干员中防御力最高的。
```