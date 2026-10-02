from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import WeatherBotState
from app.graph.nodes import (
    understand_query,
    resolve_location_node,
    fetch_weather_node,
    select_forecast_node,
    match_sops_node,
    generate_answer_node,
    no_sop_node,
    failure_node,
)


def route_after_understanding(state: WeatherBotState):
    if state.get("error"):
        return "failure"
    return "resolve_location"


def route_after_location(state: WeatherBotState):
    if state.get("error") or not state.get("coordinates"):
        return "failure"
    return "fetch_weather"


def route_after_weather(state: WeatherBotState):
    if state.get("error") or not state.get("weather_available"):
        return "failure"
    return "select_forecast"


def route_after_forecast(state: WeatherBotState):
    if state.get("error") or not state.get("weather_available"):
        return "failure"
    return "match_sops"


def route_after_matching(state: WeatherBotState):
    if state.get("match_found"):
        return "generate_answer"
    return "no_sop"


def build_graph():
    workflow = StateGraph(WeatherBotState)

    # Register nodes
    workflow.add_node("understand_query", understand_query)
    workflow.add_node("resolve_location", resolve_location_node)
    workflow.add_node("fetch_weather", fetch_weather_node)
    workflow.add_node("select_forecast", select_forecast_node)
    workflow.add_node("match_sops", match_sops_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("no_sop", no_sop_node)
    workflow.add_node("failure", failure_node)

    # Starting point
    workflow.add_edge(START, "understand_query")

    # Conditional branching
    workflow.add_conditional_edges(
        "understand_query",
        route_after_understanding,
        {
            "failure": "failure",
            "resolve_location": "resolve_location",
        },
    )

    workflow.add_conditional_edges(
        "resolve_location",
        route_after_location,
        {
            "failure": "failure",
            "fetch_weather": "fetch_weather",
        },
    )

    workflow.add_conditional_edges(
    "fetch_weather",
    route_after_weather,
    {
        "failure": "failure",
        "select_forecast": "select_forecast",
    },
)

    workflow.add_conditional_edges(
        "select_forecast",
        route_after_forecast,
        {
            "failure": "failure",
            "match_sops": "match_sops",
        },
    )

    workflow.add_conditional_edges(
        "match_sops",
        route_after_matching,
        {
            "generate_answer": "generate_answer",
            "no_sop": "no_sop",
        },
    )

    # Terminal paths
    workflow.add_edge("generate_answer", END)
    workflow.add_edge("no_sop", END)
    workflow.add_edge("failure", END)

    # In-memory session persistence
    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)


graph = build_graph()