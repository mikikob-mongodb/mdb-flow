"""
Comprehensive Memory System Audit Script

Tests all 8 memory capabilities for the complex demo flow.
"""

from shared.db import get_db
from memory.manager import MemoryManager
from shared.embeddings import embed_query
import json

def print_section(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}\n")

def check_status(condition, message):
    status = "✓" if condition else "✗"
    print(f"  {status} {message}")
    return condition

def main():
    db = get_db()
    mm = MemoryManager(db=db, embedding_fn=embed_query)

    session_id = "audit-session"
    user_id = "demo-user"

    results = {}

    # ═══════════════════════════════════════════════════════════
    # 1. WORKING MEMORY
    # ═══════════════════════════════════════════════════════════
    print_section("1️⃣ WORKING MEMORY")

    working_checks = []

    # Can store context
    try:
        mm.update_session_context(
            session_id=session_id,
            user_id=user_id,
            updates={"focus": "gaming demo", "context": "NPC memory systems"}
        )
        working_checks.append(check_status(True, "Can store session context"))
    except Exception as e:
        working_checks.append(check_status(False, f"Cannot store context: {e}"))

    # Can retrieve context
    try:
        ctx = mm.read_session_context(session_id)
        has_data = ctx and ctx.get("focus") == "gaming demo"
        working_checks.append(check_status(has_data, f"Can retrieve context: {ctx if has_data else 'None'}"))
    except Exception as e:
        working_checks.append(check_status(False, f"Cannot retrieve: {e}"))

    # Check coordinator integration
    try:
        from agents import coordinator
        coord = coordinator(session_id=session_id, user_id=user_id, memory_config={"context_injection": True})
        has_method = hasattr(coord, '_build_context_injection')
        working_checks.append(check_status(has_method, "Coordinator has context injection"))
    except Exception as e:
        working_checks.append(check_status(False, f"Coordinator error: {e}"))

    results["working_memory"] = "✅" if all(working_checks) else "⚠️"

    # ═══════════════════════════════════════════════════════════
    # 2. SEMANTIC MEMORY (Knowledge Cache)
    # ═══════════════════════════════════════════════════════════
    print_section("2️⃣ SEMANTIC MEMORY (Knowledge Cache)")

    semantic_checks = []

    # Can store knowledge
    try:
        mm.cache_knowledge(
            user_id=user_id,
            query="gaming NPC systems",
            result="NPCs use persistent state to remember player interactions",
            source="web_search",
            url="https://example.com/npc-memory"
        )
        semantic_checks.append(check_status(True, "Can cache knowledge"))
    except Exception as e:
        semantic_checks.append(check_status(False, f"Cannot cache: {e}"))

    # Can retrieve knowledge
    try:
        cached = mm.search_knowledge(user_id=user_id, query="NPC memory", limit=1)
        has_results = len(cached) > 0
        semantic_checks.append(check_status(has_results, f"Can search knowledge: {len(cached)} results"))
    except Exception as e:
        semantic_checks.append(check_status(False, f"Cannot search: {e}"))

    # Check if knowledge stats exist
    try:
        stats = mm.get_knowledge_stats(user_id)
        has_stats = stats.get("total_items", 0) > 0
        semantic_checks.append(check_status(has_stats, f"Knowledge stats: {stats}"))
    except Exception as e:
        semantic_checks.append(check_status(False, f"Stats error: {e}"))

    results["semantic_memory"] = "✅" if all(semantic_checks) else "⚠️"

    # ═══════════════════════════════════════════════════════════
    # 3. PROCEDURAL MEMORY (Templates)
    # ═══════════════════════════════════════════════════════════
    print_section("3️⃣ PROCEDURAL MEMORY (Templates)")

    procedural_checks = []

    # Check existing templates
    templates = list(db.memory_procedural.find({
        "user_id": user_id,
        "rule_type": "template"
    }))
    template_count = len(templates)
    procedural_checks.append(check_status(template_count > 0, f"Has {template_count} templates"))

    if templates:
        for tmpl in templates:
            print(f"    • {tmpl.get('name', 'Unknown')}")

    # Check if can retrieve template
    try:
        prd_template = mm.get_procedural_rule(
            user_id=user_id,
            rule_type="template",
            name="PRD Template"
        )
        procedural_checks.append(check_status(prd_template is not None, "Can retrieve template by name"))
    except Exception as e:
        procedural_checks.append(check_status(False, f"Cannot retrieve: {e}"))

    # Check workflows
    workflows = mm.get_workflows(user_id=user_id)
    procedural_checks.append(check_status(len(workflows) > 0, f"Has {len(workflows)} workflows"))

    results["procedural_memory"] = "✅" if all(procedural_checks) else "⚠️"

    # ═══════════════════════════════════════════════════════════
    # 4. EPISODIC MEMORY (Action History)
    # ═══════════════════════════════════════════════════════════
    print_section("4️⃣ EPISODIC MEMORY (Action History)")

    episodic_checks = []

    # Can record action
    try:
        mm.record_action(
            user_id=user_id,
            session_id=session_id,
            action_type="create",
            entity_type="project",
            entity={"project_name": "Test Project"},
            metadata={"test": True}
        )
        episodic_checks.append(check_status(True, "Can record actions"))
    except Exception as e:
        episodic_checks.append(check_status(False, f"Cannot record: {e}"))

    # Can retrieve recent actions
    try:
        actions = mm.get_recent_actions(user_id=user_id, limit=5)
        has_actions = len(actions) > 0
        episodic_checks.append(check_status(has_actions, f"Can retrieve actions: {len(actions)} found"))
    except Exception as e:
        episodic_checks.append(check_status(False, f"Cannot retrieve: {e}"))

    # Check episodic summaries
    summary_count = db.memory_episodic.count_documents({"user_id": user_id})
    episodic_checks.append(check_status(summary_count > 0, f"Has {summary_count} episodic summaries"))

    results["episodic_memory"] = "✅" if all(episodic_checks) else "⚠️"

    # ═══════════════════════════════════════════════════════════
    # 5. SHARED MEMORY (Agent Handoffs)
    # ═══════════════════════════════════════════════════════════
    print_section("5️⃣ SHARED MEMORY (Agent Handoffs)")

    shared_checks = []

    # Can write handoff
    try:
        mm.write_handoff(
            session_id=session_id,
            user_id=user_id,
            source_agent="coordinator",
            target_agent="worklog",
            handoff_type="task_creation",
            payload={"project_name": "Test"},
            ttl=300
        )
        shared_checks.append(check_status(True, "Can write handoffs"))
    except Exception as e:
        shared_checks.append(check_status(False, f"Cannot write: {e}"))

    # Can read handoff
    try:
        handoff = mm.read_handoff(
            session_id=session_id,
            target_agent="worklog",
            consume=False
        )
        has_handoff = handoff is not None
        shared_checks.append(check_status(has_handoff, f"Can read handoffs: {handoff is not None}"))
    except Exception as e:
        shared_checks.append(check_status(False, f"Cannot read: {e}"))

    results["shared_memory"] = "✅" if all(shared_checks) else "⚠️"

    # ═══════════════════════════════════════════════════════════
    # 6. MCP INTEGRATION
    # ═══════════════════════════════════════════════════════════
    print_section("6️⃣ MCP INTEGRATION")

    mcp_checks = []

    # Check if MCP agent exists
    try:
        from agents.mcp_agent import MCPAgent
        mcp_agent = MCPAgent(user_id=user_id, session_id=session_id, db=db)
        mcp_checks.append(check_status(True, "MCP Agent available"))

        # Check if Tavily is configured
        has_tavily = hasattr(mcp_agent, 'tavily_search') or hasattr(mcp_agent, 'handle_request')
        mcp_checks.append(check_status(has_tavily, "Tavily search capability"))
    except Exception as e:
        mcp_checks.append(check_status(False, f"MCP Agent error: {e}"))

    # Check tool_discoveries collection
    discovery_count = db.tool_discoveries.count_documents({})
    mcp_checks.append(check_status(discovery_count >= 0, f"tool_discoveries collection: {discovery_count} docs"))

    results["mcp_integration"] = "✅" if all(mcp_checks) else "⚠️"

    # ═══════════════════════════════════════════════════════════
    # 7. PROJECT CREATION FROM TEMPLATES
    # ═══════════════════════════════════════════════════════════
    print_section("7️⃣ PROJECT CREATION FROM TEMPLATES")

    template_checks = []

    # Check if coordinator can access templates
    try:
        from agents import coordinator
        coord = coordinator(session_id=session_id, user_id=user_id)
        has_worklog = hasattr(coord, 'worklog_agent')
        template_checks.append(check_status(has_worklog, "Coordinator has worklog agent"))
    except Exception as e:
        template_checks.append(check_status(False, f"Coordinator error: {e}"))

    # Check if templates have task structure
    if templates:
        has_phases = any("phases" in t or "steps" in t or "tasks" in t for t in templates)
        template_checks.append(check_status(has_phases, "Templates have task structure"))

    results["template_project_creation"] = "✅" if all(template_checks) else "⚠️"

    # ═══════════════════════════════════════════════════════════
    # 8. COMPLEX QUERY HANDLING
    # ═══════════════════════════════════════════════════════════
    print_section("8️⃣ COMPLEX QUERY HANDLING")

    complex_checks = []

    # Check multi-step detection
    try:
        from agents import coordinator
        coord = coordinator(session_id=session_id, user_id=user_id)
        has_multi_step = hasattr(coord, '_classify_multi_step_intent')
        complex_checks.append(check_status(has_multi_step, "Has multi-step intent detection"))

        has_execute = hasattr(coord, '_execute_multi_step')
        complex_checks.append(check_status(has_execute, "Has multi-step executor"))
    except Exception as e:
        complex_checks.append(check_status(False, f"Error: {e}"))

    results["complex_queries"] = "✅" if all(complex_checks) else "⚠️"

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════
    print_section("📊 AUDIT SUMMARY")

    for capability, status in results.items():
        print(f"  {status} {capability.replace('_', ' ').title()}")

    all_passing = all(s == "✅" for s in results.values())
    print(f"\n{'='*60}")
    if all_passing:
        print("✅ ALL SYSTEMS OPERATIONAL")
    else:
        print("⚠️  SOME SYSTEMS NEED ATTENTION")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
