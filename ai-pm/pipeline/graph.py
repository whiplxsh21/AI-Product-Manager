from langgraph.graph import END, StateGraph

from config import config
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

    graph.add_edge("prd", "bdd")
    graph.add_edge("bdd", "jira_format")
    graph.add_edge("jira_format", "wireframe")
    graph.add_edge("wireframe", "ux_flow")
    graph.add_edge("ux_flow", END)

    if config.hitl_enabled:
        from langgraph.checkpoint.sqlite import SqliteSaver
        checkpointer = SqliteSaver.from_conn_string("./pipeline_checkpoints.db")
        return graph.compile(checkpointer=checkpointer)

    return graph.compile()


compiled_graph = build_graph()
