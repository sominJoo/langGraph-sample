from langchain_core.tools import tool
from langchain_community.utilities import SQLDatabase

from step2 import settings


@tool
def db_query_tool(query: str) -> str:
    """
    데이터베이스에 대해 SQL 쿼리를 실행하고 결과를 가져옵니다.
    쿼리가 올바르지 않으면 오류 메시지가 반환됩니다.
    오류가 반환되면 쿼리를 다시 작성하고 쿼리를 확인한 후 다시 시도합니다.
    """
    db = db_connection()
    result = db.run_no_throw(query)
    if not result:
        return "Error: Query failed. Please rewrite your query and try again."
    return result


def db_connection():
    """
    DB 연결
    :return:
    """
    sql_url = (f"postgresql+psycopg2://"
               f"{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}"
               f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}"
               f"/{settings.POSTGRES_DATABASE}"
               f"?options=-csearch_path%3D{settings.POSTGRES_SCHEMA}")
    db = SQLDatabase.from_uri(sql_url)

    return db
