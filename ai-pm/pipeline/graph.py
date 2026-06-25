from langgraph.graph import END, StateGraph

from pipeline.nodes.bdd_stories import bdd_node
from pipeline.nodes.checkpoint import checkpoint_node
from pipeline.nodes.framework import framework_node
from pipeline.nodes.ingestion import ingestion_node
from pipeline.nodes.jira_format import jira_format_node
from pipeline.nodes.prd import prd_node
from pipeline.nodes.ux_flow import ux_flow_node
from pipeline.nodes.wireframe import wireframe_node
from pipeline.state import PipelineState


def _route_after_checkpoint(state: PipelineState) -> str:
    if state["approval_status"] in ("auto_approved", "approved"):
        return "prd"
    return END


def _route_after_prd(state: PipelineState) -> str:
    # When PRD review is enabled, stop after PRD so the user can review/edit it
    # before the remaining deliverables are generated. The run is resumed via
    # services.project_service.continue_after_prd_review(), which runs the
    # remaining nodes directly.
    if state.get("prd_review") and not state.get("prd_approved"):
        return END
    return "bdd"


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("ingestion", ingestion_node)
    graph.add_node("framework", framework_node)
    graph.add_node("checkpoint", checkpoint_node)
    graph.add_node("prd", prd_node)
    graph.add_node("bdd", bdd_node)
    graph.add_node("jira_format", jira_format_node)
    graph.add_node("wireframe", wireframe_node)
    graph.add_node("ux_flow", ux_flow_node)

    graph.set_entry_point("ingestion")
    graph.add_edge("ingestion", "framework")
    graph.add_edge("framework", "checkpoint")

    graph.add_conditional_edges("checkpoint", _route_after_checkpoint, {
        "prd": "prd",
        END: END,
    })

    graph.add_conditional_edges("prd", _route_after_prd, {
        "bdd": "bdd",
        END: END,
    })

    graph.add_edge("bdd", "jira_format")
    graph.add_edge("jira_format", "wireframe")
    graph.add_edge("wireframe", "ux_flow")
    graph.add_edge("ux_flow", END)

    return graph.compile()


compiled_graph = build_graph()
