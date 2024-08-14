import datetime
import os

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig

from step1.agent.state import State
from step1.settings import LLM, TAVILY_API_KEY
from step1.tools.car_rental import CarRentalTools
from step1.tools.excursions import Excursions
from step1.tools.flights import FlightsTools
from step1.tools.hotels import HotelsTools
from step1.tools.policies import lookup_policy

os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            passenger_id = configuration.get("passenger_id", None)
            state = {**state, "user_info": passenger_id}
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
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
    def __init__(self, db_path: str):
        self.db_path = db_path

    def tools(self):
        crt = CarRentalTools(self.db_path)
        flights = FlightsTools(self.db_path)
        excur = Excursions(self.db_path)
        hotels = HotelsTools(self.db_path)
        # Tools 정의 - 이전에 정의해둔 tools 모두 정의
        part_1_tools = [
            TavilySearchResults(max_results=1),
            lookup_policy,
            flights.fetch_user_flight_information,
            flights.search_flights,
            flights.update_ticket_to_new_flight,
            flights.cancel_ticket,
            crt.search_car_rentals,
            crt.book_car_rental,
            crt.update_car_rental,
            crt.cancel_car_rental,
            hotels.search_hotels,
            hotels.book_hotel,
            hotels.update_hotel,
            hotels.cancel_hotel,
            excur.search_trip_recommendations,
            excur.book_excursion,
            excur.update_excursion,
            excur.cancel_excursion,
        ]
        return part_1_tools

    def setting(self) -> Runnable:
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

        print("LLM", LLM)

        # Prompt + LLM 조합
        return primary_assistant_prompt | LLM.bind_tools(self.tools())
