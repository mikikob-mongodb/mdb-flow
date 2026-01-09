# Flow Companion - Demo Day Checklist

**Demo Date:** January 15, 2026
**Demo Length:** 25 minutes
**Version:** 3.0 (Milestone 6)

---

## Night Before Demo (January 14, 2026)

### Environment Setup

```
□ Clone/pull latest code from main branch
□ Install all dependencies: pip install -r requirements.txt
□ Verify .env file has all required keys:
  □ ANTHROPIC_API_KEY
  □ VOYAGE_API_KEY
  □ OPENAI_API_KEY
  □ MONGODB_URI
  □ MONGODB_DATABASE
  □ TAVILY_API_KEY (for MCP demos)
□ Test MongoDB connection
□ Test Tavily MCP connection (toggle MCP Mode ON)
```

### Database Seeding

```
□ Run: python scripts/seed_demo_data.py
□ Verify data created:
  □ 3 projects (Project Alpha, Beta, Marketing Website)
  □ 15 tasks with various statuses
  □ User preferences (working_hours, focus_mode)
  □ Procedural rules ("done" → complete task)
  □ GTM Roadmap Template
□ Check Memory Stats shows procedural memory entries
```

### Demo Practice

```
□ Run through full demo 3 times (see 09-demo-dry-run.md)
□ Verify all 7 commands work consistently:
  1. /tasks
  2. "What was completed on Project Alpha?"
  3. "I'm focusing on Project Alpha"
  4. "What should I work on next?"
  5. [Toggle Working Memory OFF] → "What should I work on next?"
  6. [Toggle MCP Mode ON] → "Research gaming market and create GTM project with tasks"
  7. "What do you know about gaming?"
□ Time the demo: should complete in 20-25 minutes
□ Record backup video (in case of live issues)
```

### Backup Plan

```
□ Take screenshots of successful demo runs
□ Record full demo walkthrough video
□ Export demo slides to PDF (offline access)
□ Have demo script printed (docs/testing/09-demo-dry-run.md)
□ Test WiFi connection at demo venue (if applicable)
```

### Equipment

```
□ Laptop fully charged
□ Backup power cable
□ WiFi credentials tested
□ Presentation remote (if using)
□ HDMI/adapter for projector
□ Mouse (optional, for easier navigation)
```

---

## Morning of Demo (January 15, 2026)

### 2 Hours Before

```
□ Laptop charged to 100%
□ Close all unnecessary applications
□ Disable notifications (Do Not Disturb mode)
□ Clear browser cache
□ Test WiFi connection
```

### 30 Minutes Before

```
□ Start MongoDB Atlas (verify connection)
□ Start app: streamlit run streamlit_app.py --server.port 8501
□ Verify app loads without errors
□ Browser in presentation mode:
  □ Hide bookmarks bar
  □ Close developer tools
  □ Full screen (F11 or Cmd+Ctrl+F)
  □ Zoom to comfortable reading size
```

### 15 Minutes Before

```
□ Clear session memory: Click "🗑️ Clear Session Memory"
□ Verify all toggles:
  ☑ Compress Results: ON
  ☑ Streamlined Prompt: ON
  ☑ Prompt Caching: ON
  ☑ Enable Memory: ON
  ☑ Working Memory: ON
  ☑ Episodic Memory: ON
  ☑ Semantic Memory: ON
  ☑ Procedural Memory: ON
  ☑ Shared Memory: ON
  ☑ Context Injection: ON
  ☐ MCP Mode: OFF (will toggle during demo)
□ Verify Memory Stats shows:
  - Working Memory: 0 entries
  - Episodic Memory: X entries (from seed data - OK)
  - Semantic Memory: 0 entries
  - Procedural Memory: X entries (rules + template - OK)
  - Shared Memory: 0 entries
□ Debug panel visible at bottom
□ Have demo script open in another tab/window
```

### 5 Minutes Before

```
□ Take deep breath 😊
□ Test first command: /tasks (verify it works)
□ Close test response, ready for live demo
□ Slides open and ready (if separate presentation)
□ Water nearby
□ Phone on silent
```

---

## During Demo - Command Sequence

### Part 1: Baseline (2 min)

| # | Command | Expected Result | Duration |
|---|---------|----------------|----------|
| 1 | `/tasks` | Shows all 15 tasks | <200ms |

**Talking Point:** "Direct MongoDB query - our baseline speed"

### Part 2: Memory Engineering (10 min)

| # | Command | Memory Type | Expected |
|---|---------|-------------|----------|
| 2 | "What was completed on Project Alpha?" | Episodic | Shows completed tasks from action history |
| 3 | "I'm focusing on Project Alpha" | Semantic | Stores preference, Memory Stats +1 |
| 4 | "What should I work on next?" | Working | Suggests Project Alpha tasks (uses context) |
| 5a | [Toggle Working Memory OFF] | - | Toggle shows unchecked |
| 5b | "What should I work on next?" | - | Context lost - shows ALL tasks or asks "which project?" |
| 5c | [Toggle Working Memory ON] | - | Toggle shows checked |

**Talking Points:**
- Episodic: Persistent action history
- Semantic: Learned preferences
- Working: Session context
- Toggle contrast: Clear before/after value demonstration

### Part 3: MCP Agent & Multi-Step (10 min) ⭐ NEW

| # | Command | Feature | Expected |
|---|---------|---------|----------|
| 6a | [Toggle MCP Mode ON] | MCP Agent | "MCP Servers: 1 connected (Tavily)" |
| 6b | "Research gaming market and create GTM project with tasks" | Multi-step workflow | 3-step execution (~10s) |
| 7 | "What do you know about gaming?" | Knowledge Cache | Cache hit (~0.5s), "📚 Source: Knowledge Cache" |

**Expected 6b Output:**
```
Step 1/3: Research gaming market trends
  → Routing to MCP Agent (Tavily)...
  → ✓ Research completed

Step 2/3: Create GTM project for gaming
  → Detected GTM project
  → Loading template: GTM Roadmap Template
  → ✓ Project created: Gaming Market

Step 3/3: Generate tasks from template
  → Phase: Research (4 tasks)
  → Phase: Strategy (4 tasks)
  → Phase: Execution (4 tasks)
  → ✓ Generated 12 tasks across 3 phases
```

**Talking Points:**
- Procedural Memory: GTM template auto-loaded
- MCP Agent: Dynamic Tavily integration
- Multi-step: Automatic orchestration
- Knowledge Cache: 7-day TTL, 90% faster on reuse

### Part 4: Wrap-up (3 min)

**Key Takeaways:**
1. 5-tier memory architecture (Working, Episodic, Semantic, Procedural, Shared)
2. Context engineering: 40-60% latency reduction
3. MCP Agent: Dynamic tool discovery (Milestone 6)
4. Multi-step workflows: Automatic orchestration
5. MongoDB Atlas: Unified memory layer with vector search
6. Production-ready: 47 tests, 90% coverage

**Q&A Ready**

---

## Troubleshooting During Demo

| Issue | Quick Fix | Fallback |
|-------|-----------|----------|
| Query stuck/slow | "First query warming up" - wait | Refresh page, retry |
| Memory not updating | Check toggle is ON | Show backup screenshots |
| MCP Mode fails | Check Tavily API key | Skip to next section |
| Voice not working | "Voice works similarly to text" | Use text queries instead |
| Tool error | "Let me try that differently" | Use slash command alternative |
| Complete failure | Apologize, switch to backup video | Have video ready |

---

## Post-Demo

```
□ Thank audience
□ Share slides/resources
□ Note any issues encountered
□ Update documentation based on learnings
□ Celebrate! 🎉
```

---

## Emergency Contacts

```
Backup Support: [Name/Email]
MongoDB Contact: [Name/Email]
Venue Tech Support: [Phone]
```

---

*Demo Checklist v3.0*
*MongoDB Developer Day - January 15, 2026*
*Good luck! You've got this! 💪*
