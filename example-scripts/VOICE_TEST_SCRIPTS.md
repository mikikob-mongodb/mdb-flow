# Flow Companion — Voice Input Test Scripts

Test scripts for Milestone 2 voice input functionality. Read these aloud to test transcription and parsing.

---

## Quick Test

Click 🎤 and say:

```
I just finished the debugging methodologies doc
```

**Expected:**
- Transcription appears in chat with 🎤 icon
- Agent fuzzy-matches to "Create debugging methodologies doc" task
- Agent marks it as complete
- Agent confirms: "Completed 'Create debugging methodologies doc' in AgentOps Framework"

---

## Test Scripts by Category

### Simple Status Updates

**Script 1: Mark task done**
```
I finished the checkpointer documentation task
```

Expected: Completes "Write checkpointer documentation" in LangGraph Integration

---

**Script 2: Mark task in progress**
```
I'm starting work on the evaluation framework
```

Expected: Updates "Design evaluation framework" to in_progress

---

**Script 3: Add a note**
```
Just a quick note on the voice agent app - I got the interruption handling working
```

Expected: Adds note to "Build voice agent reference app" task

---

### Stream-of-Consciousness Updates

**Script 4: Rambling progress update**
```
So I've been heads down on the LangGraph checkpointer thing, you know the MongoDB 
integration. I got the basic serialization working but I'm still struggling with 
the async stuff. Oh and I talked to the framework team, they said we need to add 
more tests before they'll merge it.
```

Expected parsing:
- Task: "Implement MongoDB checkpointer for LangGraph"
- Progress: Basic serialization working
- Blocker: Async implementation
- Note: Framework team requires more tests before merge
- Agent confirms what was captured

---

**Script 5: Multiple updates at once**
```
Quick update on a few things. The NPC memory schema is done, that's finished. 
I'm currently working on the conversation system for the NPCs. And the world 
state management I'm pushing to next week because I need to figure out the 
geospatial indexing first.
```

Expected parsing:
- Completion: "Design NPC memory schema" → done
- Progress: "Build NPC conversation system" → in_progress
- Deferral: "Implement world-state management" → next week, reason: geospatial indexing
- Agent confirms all three updates

---

**Script 6: Work session summary**
```
Okay so today I worked on the re:Invent presentation slides, made good progress 
there, probably about halfway done. I also did a quick pass on the live demo, 
it's working but I need to test the offline mode still. Tomorrow I want to 
focus on the practice run-through.
```

Expected parsing:
- Progress: "Create presentation slides" - halfway done
- Progress: "Build live demo" - working, needs offline testing
- Tomorrow: "Practice run-through"
- Agent summarizes the session

---

### Context and Decisions

**Script 7: Adding context**
```
For the voice agent project, I decided we're going to use WebRTC for the audio 
capture and Deepgram for transcription since it's faster than the alternatives
```

Expected:
- Updates Voice Agent Architecture project
- Adds decision: "Using WebRTC for audio capture"
- Adds decision: "Using Deepgram for transcription - faster than alternatives"

---

**Script 8: Manager feedback**
```
Just got out of my one-on-one. My manager suggested we should add more customer 
examples to the re:Invent slides, and also maybe do a dry run with the PMM team 
before the actual practice session.
```

Expected:
- Adds note to "Create presentation slides": Manager suggested more customer examples
- Adds note to "Practice run-through": Do dry run with PMM team first

---

**Script 9: Technical decision**
```
After some research on the adaptive tutoring demo, I think we should use 
Bayesian Knowledge Tracing for the learner model. It's well-established in the 
literature and should work well with MongoDB's aggregation framework.
```

Expected:
- Adds method to Education Adaptive Tutoring Demo: "Bayesian Knowledge Tracing"
- Adds note about MongoDB aggregation compatibility

---

### Questions via Voice

**Script 10: Simple question**
```
What tasks do I have in progress right now?
```

Expected: Returns list of in_progress tasks (not a voice update, just a query)

---

**Script 11: Project status question**
```
How's the Gaming NPC Demo project going?
```

Expected: Returns progress summary for Gaming NPC Demo

---

**Script 12: Semantic search**
```
What am I working on related to frameworks?
```

Expected: Returns tasks related to LangGraph, CrewAI, etc.

---

### Creating New Tasks via Voice

**Script 13: Suggest new task**
```
Oh I just remembered, I need to add a task for writing unit tests for the 
checkpointer. That should probably go in the LangGraph project.
```

Expected:
- Agent asks: "Should I create a task 'Write unit tests for checkpointer' in LangGraph Integration?"
- User confirms
- Task created

---

**Script 14: New task with context**
```
I should create a task for updating the README with the new installation 
instructions. It's blocking the PR so it's high priority.
```

Expected:
- Agent asks which project
- Creates task with context: "Blocking the PR"
- Sets priority: high

---

**Script 15: Multiple new items**
```
I need to add a few things to my list. First, review the API documentation. 
Second, set up the CI pipeline. And third, write the contribution guidelines. 
These are all for the LangGraph Integration project.
```

Expected:
- Agent offers to create 3 tasks
- All assigned to LangGraph Integration
- Confirms each one

---

### Corrections and Clarifications

**Script 16: Correction**
```
Actually wait, I said I finished the debugging doc but I meant the AgentOps 
article, that's the one that's done
```

Expected:
- Agent understands correction
- Updates "Write 'What Is AgentOps?' article" instead
- Reverts any previous change if made

---

**Script 17: Ambiguous reference**
```
I finished the documentation task
```

Expected (multiple matches):
- Agent asks: "Which documentation task do you mean?"
  1. Write checkpointer documentation (LangGraph)
  2. Create debugging methodologies doc (AgentOps)
  3. Document WebSocket streaming patterns (Voice Agent)
- User clarifies
- Agent completes correct task

---

**Script 18: Wrong project assumption**
```
The memory schema task is done
```

Expected:
- Agent fuzzy matches to "Design NPC memory schema" OR "Design learner model schema"
- If ambiguous, asks for clarification
- Completes correct one based on user response

---

### Complex Scenarios

**Script 19: Full standup update**
```
Alright here's my standup update. Yesterday I finished the January webinar, 
that went well, good attendance. Today I'm working on the February webinar 
slides, the one about RAG evolution. I'm blocked on the AgentOps starter kit 
because I'm waiting for the OpenTelemetry configs from the platform team. 
And I need help reviewing the CrewAI memory backend design, if anyone has time.
```

Expected parsing:
- Completion: "January webinar: Agent Memory Basics" → done
- Note: Good attendance
- Current: "February webinar: RAG Evolution" → in_progress
- Blocked: "Build AgentOps Starter Kit" - waiting for OpenTelemetry configs
- Help needed: "Design MongoDB memory backend" - needs review
- Agent summarizes all updates

---

**Script 20: End of day wrap-up**
```
Wrapping up for the day. Made good progress on the voice agent reference app, 
got the WebSocket streaming working. Tomorrow I need to tackle the interruption 
handling and then write up the blog post. Moving the multimodal demo to next 
week since voice is taking longer than expected.
```

Expected parsing:
- Progress: "Build voice agent reference app" - WebSocket streaming working
- Tomorrow: Interruption handling, then blog post
- Deferral: "Create multimodal demo" → next week, reason: voice taking longer
- Agent creates end-of-day summary

---

**Script 21: Meeting notes capture**
```
Just got out of the partner sync with the LangChain team. They're excited about 
the checkpointer contribution. They asked us to make sure we support both sync 
and async interfaces. They also mentioned they're working on a new persistence 
API that we should align with. Let me capture this on the LangGraph project.
```

Expected:
- Updates LangGraph Integration project
- Adds notes: Partner sync feedback, sync/async requirement, new persistence API
- Possibly creates follow-up task for API alignment

---

### Edge Cases

**Script 22: Very short input**
```
Done with slides
```

Expected:
- Fuzzy matches to "Create presentation slides"
- Marks as complete
- Confirms

---

**Script 23: Filler words and pauses**
```
Um so like I was working on... you know... the uh... the checkpointer thing? 
And um I think it's like almost done, maybe like 80 percent?
```

Expected:
- Agent parses through filler words
- Matches to "Implement MongoDB checkpointer for LangGraph"
- Adds note: ~80% complete
- Confirms understanding

---

**Script 24: Project name variations**
```
Update on the gaming demo - the NPC thing - I finished the schema design
```

Expected:
- Matches "gaming demo" and "NPC thing" to Gaming NPC Demo project
- Completes "Design NPC memory schema"

---

**Script 25: Partial task names**
```
The webinar landing page is done
```

Expected:
- Matches to "Create webinar landing page"
- Marks as complete (or notes it's already done)

---

## Expected Voice Update Activity Log

After a voice update, the task's activity_log should contain:

```json
{
  "timestamp": "2026-01-03T10:30:00Z",
  "action": "voice_update",
  "summary": "WebSocket streaming working. Interruption handling tomorrow.",
  "raw_transcript": "Made good progress on the voice agent reference app, got the WebSocket streaming working. Tomorrow I need to tackle the interruption handling.",
  "extracted": {
    "completions": [],
    "progress": ["WebSocket streaming working"],
    "deferrals": [],
    "new_items": [],
    "notes_added": ["WebSocket streaming implemented"],
    "tomorrow": ["Interruption handling"]
  }
}
```

---

## Troubleshooting

### Transcription not working
- Check OPENAI_API_KEY is set in .env
- Verify microphone permissions in browser
- Check browser console for errors

### Wrong task matched
- Be more specific: "the checkpointer task in LangGraph" vs "the checkpointer"
- If ambiguous, agent should ask for clarification

### Updates not saving
- Check MongoDB connection
- Verify task exists in database
- Check activity_log in MongoDB Compass

### Filler words confusing parser
- The parser should handle "um", "uh", "like", "you know"
- If issues persist, speak more deliberately

---

## Pro Tips

1. **Be conversational** — You don't need to speak in commands
2. **Mention project names** — Helps with fuzzy matching
3. **Say "done" or "finished"** — Clear completion signals
4. **Say "tomorrow" or "next week"** — Clear deferral signals
5. **Pause between topics** — Helps parsing multiple updates
6. **Confirm at the end** — Agent should summarize; correct if wrong

---

## Quick Verification Checklist

| # | Test | What to Say |
|---|------|-------------|
| 1 | Simple completion | "I finished the debugging methodologies doc" |
| 2 | Status update | "I'm working on the February webinar slides" |
| 3 | Add note | "Note for the checkpointer: need to handle serialization edge cases" |
| 4 | Deferral | "Moving the multimodal demo to next week" |
| 5 | Question | "What's the progress on AgentOps Framework?" |
| 6 | Multiple updates | Script 5 above |
| 7 | New task | "I need to add a task for writing tests" |
| 8 | Ambiguous | "I finished the documentation" (should ask which one) |
| 9 | Rambling | Script 4 above |
| 10 | Correction | "Wait, I meant the article, not the doc" |