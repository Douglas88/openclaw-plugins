#!/usr/bin/env python3
"""
Manus Task Orchestrator — Break complex tasks into parallel subtasks
======================================================================
Given a complex goal, decomposes into subtasks, spawns agents, collects results.

Usage: python3 manus_orchestrator.py "Research AI coding tools and create comparison report"
"""

import sys, json

TEMPLATES = {
    "research": {
        "phases": ["search", "deep_read", "synthesize", "report"],
        "tools": ["web_search", "web_fetch", "reasoning-engine", "doc-generator"],
        "parallel": ["search"]  # Can search multiple angles in parallel
    },
    "build": {
        "phases": ["plan", "implement", "test", "review", "deploy"],
        "tools": ["update_plan", "coding-agent", "test-generator", "code-review"],
        "parallel": ["implement", "test"]
    },
    "analyze": {
        "phases": ["gather", "process", "visualize", "insights"],
        "tools": ["sqlite MCP", "exec python", "data-pipeline", "doc-generator"],
        "parallel": ["gather", "process"]
    },
    "automate": {
        "phases": ["observe", "plan_steps", "execute", "verify"],
        "tools": ["desktop-automation", "browser-automation", "filesystem MCP"],
        "parallel": []
    },
    "full": {
        "phases": ["understand", "plan", "research", "build", "test", "deliver"],
        "tools": ["all"],
        "parallel": ["research", "build"]
    }
}


def decompose(task: str) -> dict:
    """Analyze task and select template."""
    task_lower = task.lower()
    
    if any(w in task_lower for w in ["research", "compare", "survey", "find", "analyze"]):
        template = "research"
    elif any(w in task_lower for w in ["build", "create", "develop", "code", "implement"]):
        template = "build"
    elif any(w in task_lower for w in ["csv", "sql", "chart", "report", "statistics"]):
        template = "analyze"
    elif any(w in task_lower for w in ["automate", "click", "browse", "fill form", "desktop"]):
        template = "automate"
    else:
        template = "full"
    
    t = TEMPLATES[template]
    
    # Generate subtasks
    subtasks = []
    for i, phase in enumerate(t["phases"]):
        subtasks.append({
            "id": f"phase_{i+1}",
            "name": phase.upper(),
            "description": f"Complete the {phase} phase",
            "parallel": phase in t["parallel"],
            "tools": t["tools"]
        })
    
    return {
        "task": task,
        "template": template,
        "phases": len(subtasks),
        "parallel_phases": t["parallel"],
        "subtasks": subtasks,
        "execution_plan": f"Execute phases sequentially, with {t['parallel']} running in parallel"
    }


def main():
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Research AI coding tools"
    plan = decompose(task)
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
