# Flow Companion v2.0.0 - Milestone 2: Voice Input

🎤 Voice-powered task updates! Stream-of-consciousness voice input with intelligent parsing, fuzzy matching, and automatic task updates.

## Summary

This PR adds voice input capabilities to Flow Companion, enabling users to give rambling status updates via microphone and have them intelligently parsed into structured task/project updates.

## What's New in Milestone 2

### 🎤 Voice Input System
- ✅ **Native Audio Recording** - Streamlit's built-in `st.audio_input()` for recording
- ✅ **Speech-to-Text** - OpenAI Whisper API transcription with automatic error handling
- ✅ **Voice Message Display** - Chat history shows 🎤 icon for voice messages
- ✅ **Temporary File Management** - Automatic cleanup of audio files after transcription

### 🧠 Intelligent Voice Parsing
- ✅ **Stream-of-Consciousness Parser** - Claude parses rambling voice into structured updates
- ✅ **10 Extraction Categories**:
  - `task_references`: Informal mentions ("the auth thing", "login stuff")
  - `project_references`: Project mentions ("the mobile app", "client project")
  - `completions`: Tasks mentioned as done/finished
  - `progress_updates`: Work in progress with details
  - `deferrals`: Items pushed to later (with when/reason)
  - `new_items`: New tasks suggested (with source attribution)
  - `context_updates`: Context to add to tasks/projects
  - `notes_to_add`: Specific notes to capture
  - `decisions`: Decisions made (with reasoning)
  - `cleaned_summary`: 1-2 sentence clean summary

### 🔍 Fuzzy Matching Engine
- ✅ **Hybrid Matching** - Combines vector similarity (60%) + text similarity (40%)
- ✅ **Task Matching** - `fuzzy_match_task(reference, project_hint, threshold=0.7)`
- ✅ **Project Matching** - `fuzzy_match_project(reference, threshold=0.7)`
- ✅ **Confidence Scoring** - Returns match confidence and alternatives
- ✅ **Ambiguity Detection** - Identifies close alternatives for clarification
- ✅ **RapidFuzz Integration** - Fast string matching with Levenshtein distance

### 🤖 Voice-Aware Coordinator
- ✅ **Input Type Routing** - Detects `input_type="voice"` vs `"text"`
- ✅ **Special Voice Processing** - Different flow for voice vs text input
- ✅ **Automatic Fuzzy Matching** - Matches informal mentions to real tasks/projects
- ✅ **Clarification Requests** - Asks user to clarify ambiguous references
- ✅ **Confirmation Flow** - "Should I create this task?" for new items
- ✅ **Action Summary** - Structured response showing what was captured

### 📝 Voice-Enhanced Worklog Agent
- ✅ **Voice Update Method** - `apply_voice_update(task_id, project_id, updates, voice_log_entry)`
- ✅ **Batch Updates** - Apply status, notes, and context in one call
- ✅ **Voice Creation** - `create_task_from_voice(title, project_id, source, context, from_transcript)`
- ✅ **Source Attribution** - Tracks who mentioned the task ("mentioned by Sarah")
- ✅ **Transcript Storage** - Raw transcripts stored in activity_log

### 📊 Enhanced Activity Logging
- ✅ **Voice Log Entries** - New `action="voice_update"` type
- ✅ **Transcript Preservation** - `raw_transcript` field in activity logs
- ✅ **Parsed Structure** - `extracted` field stores structured parse results
- ✅ **Summary Field** - `summary` field for cleaned voice summaries
- ✅ **Full Traceability** - Complete audit trail of voice inputs

## How Voice Input Works

### User Flow
1. Click microphone button next to text input
2. Speak naturally - rambling updates, stream-of-consciousness
3. Transcription appears with 🎤 icon
4. System responds with actions taken, clarifications needed, and confirmations

### Example
**Voice Input:**
> "Hey, I finished the auth thing. The login bug is still in progress but I'm about halfway done. Oh and Sarah mentioned we should add password reset, maybe put that in the auth project. The mobile app deployment is pushed to next week because we're waiting on the staging environment."

**System Response:**
```
Voice Update Received: Completed auth, halfway through login bug, password reset suggested, mobile deployment deferred to next week.

Actions taken:
✓ Marked 'Implement authentication system' as done
📝 Added progress update to 'Fix login validation bug'
⏸️ Deferred 'Mobile App Deployment' to next week

New items mentioned:
Should I create a task: 'Add password reset flow' (from: mentioned by Sarah)?
```

## Technical Details

### New Files
- `utils/audio.py` - Whisper transcription utility (49 lines)

### Enhanced Files
- `agents/coordinator.py` - Voice parsing and processing (+170 lines)
- `agents/retrieval.py` - Fuzzy matching methods (+238 lines)
- `agents/worklog.py` - Voice-specific tools (+221 lines)
- `shared/models.py` - Voice activity log fields (+3 fields)
- `ui/streamlit_app.py` - Audio recorder integration (+74 lines)

### Code Statistics
- **Total New Code**: ~750 lines
- **Voice Processing Logic**: ~170 lines
- **Fuzzy Matching Engine**: ~238 lines
- **Voice Worklog Tools**: ~221 lines
- **Audio Utilities**: ~49 lines
- **UI Enhancements**: ~74 lines

### Tech Stack
- **UI**: Streamlit + streamlit-audio-recorder
- **AI**: Claude API (Sonnet 4.5)
- **Speech-to-Text**: OpenAI Whisper API (whisper-1 model)
- **Embeddings**: Voyage AI (voyage-3, 1024 dimensions)
- **Fuzzy Matching**: RapidFuzz (Levenshtein distance)
- **Database**: MongoDB Atlas (operational DB + vector store)

### New Dependencies
- `openai>=1.0.0` - Whisper API client
- `rapidfuzz>=3.0.0` - Fast fuzzy string matching

**Note**: Voice recording uses Streamlit's native `st.audio_input()` (available in Streamlit 1.28.0+), so no additional audio recording library is needed.

## Architecture Highlights

### Voice Processing Pipeline
```
Voice Input → Whisper API → Transcript → Claude Parser → Structured Data
                                                ↓
Fuzzy Matcher → Match Tasks/Projects → Apply Updates → Confirm with User
```

### Fuzzy Matching Algorithm
1. **Vector Search**: Get top 10 candidates using MongoDB Atlas vector search
2. **Text Similarity**: Calculate Levenshtein distance on titles/names
3. **Combined Score**: `0.6 * vector_score + 0.4 * text_score`
4. **Threshold Check**: Return match if score ≥ 0.7
5. **Alternatives**: Include close alternatives within 0.1 of best score

### Activity Log Enhancement
```python
ActivityLogEntry(
    action="voice_update",
    note="Cleaned summary of update",
    summary="1-2 sentence summary",
    raw_transcript="Original voice transcript...",
    extracted={
        "completions": [...],
        "progress_updates": [...],
        # ... full parsed structure
    }
)
```

## Setup Instructions

### Prerequisites
- Milestone 1 must be set up (MongoDB Atlas, vector search indexes)
- **New**: OpenAI API key for Whisper transcription

### Installation
1. Update dependencies:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Add OpenAI API key to `.env`:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Run the app:
   ```bash
   PYTHONPATH=$PWD streamlit run ui/streamlit_app.py
   ```

4. Test voice input:
   - Click microphone button (🎤)
   - Allow browser microphone permissions
   - Speak a status update
   - See transcription and parsed results

## Testing Voice Input

### Test Voice Commands

**Task Completion:**
> "I finished the authentication work and completed the login bug fix"

**Progress Update:**
> "The API integration is about halfway done. I've got the GET and POST endpoints working"

**Deferral:**
> "Moving deployment to next Tuesday, waiting for staging environment"

**New Task:**
> "Sarah mentioned we should add password reset to the auth project"

**Context Update:**
> "For the mobile app, we're using React Native and deploying to AWS"

**Combined Update:**
> "Finished auth. Login bug halfway done. Sarah wants password reset. Deploy pushed to next week."

### Expected Behavior
- ✅ Fuzzy matching matches informal mentions to real tasks
- ✅ Status updates applied automatically
- ✅ Raw transcripts stored in activity_log
- ✅ Clarification requested for ambiguous references
- ✅ Confirmation requested for new tasks
- ✅ Summary shows all actions taken

## Known Limitations
- Voice input requires OpenAI API key (Whisper API)
- Browser must support Web Audio API
- Fuzzy matching requires existing tasks with embeddings
- Ambiguous references need user clarification
- Session state is per-browser-tab
- Voice transcripts stored as raw text (not searchable)

## Future Enhancements (v3.0+)
- Multi-language voice support
- Custom wake words
- Voice commands ("Show tasks", "What's next?")
- Speaker identification for teams
- Voice-to-voice responses (TTS)
- Offline voice processing
- Voice shortcuts and macros

## Files Changed

### New
- `utils/audio.py`

### Modified
- `agents/coordinator.py`
- `agents/retrieval.py`
- `agents/worklog.py`
- `shared/models.py`
- `ui/streamlit_app.py`
- `requirements.txt`
- `.env.example`

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
