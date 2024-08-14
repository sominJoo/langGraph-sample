import os
import shutil

import requests

from db_setting import DBSetting
from step1.agent.graph_part1 import run_graph


def main():
    local_db_file = "travel2.sqlite"

    # DB 파일이 존재하지 않는다면 URL에서 다운로드 진행해 local_db 파일 생성
    db_url = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"
    backup_file = "travel2.backup.sqlite"
    overwrite = False
    if overwrite or not os.path.exists(local_db_file):
        response = requests.get(db_url)
        response.raise_for_status()  # Ensure the request was successful
        with open(local_db_file, "wb") as f:
            f.write(response.content)
        shutil.copy(local_db_file, backup_file)

    db = DBSetting()
    pandas_module = db.connect_db(local_db_file)  # pd 값을 받아옴
    # pandas_module로 pd 사용 가능
    print("pandas_module = ", pandas_module)
    run_graph(local_db_file)


#     TODO: 사용자 인풋 받기

if __name__ == "__main__":
    main()
