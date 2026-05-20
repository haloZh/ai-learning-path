"""LangGraph 编排:两条独立链。

- diagnose 链:diagnose -> plan,首次启动跑一次,产出初版路径
- optimize 链:optimize 单节点,学习过程中每次交互触发
"""

from langgraph.graph import END, StateGraph

from .nodes import diagnose_node, optimize_node, plan_node
from .state import AgentState


def build_diagnose_graph():
    g = StateGraph(AgentState)
    g.add_node("diagnose", diagnose_node)
    g.add_node("plan", plan_node)
    g.set_entry_point("diagnose")
    g.add_edge("diagnose", "plan")
    g.add_edge("plan", END)
    return g.compile()


def build_optimize_graph():
    g = StateGraph(AgentState)
    g.add_node("optimize", optimize_node)
    g.set_entry_point("optimize")
    g.add_edge("optimize", END)
    return g.compile()
