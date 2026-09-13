"""Multi-Agent Clinical Decision Support LangGraph workflow."""

from langgraph.graph import StateGraph, START, END
from src.schemas import ClinicalGraphState
from src.agents import (
    lab_agent_node,
    pharma_agent_node,
    history_agent_node,
    triage_coordinator_node,
)


def create_clinical_graph():
    """Build and compile the scatter-gather clinical decision support graph."""
    builder = StateGraph(ClinicalGraphState)

    # 1. Register specialized agent nodes
    builder.add_node("lab_agent", lab_agent_node)
    builder.add_node("pharma_agent", pharma_agent_node)
    builder.add_node("history_agent", history_agent_node)
    builder.add_node("triage_coordinator", triage_coordinator_node)

    # 2. Scatter: Fan-out from START to specialized parallel agents
    builder.add_edge(START, "lab_agent")
    builder.add_edge(START, "pharma_agent")
    builder.add_edge(START, "history_agent")

    # 3. Gather: Fan-in from specialist agents to Lead Triage Coordinator
    builder.add_edge("lab_agent", "triage_coordinator")
    builder.add_edge("pharma_agent", "triage_coordinator")
    builder.add_edge("history_agent", "triage_coordinator")

    # 4. Terminal edge
    builder.add_edge("triage_coordinator", END)

    return builder.compile()


# Pre-compiled clinical graph instance
clinical_graph = create_clinical_graph()
