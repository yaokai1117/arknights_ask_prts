import re

from pydantic import BaseModel
from typing import List, Callable, Optional
from graphql import parse, print_ast
from graphql.language.ast import ObjectFieldNode, FieldNode
from graphql.language.visitor import visit, Visitor, IDLE
from typing import Dict, Any


class ValueNormalizationData(BaseModel):
    normalized_value: str
    display_name: str
    potential_names: List[str]


class FieldNormalizer(BaseModel):
    field_name: str
    values: List[ValueNormalizationData]
    pre_process: Optional[Callable[[str], str]]

    def __init__(self, **data):
        super().__init__(**data)
        self._normalize_map = {name: value.normalized_value for value in self.values for name in value.potential_names}
        self._denormalize_map = {value.normalized_value: value.display_name for value in self.values}

    def normalize(self, input: str) -> str:
        if self.pre_process != None:
            input = self.pre_process(input)
        return self._normalize_map.get(input, input)

    def denormalize(self, input: str) -> str:
        return self._denormalize_map.get(input, input)


operator_suffix = re.compile('干员$')
def remove_operator_suffix(input): return re.sub(operator_suffix, '', input)


POSITION_FIELD_NORMALIZER = FieldNormalizer(field_name='position', values=[
    ValueNormalizationData(normalized_value='MELEE', display_name='近战', potential_names=['MELEE', '近战', '地面']),
    ValueNormalizationData(normalized_value='RANGED', display_name='远程', potential_names=['RANGED', '远程', '高台']),
], pre_process=remove_operator_suffix)

PROFESSION_FIELD_NORMALIZER = FieldNormalizer(field_name='profession', values=[
    ValueNormalizationData(normalized_value='PIONEER', display_name='先锋', potential_names=['PIONEER', '先锋']),
    ValueNormalizationData(normalized_value='CASTER', display_name='术师', potential_names=['CASTER', '术师', '术士']),
    ValueNormalizationData(normalized_value='SNIPER', display_name='狙击', potential_names=['SNIPER', '狙击']),
    ValueNormalizationData(normalized_value='WARRIOR', display_name='近卫', potential_names=['WARRIOR', '近卫']),
    ValueNormalizationData(normalized_value='SUPPORT', display_name='辅助', potential_names=['SUPPORT', '辅助']),
    ValueNormalizationData(normalized_value='SPECIAL', display_name='特种', potential_names=['SPECIAL', '特种']),
    ValueNormalizationData(normalized_value='MEDIC', display_name='医疗', potential_names=['MEDIC', '医疗']),
    ValueNormalizationData(normalized_value='TANK', display_name='重装', potential_names=['TANK', '重装']),
], pre_process=remove_operator_suffix)

SUB_PROFESSION_FIELD_NORMALIZER = FieldNormalizer(field_name='subProfession', values=[
    ValueNormalizationData(normalized_value='protector', display_name='铁卫', potential_names=['protector', '铁卫']),
    ValueNormalizationData(normalized_value='merchant', display_name='行商', potential_names=['merchant', '行商']),
    ValueNormalizationData(normalized_value='longrange', display_name='神射手', potential_names=['longrange', '神射手']),
    ValueNormalizationData(normalized_value='centurion', display_name='强攻手', potential_names=['centurion', '强攻手']),
    ValueNormalizationData(normalized_value='agent', display_name='情报官', potential_names=['agent', '情报官']),
    ValueNormalizationData(normalized_value='geek', display_name='怪杰', potential_names=['geek', '怪杰']),
    ValueNormalizationData(normalized_value='healer', display_name='疗养师', potential_names=['healer', '疗养师']),
    ValueNormalizationData(normalized_value='fortress', display_name='要塞', potential_names=['fortress', '要塞']),
    ValueNormalizationData(normalized_value='funnel', display_name='驭械术师', potential_names=['funnel', '驭械术师', '驭械术士']),
    ValueNormalizationData(normalized_value='chain', display_name='链术师', potential_names=['chain', '链术师', '链术士']),
    ValueNormalizationData(normalized_value='ritualist', display_name='巫役', potential_names=['ritualist', '巫役']),
    ValueNormalizationData(normalized_value='phalanx', display_name='阵法术师', potential_names=['phalanx', '阵法术师', '阵法术士']),
    ValueNormalizationData(normalized_value='underminer', display_name='削弱者', potential_names=['underminer', '削弱者']),
    ValueNormalizationData(normalized_value='splashcaster', display_name='扩散术师', potential_names=['splashcaster', '扩散术师', '扩散术士']),
    ValueNormalizationData(normalized_value='ringhealer', display_name='群愈师', potential_names=['ringhealer', '群愈师', '群奶']),
    ValueNormalizationData(normalized_value='guardian', display_name='守护者', potential_names=['guardian', '守护者', '奶盾']),
    ValueNormalizationData(normalized_value='bombarder', display_name='投掷手', potential_names=['bombarder', '投掷手']),
    ValueNormalizationData(normalized_value='incantationmedic', display_name='咒愈师', potential_names=['incantationmedic', '咒愈师']),
    ValueNormalizationData(normalized_value='hunter', display_name='猎手', potential_names=['hunter', '猎手']),
    ValueNormalizationData(normalized_value='corecaster', display_name='中坚术师', potential_names=['corecaster', '中坚术师', '中坚术士']),
    ValueNormalizationData(normalized_value='mystic', display_name='秘术师', potential_names=['mystic', '秘术师', '秘术士']),
    ValueNormalizationData(normalized_value='fastshot', display_name='速射手', potential_names=['fastshot', '速射手', '速狙']),
    ValueNormalizationData(normalized_value='sword', display_name='剑豪', potential_names=['sword', '剑豪']),
    ValueNormalizationData(normalized_value='reaperrange', display_name='散射手', potential_names=['reaperrange', '散射手']),
    ValueNormalizationData(normalized_value='executor', display_name='处决者', potential_names=['executor', '处决者']),
    ValueNormalizationData(normalized_value='charger', display_name='冲锋手', potential_names=['charger', '冲锋手']),
    ValueNormalizationData(normalized_value='crusher', display_name='重剑手', potential_names=['crusher', '重剑手']),
    ValueNormalizationData(normalized_value='librator', display_name='解放者', potential_names=['librator', '解放者']),
    ValueNormalizationData(normalized_value='unyield', display_name='不屈者', potential_names=['unyield', '不屈者']),
    ValueNormalizationData(normalized_value='instructor', display_name='教官', potential_names=['instructor', '教官']),
    ValueNormalizationData(normalized_value='craftsman', display_name='工匠', potential_names=['craftsman', '工匠']),
    ValueNormalizationData(normalized_value='slower', display_name='凝滞师', potential_names=['slower', '凝滞师']),
    ValueNormalizationData(normalized_value='artsfghter', display_name='术战者', potential_names=['artsfghter', '术战者', '法术近卫', '法卫']),
    ValueNormalizationData(normalized_value='lord', display_name='领主', potential_names=['lord', '领主', '远卫']),
    ValueNormalizationData(normalized_value='bard', display_name='吟游者', potential_names=['bard', '吟游者']),
    ValueNormalizationData(normalized_value='dollkeeper', display_name='傀儡师', potential_names=['dollkeeper', '傀儡师']),
    ValueNormalizationData(normalized_value='shotprotector', display_name='哨戒铁卫', potential_names=['protector', '哨戒铁卫']),
    ValueNormalizationData(normalized_value='physician', display_name='医师', potential_names=['physician', '医师']),
    ValueNormalizationData(normalized_value='pioneer', display_name='尖兵', potential_names=['pioneer', '尖兵']),
    ValueNormalizationData(normalized_value='reaper', display_name='收割者', potential_names=['reaper', '收割者']),
    ValueNormalizationData(normalized_value='wandermedic', display_name='行医', potential_names=['wandermedic', '行医']),
    ValueNormalizationData(normalized_value='bearer', display_name='执旗手', potential_names=['bearer', '执旗手', '投锋', '投降先锋']),
    ValueNormalizationData(normalized_value='artsprotector', display_name='驭法铁卫', potential_names=['artsprotector', '驭法铁卫']),
    ValueNormalizationData(normalized_value='traper', display_name='陷阱师', potential_names=['traper', '陷阱师']),
    ValueNormalizationData(normalized_value='closerange', display_name='重射手', potential_names=['closerange', '重射手']),
    ValueNormalizationData(normalized_value='siegesniper', display_name='攻城手', potential_names=['siegesniper', '攻城手']),
    ValueNormalizationData(normalized_value='musha', display_name='武者', potential_names=['musha', '武者']),
    ValueNormalizationData(normalized_value='blastcaster', display_name='轰击术师', potential_names=['blastcaster', '轰击术师']),
    ValueNormalizationData(normalized_value='stalker', display_name='伏击客', potential_names=['stalker', '伏击客']),
    ValueNormalizationData(normalized_value='tactician', display_name='战术家', potential_names=['tactician', '战术家']),
    ValueNormalizationData(normalized_value='pusher', display_name='推击手', potential_names=['pusher', '推击手']),
    ValueNormalizationData(normalized_value='fearless', display_name='无畏者', potential_names=['fearless', '无畏者']),
    ValueNormalizationData(normalized_value='hookmaster', display_name='钩索师', potential_names=['hookmaster', '钩索师']),
    ValueNormalizationData(normalized_value='summoner', display_name='召唤师', potential_names=['summoner', '召唤师']),
    ValueNormalizationData(normalized_value='blessing', display_name='护佑者', potential_names=['blessing', '护佑者']),
    ValueNormalizationData(normalized_value='aoesniper', display_name='炮手', potential_names=['aoesniper', '炮手']),
    ValueNormalizationData(normalized_value='fighter', display_name='斗士', potential_names=['fighter', '斗士', '拳卫']),
    ValueNormalizationData(normalized_value='chainhealer', display_name='链愈师', potential_names=['chainhealer', '链愈师']),
    ValueNormalizationData(normalized_value='duelist', display_name='决战者', potential_names=['duelist', '决战者']),
], pre_process=remove_operator_suffix)

normalizers_map = {normalizer.field_name: normalizer for normalizer in [
    POSITION_FIELD_NORMALIZER,
    PROFESSION_FIELD_NORMALIZER,
    SUB_PROFESSION_FIELD_NORMALIZER,
]}


def _normalize_field(field: str, input: str) -> str:
    if field in normalizers_map.keys():
        return normalizers_map[field].normalize(input)
    return input


def _denormalize_field(field: str, input: str) -> str:
    if field in normalizers_map.keys():
        return normalizers_map[field].denormalize(input)
    return input


class NormalizeVisitor(Visitor):
    # TODO: read this from schema.
    FIELDS_WITH_ARGUMENTS = ['characters', 'skill', 'skills', 'phases', 'levels', 'attributesKeyFrames']

    def enter(self, node, key, parent, path, ancestors):
        # Remove unwanted arguments.
        if isinstance(node, FieldNode):
            if len(node.arguments) != 0 and node.name.value not in NormalizeVisitor.FIELDS_WITH_ARGUMENTS:
                node.arguments = None
            return IDLE

        # Normalize argument values.
        if isinstance(node, ObjectFieldNode):
            field_name = node.name.value
            value = node.value

            if value.kind == 'list_value':
                for value in value.values:
                    if value.kind == 'string_value':
                        value.value = _normalize_field(field_name, value.value)
                return IDLE
            elif value.kind == 'string_value':
                value.value = _normalize_field(field_name, value.value)
                return IDLE
        return IDLE


def normalize_graphql_query(query: str) -> str:
    ast = parse(query)
    new_ast = visit(ast, NormalizeVisitor())
    return print_ast(new_ast)


def denormalize_graphql_result(obj: Dict[str, Any]) -> None:
    for key, value in obj.items():
        if isinstance(value, str):
            obj[key] = _denormalize_field(key, value)
        elif isinstance(value, dict):
            denormalize_graphql_result(value)
        elif isinstance(value, list):
            new_list = []
            for sub_value in value:
                if isinstance(sub_value, str):
                    new_list.append(_denormalize_field(key, sub_value))
                elif isinstance(sub_value, dict):
                    denormalize_graphql_result(sub_value)
                    new_list.append(sub_value)
                else:
                    new_list.append(sub_value)
            obj[key] = new_list


if __name__ == '__main__':
    PRODUCT_QUERY = '''
    {
        characters(filter: {tagList: ["治疗", "防护", "输出"], rarity: 6, position: "高台", profession: "术士"}) {
            name
        }
    }
'''
    print(normalize_graphql_query(PRODUCT_QUERY))

    result = {
        'position': 'RANGED',
        'profession': 'CASTER',
        'something': ['A', 'B'],
        'another': [
            {
                'subProfession': ['fighter', 'lord']
            }
        ]
    }
    denormalize_graphql_result(result)
    print(result)
