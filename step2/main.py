import uuid

from step2.graph.graph import get_graph
from langchain_core.messages import HumanMessage


def main():
    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "thread_id": thread_id,  # LangGraph memory를 위한 thread_id
        },
        "recursion_limit": 150  # 그래프에서 수행할 최대 단계 수
    }

    # 사용자 입출력
    print("질문을 입력해세요.")
    _printed = set()
    graph = get_graph()
    while True:
        query = input()
        events = graph.stream(
            {
                "messages": [HumanMessage(content=query)],
            },
            config,
            stream_mode="values"
        )
        for event in events:
            from step2.utils.utillities import _print_event
            _print_event(event, _printed)


if __name__ == "__main__":
    main()
