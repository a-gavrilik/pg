import json
import pandas as pd
import mysql.connector

# -----------------------------
# 1. Подключение к БД
# -----------------------------
conn = mysql.connector.connect(
    user='bi',
    password='Chie4AhS3huoS7dae8Joephoh',
    host='172.16.22.14',
    port='3307',
    database='crm_level_v1',
    charset="utf8mb4"
)

cursor = conn.cursor()
cursor.execute("""
        SELECT daps.l_id,
               jt.lat,
               jt.lon,
               jt.ord AS point_order
        FROM delivery_area_polygons p
                 JOIN delivery_area_polygon_settings daps ON daps.id = p.id
                 JOIN JSON_TABLE(
                p.data,
                '$[*]' COLUMNS (
                    ord FOR ORDINALITY,
                    lat DOUBLE PATH '$[0]',
                    lon DOUBLE PATH '$[1]'
                    )
                      ) jt
        WHERE daps.l_id IS NOT NULL
        ORDER BY daps.l_id, jt.ord
        """)
result = cursor.fetchall()
df = pd.DataFrame(
    result,
    columns=["l_id", "lat", "lon", "point_order"]
)
conn.close()

# -----------------------------
# 2. Группировка
# -----------------------------
polygons = []

for l_id, group in df.groupby("l_id"):
    coords = group[["lat", "lon"]].values.tolist()

    polygons.append({
        "l_id": l_id,
        "coords": coords
    })

# -----------------------------
# 3. JSON
# -----------------------------
with open("polygons.json", "w", encoding="utf-8") as f:
    json.dump({"polygons": polygons}, f, ensure_ascii=False)

import os
from github import Github
import base64

# -----------------------------
# 4. Загрузка в GitHub
# -----------------------------

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO_NAME = "a-gavrilik/pg"  # owner/repo
FILE_PATH = "polygons.json"
COMMIT_MESSAGE = "Auto update polygons.json"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

with open("polygons.json", "rb") as f:
    content = f.read()

try:
    # если файл уже есть — обновляем
    existing_file = repo.get_contents(FILE_PATH)
    repo.update_file(
        path=FILE_PATH,
        message=COMMIT_MESSAGE,
        content=content,
        sha=existing_file.sha
    )
    print("polygons.json обновлён в GitHub")

except:
    # если файла нет — создаём
    repo.create_file(
        path=FILE_PATH,
        message=COMMIT_MESSAGE,
        content=content
    )
    print("polygons.json создан в GitHub")