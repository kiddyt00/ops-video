"""Built-in knowledge base seed data."""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..knowledge_crud import knowledge_crud

SEED_KNOWLEDGE: List[Dict[str, Any]] = [
    {
        "name": "chinese-names",
        "category": "name",
        "description": "中文姓名生成字典：常见姓氏、男女名用字及含义",
        "content": """## 中文姓名字典\n\n### 常见姓氏（50个）\n李、王、张、刘、陈、杨、赵、黄、周、吴、徐、孙、胡、朱、高、林、何、郭、马、罗、\n梁、宋、郑、谢、韩、唐、冯、于、董、萧、程、曹、袁、邓、许、傅、沈、曾、彭、吕、\n苏、卢、蒋、蔡、贾、丁、魏、薛、叶、阎\n\n### 男性名用字（30个）\n轩、宇、晨、浩、然、博、文、杰、铭、泽、昊、毅、锋、涛、彬、哲、翰、睿、彦、恒、\n辰、凯、铭、瑞、霖、旭、烨、鹏、骏、渊\n\n### 女性名用字（30个）\n涵、嫣、瑶、璇、萱、琳、悦、婷、婉、倩、怡、璐、彤、菲、晴、瑜、洁、秀、娟、莉、\n蓉、梅、兰、雪、月、诗、画、思、语、梦\n\n### 取名规则\n- 修仙题材：多用"玄、灵、道、仙、清、虚、天、云、星、月"\n- 武侠题材：多用"风、剑、影、霜、雪、寒、龙、凤、虎、鹰"\n- 都市题材：使用现代常用名即可""",
    },
    {
        "name": "chinese-place-names",
        "category": "world",
        "description": "中文地名生成字典：前缀、后缀和命名模板",
        "content": """## 中文地名字典\n\n### 地名前缀（20个）\n青云、紫霞、碧落、苍梧、玉虚、凌霄、太初、混元、无极、清风、\n白云、黑水、赤焰、翠微、金鳌、银月、玄冥、九幽、万象、归元\n\n### 地名后缀（15个）\n城、山、谷、峰、崖、洞、湖、海、渊、阁、殿、宗、门、派、坊\n\n### 命名规则\n- 宗门：前缀+宗/门/派\n- 城市：前缀+城\n- 险地：前缀+谷/渊/崖\n- 仙山：前缀+山/峰""",
    },
    {
        "name": "chinese-dynasties",
        "category": "world",
        "description": "中国古代朝代设定模板：制度、服饰、科技水平参考",
        "content": """## 朝代设定模板\n\n| 朝代 | 制度 | 科技 | 适合题材 |\n|------|------|------|---------|\n| 架空上古 | 部落联盟 | 原始+灵力 | 洪荒修仙 |\n| 封神时代 | 分封制 | 青铜+道法 | 封神修仙 |\n| 仙侠黄金 | 帝国+宗门 | 灵力鼎盛 | 古典仙侠 |\n| 架空盛唐 | 三省六部 | 繁荣盛世 | 历史奇幻 |\n| 架空宋明 | 重文轻武 | 火药萌芽 | 文官修仙 |\n| 末法时代 | 高度集权 | 冷热交替 | 末法修仙 |\n| 赛博纪元 | 赛博政权 | AI/义体 | 赛博修仙 |""",
    },
    {
        "name": "xianxia-world-rules",
        "category": "world",
        "description": "修仙世界观设定指南",
        "content": """## 修仙世界设定\n\n### 境界体系\n1. 炼气期 2. 筑基期 3. 金丹期 4. 元婴期 5. 化神期\n6. 炼虚期 7. 合体期 8. 大乘期 9. 渡劫期\n\n### 宗门结构\n太上长老→掌门→长老→执事→内门→外门→杂役\n\n### 灵石货币\n下品(日常) < 中品(修炼) < 上品(高阶) < 极品(稀世)\n\n### 宗门类型\n剑修、丹修、阵修、符修、体修""",
    },
    {
        "name": "scifi-world-rules",
        "category": "world",
        "description": "科幻世界观设定指南",
        "content": """## 科幻世界设定\n\n### 科技等级\nLv1行星 → Lv2恒星 → Lv3星系 → Lv4银河 → Lv5宇宙\n\n### 星际政治\n银河联邦 / 帝国制 / 企业联合 / 蜂巢意识 / 法外之地\n\n### 常见元素\n义体改造、脑机接口、太空电梯、基因编辑、AI伦理分级""",
    },
    {
        "name": "story-structures",
        "category": "genre",
        "description": "7种经典叙事结构",
        "content": """## 叙事结构\n\n1. **英雄之旅**（12步）：修仙/奇幻/冒险\n2. **三幕式**：几乎所有类型\n3. **起承转合**：短篇/漫剧单集\n4. **七点式**：中长篇\n5. **拯救猫咪**：商业漫剧\n6. **非线性**：悬疑/文艺\n7. **单元剧**：漫剧系列""",
    },
]


def seed_knowledge(db: Session) -> int:
    created = 0
    for item in SEED_KNOWLEDGE:
        existing = knowledge_crud.get_by_name(db, item["name"])
        if existing:
            continue
        knowledge_crud.create(db, name=item["name"], category=item["category"],
                              content=item["content"], description=item.get("description"),
                              built_in=True)
        created += 1
    return created
