## arknights_ask_prts

A chat bot API for questions about game Arknights, leveraing the GraphQL game data API [arknights_data_api](https://github.com/yaokai1117/arknights_data_api)  

**Everythign is still WIP.**

**Note**: currently only support Chinese version data set.  

Currnely only support single turn question answering. The process flow is:
1. User send a question.
2. The question is proceessed by a [Planner](https://github.com/yaokai1117/arknights_ask_prts/blob/main/planner.py), to use LLM to decide whether this question is related, which tool can be used, and more importantly, generate a valid input for the tool based on the schema we provide. In our case we provdie the[ Graph QL schema](https://github.com/yaokai1117/arknights_data_api/blob/main/graphql_api/schema.graphql) of the game data API.
3. The tool will be triggered with tht input returne by Planner.   
a. For the case that the question can be answerd by querying the game data API, we send the genrate queries and get a list of resutls.  
b. For the case that cannot be solve by querying game data, we search the keywords using Bilibili search API and return the top 5 results.  
4. (Optionally) for the graph ql results, we send them together with the query and the initial question to LLM again to summarize and give an answer. Though [Summarizer](https://github.com/yaokai1117/arknights_ask_prts/blob/main/summarizer.py).


## Example process flow
User send an initial question: 
```
山是什么职业的干员?他的第二个天赋是什么?
```

This will send with our system prompt to the LLM to decide whether we can use the game data API to answer. The response of the LLM:
```
Thoughts: 用户询问关于一个名为"山"的干员的职业和第二个天赋。我们可以使用Character的name字段来获取干员的信息，然后通过talents字段获取天赋信息。

Final output:
{
    "result_type": "related",
    "tool_name": "game_data_graph_ql",
    "tool_input": [
        "{
          characters(filter: {name: "山"}) {
            name
            profession
            talents
          }
        }"
    ]
}
```

The Planner determines that this is related to Arknights, and can be solved by `game_data_graph_ql`, so we will send the generated `tool_input` to the game data API.

The results returned by the API are:
```
[
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
```

Then we send the initial question, the request, the response altogher to LLM again, then we get the final response:
```
Toughts: 从查询结果中可以得知，干员"山"的职业是近卫，他的第二个天赋是"强壮肉体: 防御力+10%，获得15%的物理闪避"。
Final output: "山"是近卫职业的干员，他的第二个天赋是"强壮肉体: 防御力+10%，获得15%的物理闪避"。
```

From the end user's perspective, they will see a conversation:
```
User: 山是什么职业的干员?他的第二个天赋是什么?
Agent: "山"是近卫职业的干员，他的第二个天赋是"强壮肉体: 防御力+10%，获得15%的物理闪避"。
```