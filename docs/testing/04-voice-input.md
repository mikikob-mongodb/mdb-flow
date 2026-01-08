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

*Voice Input Testing Guide v2.0*
