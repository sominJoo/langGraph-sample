import datetime
import os

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig

from step1.agent.state import State
from step1.settings import LLM, TAVILY_API_KEY
from step1.tools.car_rental import search_car_rentals, book_car_rental, update_car_rental, \
    cancel_car_rental
from step1.tools.excursions import search_trip_recommendations, book_excursion, update_excursion, \
    cancel_excursion
from step1.tools.flights import search_flights, update_ticket_to_new_flight, cancel_ticket, \
    fetch_user_flight_information
from step1.tools.hotels import search_hotels, book_hotel, update_hotel, cancel_hotel
from step1.tools.policies import lookup_policy

os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY


class Assistant:
    """
    graph Node : 사용자 입력 값(*이전 대화 내용을 포함해서 반환)
    """
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            thread_id = configuration.get("thread_id", None)
            state = {**state, "user_info": thread_id}  # memory 유지를 위한 thread_id를 user_info로 저장
            result = self.runnable.invoke(state)
            # 실제 응답을 위한 빈응답일 경우 다시 결과 확인
            if not result.tool_calls and (
                    not result.content
                    or isinstance(result.content, list)
                    and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


class SimpleAgent:
    @staticmethod
    def tools():
        """
        Tools 정의 - 이전에 정의해둔 tools 모두 정의
        :return: 사용한 tool 배열
        """
        part_1_tools = [
            TavilySearchResults(max_results=1),
            lookup_policy,
            fetch_user_flight_information,
            search_flights,
            update_ticket_to_new_flight,
            cancel_ticket,
            search_car_rentals,
            book_car_rental,
            update_car_rental,
            cancel_car_rental,
            search_hotels,
            book_hotel,
            update_hotel,
            cancel_hotel,
            search_trip_recommendations,
            book_excursion,
            update_excursion,
            cancel_excursion,
        ]
        return part_1_tools

    def setting(self) -> Runnable:
        """
        LLM Chain 정의
        :return: Runnable(LLM + Prompt + Tool)
        """
        # Prompt 정의
        primary_assistant_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful customer support assistant for Swiss Airlines. "
                    "Use the provided tools to search for flights, company policies, and other information to assist "
                    "the user's queries."
                    " When searching, be persistent. Expand your query bounds if the first search returns no results. "
                    " If a search comes up empty, expand your search before giving up."
                    "\n\nCurrent user:\n\n{user_info}\n"
                    "\nCurrent time: {time}.",
                ),
                ("placeholder", "{messages}"),
            ]
        ).partial(time=datetime.datetime.now())

        # Prompt + LLM 조합
        return primary_assistant_prompt | LLM.bind_tools(self.tools())
