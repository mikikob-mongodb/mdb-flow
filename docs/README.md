# Flow Companion Documentation

This directory contains all documentation for Flow Companion, organized into logical categories.

## Directory Structure

```
docs/
├── architecture/     System architecture and design
├── features/         Feature-specific documentation
├── testing/          Testing guides and procedures
└── archive/          Historical/superseded documentation
```

## Documentation Categories

### Architecture

System design, agent architecture, and optimization strategies.

- **[ARCHITECTURE.md](./architecture/ARCHITECTURE.md)** - Complete system architecture overview
  - 3-agent system design (Coordinator, Worklog, Retrieval)
  - Flow diagrams for common operations
  - 5-tier memory system architecture
  - Performance characteristics

- **[AGENT_ARCHITECTURE_AND_OPTIMIZATIONS.md](./architecture/AGENT_ARCHITECTURE_AND_OPTIMIZATIONS.md)** - Version 4.0
  - Detailed agent responsibilities and tool routing
  - Context engineering optimizations (Milestone 2)
  - 5-tier memory system (Milestone 4 & 5)
  - Performance metrics and latency breakdown
  - Future enhancements roadmap

### Features

Documentation for specific features and capabilities.

- **[MEMORY.md](./features/MEMORY.md)** - 5-Tier Memory System
  - Working Memory (2hr TTL)
  - Episodic Memory (action history with embeddings)
  - Semantic Memory (preferences with confidence scoring)
  - Procedural Memory (rules with usage tracking)
  - Shared Memory (agent handoffs)
  - Complete API reference and schemas
  - Testing methodology

- **[SLASH_COMMANDS.md](./features/SLASH_COMMANDS.md)** - Slash Command Reference
  - `/tasks` - Query tasks directly
  - `/projects` - Query projects directly
  - `/do` - Execute quick actions
  - `/search` - Semantic search
  - Performance comparisons vs LLM routing

### Testing

Testing guides, procedures, and demo scripts.

- **[README.md](./testing/README.md)** - Testing suite overview
- **[TESTING.md](./testing/TESTING.md)** - General testing guide
- **[FLOW_COMPANION_TESTING_GUIDE.md](./testing/FLOW_COMPANION_TESTING_GUIDE.md)** - Comprehensive testing guide
- **[demo_script.md](./testing/demo_script.md)** - Demo walkthrough

**Structured Test Scenarios** (00-09):
- 00-setup.md - Environment setup
- 01-slash-commands.md - Slash command tests
- 02-text-queries.md - Text query tests
- 03-text-actions.md - Text action tests
- 04-voice-input.md - Voice input tests
- 05-context-engineering.md - Optimization tests
- 06-memory-engineering.md - Memory system tests
- 07-multi-turn.md - Multi-turn conversation tests
- 08-error-handling.md - Error handling tests
- 09-demo-dry-run.md - Complete demo script

### Archive

Historical documentation and superseded content.

- Memory evaluation methodologies (superseded by MEMORY.md)
- Session summaries (moved to /session_summaries)
- Test results and analyses from early development
- Pull request descriptions

## Quick Links

### Getting Started
- [System Architecture](./architecture/ARCHITECTURE.md) - Start here for system overview
- [Testing Setup](./testing/00-setup.md) - Set up testing environment
- [Demo Script](./testing/09-demo-dry-run.md) - Run a complete demo

### Key Features
- [5-Tier Memory System](./features/MEMORY.md) - Comprehensive memory documentation
- [Slash Commands](./features/SLASH_COMMANDS.md) - Fast direct database queries

### Development
- [Agent Architecture](./architecture/AGENT_ARCHITECTURE_AND_OPTIMIZATIONS.md) - Deep dive into agent design
- [Testing Guide](./testing/FLOW_COMPANION_TESTING_GUIDE.md) - Complete testing methodology

## Version History

- **Version 4.0** (Current) - Milestone 5 Complete
  - 5-tier memory system fully implemented
  - Semantic memory (preferences with confidence scoring)
  - Procedural memory (rules with usage tracking)
  - 27 memory-specific tests
  - Memory UI integration

- **Version 3.1** - Milestone 3 Complete
  - Evals dashboard and comparison framework
  - UI improvements and metric toggles
  - Search mode variants (hybrid/vector/text)

- **Version 2.0** - Milestone 2 Complete
  - Context engineering optimizations
  - Tool result compression
  - Streamlined prompts
  - Prompt caching

- **Version 1.0** - Milestone 1 Complete
  - 3-agent system (Coordinator, Worklog, Retrieval)
  - MongoDB Atlas integration
  - Voice input support
  - Slash commands

## Contributing

When adding new documentation:

1. **Choose the right category**:
   - Architecture docs → `architecture/`
   - Feature-specific docs → `features/`
   - Testing docs → `testing/`
   - Superseded docs → `archive/`

2. **Follow naming conventions**:
   - Use UPPERCASE for major docs (e.g., MEMORY.md)
   - Use lowercase with dashes for test scenarios (e.g., 01-slash-commands.md)
   - Include version numbers where applicable

3. **Update this README**:
   - Add new docs to the relevant section
   - Update version history if applicable
   - Update quick links as needed

4. **Archive old docs**:
   - Move superseded docs to `archive/`
   - Reference the new location in the old doc
   - Keep archive/ organized by topic

## Maintenance

- Review and update architecture docs with each milestone
- Keep feature docs in sync with code changes
- Archive docs when superseded by newer versions
- Maintain clear cross-references between related docs
