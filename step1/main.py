import os
import shutil
import requests
import uuid

from db_setting import DBSetting
from step1.agent.graph_part1 import run_graph
from step1.tools.utils.utillities import _print_event


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
    db.connect_db(local_db_file)

    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "thread_id": thread_id,  # LangGraph memory를 위한 thread_id
        }
    }

    # 사용자 입출력
    print("여행 예약정보에 대한 질문을 입력해세요.")
    _printed = set()
    part_1_graph = run_graph()
    while True:
        query = input()
        events = part_1_graph.stream(
            {"messages": ("user", query)}, config, stream_mode="values"
        )
        for event in events:
            _print_event(event, _printed)


if __name__ == "__main__":
    main()
