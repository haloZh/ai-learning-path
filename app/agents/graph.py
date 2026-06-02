"""LangGraph 编排:三条链。

- diagnose 链:diagnose -> plan,首次启动跑一次,返回 mastery + path(快)
- evaluate 链:evaluate 单节点,对 path 做客观评分。
  · 拆出来后由 /diagnose 用 BackgroundTasks 异步调用,不阻塞主响应。
- optimize 链:optimize 单节点,学习过程中每次交互触发
"""

from langgraph.graph import END, StateGraph

from .nodes import diagnose_node, evaluate_node, optimize_node, plan_node
from .state import AgentState


def build_diagnose_graph():
    """诊断主链:只跑 diagnose -> plan,尽快返回路径给用户。"""
    g = StateGraph(AgentState)
    g.add_node("diagnose", diagnose_node)
    g.add_node("plan", plan_node)
    g.set_entry_point("diagnose")
    g.add_edge("diagnose", "plan")
    g.add_edge("plan", END)
    return g.compile()


def build_evaluate_graph():
    """评价链:单独的 evaluate 节点,后台异步调用。"""
    g = StateGraph(AgentState)
    g.add_node("evaluate", evaluate_node)
    g.set_entry_point("evaluate")
    g.add_edge("evaluate", END)
    return g.compile()


def build_optimize_graph():
    g = StateGraph(AgentState)
    g.add_node("optimize", optimize_node)
    g.set_entry_point("optimize")
    g.add_edge("optimize", END)
    return g.compile()
