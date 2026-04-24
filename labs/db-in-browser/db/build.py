#!/usr/bin/env python3
"""
构建示例 SQLite 数据库，模拟《史记》实体数据。
生产环境用你自己的知识库数据替换 SAMPLE_ENTITIES 即可。

关键点：
- page_size 设为 4096（默认，且与前端 requestChunkSize 对齐）
- 为每个查询列建索引，否则浏览器端会下载整张表
- 用 COVERING INDEX 让常见查询只读索引页，不读数据页
"""

import sqlite3
import os

OUT = os.path.join(os.path.dirname(__file__), "shiji.sqlite3")

# 示例数据：真实使用时从你的 KB 导入
SAMPLE_ENTITIES = [
    # (id, name, type, dynasty, birth_year, death_year, description)
    (1,  "秦始皇",   "person", "秦", -259, -210, "名政，秦庄襄王之子，统一六国，建立秦朝。"),
    (2,  "刘邦",     "person", "汉", -256, -195, "字季，沛丰邑人，汉朝开国皇帝。"),
    (3,  "项羽",     "person", "楚", -232, -202, "名籍，字羽，下相人，西楚霸王。"),
    (4,  "韩信",     "person", "汉", -231, -196, "淮阴人，汉初三杰之一，齐王、楚王。"),
    (5,  "张良",     "person", "汉", -250, -186, "字子房，汉初三杰之一，留侯。"),
    (6,  "萧何",     "person", "汉", -257, -193, "沛县人，汉初三杰之一，相国。"),
    (7,  "吕后",     "person", "汉", -241, -180, "名雉，字娥姁，汉高祖皇后。"),
    (8,  "李斯",     "person", "秦", -284, -208, "楚上蔡人，秦朝丞相。"),
    (9,  "赵高",     "person", "秦", None,  -207, "秦朝宦官，沙丘之变主谋。"),
    (10, "扶苏",     "person", "秦", None,  -210, "秦始皇长子。"),
    (11, "胡亥",     "person", "秦", -230, -207, "秦始皇幼子，秦二世。"),
    (12, "孔子",     "person", "春秋", -551, -479, "名丘，字仲尼，鲁国陬邑人，儒家学派创始人。"),
    (13, "孟子",     "person", "战国", -372, -289, "名轲，邹国人，儒家代表人物。"),
    (14, "商鞅",     "person", "战国", -395, -338, "卫国人，法家代表，秦国变法。"),
    (15, "白起",     "person", "战国", None,  -257, "秦国名将，战国四名将之一。"),
    (16, "廉颇",     "person", "战国", None,  None, "赵国名将，战国四名将之一。"),
    (17, "蔺相如",   "person", "战国", None,  None, "赵国上卿，完璧归赵、渑池之会。"),
    (18, "苏秦",     "person", "战国", None,  -284, "洛阳人，合纵家，佩六国相印。"),
    (19, "张仪",     "person", "战国", None,  -309, "魏国人，连横家，秦相。"),
    (20, "荆轲",     "person", "战国", None,  -227, "卫国人，刺秦王。"),

    (101, "秦",      "state", "先秦", None, None, "战国七雄之一，后统一六国。"),
    (102, "汉",      "state", "汉",   None, None, "汉朝。"),
    (103, "楚",      "state", "先秦", None, None, "战国七雄之一。"),
    (104, "赵",      "state", "先秦", None, None, "战国七雄之一。"),
    (105, "齐",      "state", "先秦", None, None, "战国七雄之一。"),
    (106, "魏",      "state", "先秦", None, None, "战国七雄之一。"),
    (107, "韩",      "state", "先秦", None, None, "战国七雄之一。"),
    (108, "燕",      "state", "先秦", None, None, "战国七雄之一。"),
    (109, "鲁",      "state", "春秋", None, None, "春秋时期诸侯国。"),

    (201, "咸阳",    "place", "秦", None, None, "秦朝都城。"),
    (202, "长安",    "place", "汉", None, None, "汉朝都城。"),
    (203, "彭城",    "place", "楚", None, None, "项羽所定楚都。"),
    (204, "邯郸",    "place", "赵", None, None, "赵国都城。"),

    (301, "史记",    "work",  "汉", None, None, "司马迁所著纪传体通史。"),
    (302, "论语",    "work",  "春秋", None, None, "孔门弟子记录孔子言行。"),
]

def build():
    if os.path.exists(OUT):
        os.remove(OUT)

    conn = sqlite3.connect(OUT)
    c = conn.cursor()

    # page_size 必须在建任何表之前设置
    c.execute("PRAGMA page_size = 4096")
    c.execute("PRAGMA journal_mode = DELETE")  # 不要 WAL，静态托管场景

    c.execute("""
        CREATE TABLE entity (
            id          INTEGER PRIMARY KEY,
            name        TEXT    NOT NULL,
            type        TEXT    NOT NULL,
            dynasty     TEXT,
            birth_year  INTEGER,
            death_year  INTEGER,
            description TEXT
        )
    """)

    c.executemany(
        "INSERT INTO entity VALUES (?, ?, ?, ?, ?, ?, ?)",
        SAMPLE_ENTITIES
    )

    # 关键：按 type 过滤的 covering index
    # 浏览器端按 type 查询时只需读索引页，不用读 entity 表
    c.execute("""
        CREATE INDEX idx_entity_type_name
        ON entity (type, name, id, dynasty, birth_year, death_year)
    """)

    # 按 name 前缀搜索的索引
    c.execute("CREATE INDEX idx_entity_name ON entity (name)")

    # 按朝代过滤
    c.execute("CREATE INDEX idx_entity_dynasty ON entity (dynasty, type, name)")

    # VACUUM 以确保 page layout 紧凑
    conn.commit()
    c.execute("VACUUM")
    conn.close()

    size = os.path.getsize(OUT)
    print(f"Built {OUT} ({size:,} bytes)")
    print(f"Rows: {len(SAMPLE_ENTITIES)}")

if __name__ == "__main__":
    build()
