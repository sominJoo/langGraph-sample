from db_setting import DBSetting
from step1.agent.graph_part1 import run_graph


def main():
    local_db_file = "travel2.sqlite"

    db = DBSetting()
    pandas_module = db.connect_db(local_db_file)  # pd 값을 받아옴
    # pandas_module로 pd 사용 가능
    print("pandas_module = ", pandas_module)
    run_graph(local_db_file)


#     TODO: 사용자 인풋 받기

if __name__ == "__main__":
    main()
