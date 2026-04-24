# Agentic Development Workflows

**Proven workflows for building software with AI coding agents effectively.**

---
name: Agentic Development Workflows
description: Apply proven workflows for coding with AI agents, managing context, and building production-quality software with minimal overhead
user-invocable: true
argument-hint: [development-task]
---

## Core Philosophy

You're working with a capable but overconfident programming assistant that never gets tired but makes subtle judgment errors. Your job is to provide clear constraints, verify mechanically, and manage the collaboration systematically.

**Key insight:** Code generation is almost zero cost, but delivering good software still requires discipline, verification, and systematic processes.

## The Eight Core Workflows

### 1. Hoard Technique Patterns
**Archive everything you've learned so AI can recombine it.**

- Maintain a personal knowledge base of patterns, solutions, and techniques
- Document not just code, but decision rationale and context
- Create reusable templates for common tasks
- Tag and organize for easy retrieval by AI agents

**Example:** Instead of recreating authentication from scratch each time, maintain templates for "JWT auth with refresh tokens," "OAuth 2.0 flow," "session management patterns."

### 2. Interactive Explanation Workflow  
**When text documentation isn't enough, generate visual aids.**

Process:
1. Encounter complex concept or algorithm
2. Ask agent to create interactive demonstrations
3. Generate code that visualizes the concept step-by-step
4. Use this to build understanding before implementing

**Example:** "I don't understand how this word cloud algorithm works from the docs. Create an animated demo showing how each word finds its position along the Archimedean spiral."

### 3. Linear Walkthrough Pattern
**Pay down cognitive debt systematically.**

When you have working code you don't understand:
1. Ask agent to create detailed walkthrough of each component
2. Generate explanations that connect high-level purpose to implementation details
3. Create architectural diagrams showing data flow and decision points
4. Document the mental model in your own words

### 4. High-Frequency Verification Loop
**Short cycles with immediate validation.**

Structure every task as:
1. **Small, testable chunk** (one clear objective)
2. **Immediate execution** (run the code, see results)  
3. **Quick verification** (does it work as expected?)
4. **Feedback integration** (adjust based on what you learned)

Avoid long periods without verification - verify every 10-15 minutes maximum.

### 5. Context Archaeology  
**Systematically manage information flow to prevent degradation.**

Context management rules:
- Document decisions as you make them, not after
- Commit frequently with detailed messages
- Use external tools (files, scripts) to store state
- Clear context and restart sessions when quality drops
- Never rely solely on conversation history for important information

### 6. Constraint Engineering
**Clear boundaries prevent overengineering.**

Before starting any task:
- Define exactly what success looks like
- Specify what you explicitly don't want built
- Set hard constraints on scope and complexity
- Identify the minimal viable implementation

**Example:** "Build user authentication. Success: users can register, login, logout. Constraints: no password recovery, no 2FA, no user profiles. Use simple JWT, nothing fancy."

### 7. Plan-First Development
**For complex tasks, iterate on the plan before implementing.**

Process:
1. Ask agent to draft detailed implementation plan
2. Review and refine the plan multiple times  
3. Only start coding when plan is solid
4. Refer back to plan frequently during implementation
5. Update plan as you discover new requirements

The plan becomes a contract between you and the agent.

### 8. Authoritarian vs Collaborative Modes
**Choose the right interaction style for the task.**

**Authoritarian mode** (for well-defined tasks):
- Give specific, detailed requirements
- Expect implementation without back-and-forth
- Suitable for: API integrations, known patterns, refactoring

**Collaborative mode** (for exploratory work):
- Ask agent to propose multiple approaches
- Iterate on requirements together  
- Let agent suggest better alternatives
- Suitable for: new features, architectural decisions, problem-solving

## Context Management Strategies

### Session Hygiene
- Start each session with clear context about current state
- Use external files to maintain state between sessions
- Commit work frequently to preserve progress
- Clear context and restart when output quality degrades

### Information Architecture
- Keep project docs in structured markdown files
- Use consistent file naming and organization
- Maintain a project README that agents can read for context
- Document patterns and decisions in easily scannable format

### Progressive Disclosure
- Start with simple implementations
- Add complexity only when needed
- Build incrementally with frequent verification points
- Resist the temptation to build flexible systems upfront

## Quality Gates

### Before Writing Code
- [ ] Requirements are specific and testable
- [ ] Success criteria are defined
- [ ] Scope is appropriately constrained  
- [ ] Approach has been validated

### During Development
- [ ] Each increment can be tested independently
- [ ] Progress is being committed regularly
- [ ] Current state is documented
- [ ] Agent understands the larger context

### Before Considering Complete  
- [ ] Code works as specified
- [ ] Tests confirm expected behavior
- [ ] Documentation reflects current state
- [ ] Technical debt is documented for future

## Common Failure Modes to Avoid

### The Tools Trap
**Symptom:** Focusing on frameworks, architectures, and tooling before understanding the problem.
**Solution:** Start with the simplest possible implementation. Add tools only when you hit their specific limitations.

### Context Pollution
**Symptom:** Agent responses become generic or off-target as conversation length increases.
**Solution:** Monitor session quality. Document key decisions externally. Restart sessions before quality degrades significantly.

### Overengineering Spiral  
**Symptom:** Agent builds elaborate, flexible systems for simple requirements.
**Solution:** Use constraint engineering. Be explicit about what you don't want. Ask "would a senior engineer call this overcomplicated?"

### Vibe Coding Drift
**Symptom:** Working without clear objectives, hoping things will emerge.
**Solution:** Define specific, measurable outcomes before starting any coding session.

## Advanced Patterns

### Multi-Session Workflows
For tasks spanning multiple sessions:
1. Create detailed handoff documents between sessions
2. Use git commits as checkpoint/restore points  
3. Maintain a running log of decisions and context
4. Start each new session by reviewing the previous session's summary

### Agent Specialization
Use different interaction patterns for different types of tasks:
- **Research tasks:** Collaborative, exploratory approach
- **Implementation tasks:** Authoritarian, specification-driven approach  
- **Debugging tasks:** Systematic, hypothesis-driven approach
- **Refactoring tasks:** Conservative, test-driven approach

### Knowledge Capture
Transform successful workflows into reusable patterns:
1. Document what worked and why
2. Create templates for similar future tasks
3. Build personal libraries of proven approaches
4. Share successful patterns with team/community

## Success Metrics

You're applying this skill effectively when:
- Sessions stay productive for longer periods
- Less time spent on rewrites and scope creep
- More predictable delivery timeframes  
- Accumulated knowledge compounds over time
- Quality of AI assistance improves as you work together more

The goal is sustainable productivity: doing more, higher-quality work without burning out on context management or fighting with AI quirks.
