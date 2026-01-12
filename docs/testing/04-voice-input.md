# 04 - Voice Input

**Time:** 10 minutes  
**Priority:** P1 - Important for demo

---

## Overview

Voice input should produce identical results to text input. The flow is:
1. User speaks → Browser captures audio
2. Audio → Whisper/Deepgram → Text transcription
3. Text → Same LLM processing as text queries

**Key Point:** Same query spoken vs typed should produce same results.

---

## Prerequisites

```
□ Microphone access granted in browser
□ Stable internet connection
□ Quiet environment for testing
□ Chrome or Safari (Firefox may have issues)
```

---

## Test Cases

### 4.1 Voice Query Tests

| ID | Speak | Expected | Same as Text? | Pass |
|----|-------|----------|---------------|------|
| 4.1 | "What are my tasks?" | Task list | ✓ Match 2.1 | □ |
| 4.2 | "What's in progress?" | Filtered tasks | ✓ Match 2.2 | □ |
| 4.3 | "Show me the AgentOps project" | Project details | ✓ Match 2.5 | □ |
| 4.4 | "Find tasks about debugging" | Search results | ✓ Match 2.7 | □ |

### 4.2 Voice Action Tests

| ID | Speak | Expected | Same as Text? | Pass |
|----|-------|----------|---------------|------|
| 4.5 | "I finished the debugging doc" | Complete flow | ✓ Match 3.1 | □ |
| 4.6 | "Add a note to voice agent: testing complete" | Add note flow | ✓ Match 3.6 | □ |

### 4.3 Voice-Specific Tests

| ID | Test | Expected Behavior | Pass |
|----|------|-------------------|------|
| 4.7 | Speak with filler words: "Um, what are, uh, my tasks?" | Should still understand | □ |
| 4.8 | Speak quickly | Transcription accurate | □ |
| 4.9 | Speak with background noise | Reasonable transcription | □ |
| 4.10 | Long query (20+ words) | Full transcription | □ |

### 4.4 Transcription Quality

| ID | Speak | Check Transcription | Pass |
|----|-------|---------------------|------|
| 4.11 | "AgentOps" | Spelled correctly | □ |
| 4.12 | "checkpointer" | Technical term accurate | □ |
| 4.13 | "WebSocket" | Capitalization correct | □ |

---

## Test Procedure

```
1. □ Click microphone button (🎤)
2. □ Wait for "Listening..." indicator
3. □ Speak query clearly
4. □ Wait for transcription to appear
5. □ Verify transcription matches what you said
6. □ Verify response matches equivalent text query
7. □ Check debug panel shows same tools called
```

---

## Verification Checklist

```
□ Microphone button works
□ "Listening" indicator appears
□ Transcription appears in input field
□ Transcription is accurate
□ Response matches text equivalent
□ Same tools called (check debug panel)
□ Latency similar to text (+ transcription time)
```

---

## Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| No audio capture | Button clicks but nothing happens | Check browser permissions |
| Poor transcription | Words garbled | Speak more clearly, reduce noise |
| Timeout | Transcription cuts off | Keep queries under 30 seconds |
| Wrong language | Transcription in wrong language | Check browser language settings |

---

## Results Summary

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| Voice Queries | 4 | __ | __ |
| Voice Actions | 2 | __ | __ |
| Voice-Specific | 4 | __ | __ |
| Transcription Quality | 3 | __ | __ |
| **Total** | **13** | __ | __ |

---

## Appendix: Voice Test Scripts

For comprehensive voice testing, use these read-aloud test scripts. See full details in the sections below.

### Quick Test Scripts

**Simple completion:**
```
I just finished the debugging methodologies doc
```

**Status update:**
```
I'm starting work on the evaluation framework
```

**Query:**
```
What tasks do I have in progress right now?
```

For 25 additional test scripts covering complex scenarios, stream-of-consciousness updates, corrections, and edge cases, see the complete voice testing scripts below.

---

### Complete Voice Test Script Library

The following 25 test scripts cover all voice input scenarios. Click 🎤 and read these aloud to test transcription and parsing.

#### Simple Status Updates (Scripts 1-3)

**Script 1: Mark task done**
```
I finished the checkpointer documentation task
```
Expected: Completes "Write checkpointer documentation" in LangGraph Integration

**Script 2: Mark task in progress**
```
I'm starting work on the evaluation framework
```
Expected: Updates "Design evaluation framework" to in_progress

**Script 3: Add a note**
```
Just a quick note on the voice agent app - I got the interruption handling working
```
Expected: Adds note to "Build voice agent reference app" task

#### Stream-of-Consciousness Updates (Scripts 4-6)

**Script 4: Rambling progress update**
```
So I've been heads down on the LangGraph checkpointer thing, you know the MongoDB
integration. I got the basic serialization working but I'm still struggling with
the async stuff. Oh and I talked to the framework team, they said we need to add
more tests before they'll merge it.
```

**Script 5: Multiple updates at once**
```
Quick update on a few things. The NPC memory schema is done, that's finished.
I'm currently working on the conversation system for the NPCs. And the world
state management I'm pushing to next week because I need to figure out the
geospatial indexing first.
```

**Script 6: Work session summary**
```
Okay so today I worked on the re:Invent presentation slides, made good progress
there, probably about halfway done. I also did a quick pass on the live demo,
it's working but I need to test the offline mode still. Tomorrow I want to
focus on the practice run-through.
```

#### Context and Decisions (Scripts 7-9)

**Script 7: Adding context**
```
For the voice agent project, I decided we're going to use WebRTC for the audio
capture and Deepgram for transcription since it's faster than the alternatives
```

**Script 8: Manager feedback**
```
Just got out of my one-on-one. My manager suggested we should add more customer
examples to the re:Invent slides, and also maybe do a dry run with the PMM team
before the actual practice session.
```

**Script 9: Technical decision**
```
After some research on the adaptive tutoring demo, I think we should use
Bayesian Knowledge Tracing for the learner model. It's well-established in the
literature and should work well with MongoDB's aggregation framework.
```

#### Questions via Voice (Scripts 10-12)

**Script 10: Simple question**
```
What tasks do I have in progress right now?
```

**Script 11: Project status question**
```
How's the Gaming NPC Demo project going?
```

**Script 12: Semantic search**
```
What am I working on related to frameworks?
```

#### Creating New Tasks (Scripts 13-15)

**Script 13: Suggest new task**
```
Oh I just remembered, I need to add a task for writing unit tests for the
checkpointer. That should probably go in the LangGraph project.
```

**Script 14: New task with context**
```
I should create a task for updating the README with the new installation
instructions. It's blocking the PR so it's high priority.
```

**Script 15: Multiple new items**
```
I need to add a few things to my list. First, review the API documentation.
Second, set up the CI pipeline. And third, write the contribution guidelines.
These are all for the LangGraph Integration project.
```

#### Corrections and Clarifications (Scripts 16-18)

**Script 16: Correction**
```
Actually wait, I said I finished the debugging doc but I meant the AgentOps
article, that's the one that's done
```

**Script 17: Ambiguous reference**
```
I finished the documentation task
```
Expected: Agent should ask "Which documentation task?" if multiple matches

**Script 18: Wrong project assumption**
```
The memory schema task is done
```
Expected: Agent asks for clarification if ambiguous

#### Complex Scenarios (Scripts 19-21)

**Script 19: Full standup update**
```
Alright here's my standup update. Yesterday I finished the January webinar,
that went well, good attendance. Today I'm working on the February webinar
slides, the one about RAG evolution. I'm blocked on the AgentOps starter kit
because I'm waiting for the OpenTelemetry configs from the platform team.
And I need help reviewing the CrewAI memory backend design, if anyone has time.
```

**Script 20: End of day wrap-up**
```
Wrapping up for the day. Made good progress on the voice agent reference app,
got the WebSocket streaming working. Tomorrow I need to tackle the interruption
handling and then write up the blog post. Moving the multimodal demo to next
week since voice is taking longer than expected.
```

**Script 21: Meeting notes capture**
```
Just got out of the partner sync with the LangChain team. They're excited about
the checkpointer contribution. They asked us to make sure we support both sync
and async interfaces. They also mentioned they're working on a new persistence
API that we should align with. Let me capture this on the LangGraph project.
```

#### Edge Cases (Scripts 22-25)

**Script 22: Very short input**
```
Done with slides
```
Expected: Fuzzy matches to "Create presentation slides"

**Script 23: Filler words and pauses**
```
Um so like I was working on... you know... the uh... the checkpointer thing?
And um I think it's like almost done, maybe like 80 percent?
```
Expected: Agent parses through filler words

**Script 24: Project name variations**
```
Update on the gaming demo - the NPC thing - I finished the schema design
```
Expected: Matches variations to Gaming NPC Demo project

**Script 25: Partial task names**
```
The webinar landing page is done
```
Expected: Matches to "Create webinar landing page"

### Pro Tips for Voice Testing

1. **Be conversational** — You don't need to speak in commands
2. **Mention project names** — Helps with fuzzy matching
3. **Say "done" or "finished"** — Clear completion signals
4. **Say "tomorrow" or "next week"** — Clear deferral signals
5. **Pause between topics** — Helps parsing multiple updates
6. **Confirm at the end** — Agent should summarize; correct if wrong

---

*Voice Input Testing Guide v2.0*
*Includes 25 comprehensive test scripts for voice functionality*
