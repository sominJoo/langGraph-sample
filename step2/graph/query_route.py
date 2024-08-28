def query_route(state):
    # 상태 정보를 기반으로 다음 단계를 결정하는 라우터 함수
    messages = state["messages"]
    last_message = messages[-1]

    if "function_call" in last_message.additional_kwargs:
        # 이전 에이전트가 도구를 호출함
        return "call_tool"

    if "FINAL ANSWER" in last_message.content:
        # 어느 에이전트든 작업이 끝났다고 결정함
        return "end"
    return "continue"
