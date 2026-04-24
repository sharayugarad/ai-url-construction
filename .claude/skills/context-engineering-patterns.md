# Context Engineering Patterns

**Systematic approaches to managing LLM context windows for maximum effectiveness.**

---
name: Context Engineering Patterns
description: Apply proven patterns for curating, compressing, and managing context to maximize AI effectiveness within attention and token constraints
user-invocable: true
argument-hint: [context-management-task]
---

## Core Philosophy

Context engineering is the discipline of managing what information enters the model's limited attention budget. Unlike prompt engineering, which focuses on crafting instructions, context engineering addresses the holistic curation of all information: system prompts, tool definitions, retrieved documents, message history, and outputs.

**Key insight:** Context windows are constrained not by raw token capacity but by attention mechanisms. Quality degrades predictably as context length increases, regardless of technical limits.

## Fundamental Context Constraints

### Attention Degradation Patterns
**Understanding how model performance changes with context length.**

**The U-Shaped Attention Curve:**
- Information at the **beginning** (primacy) gets strong attention
- Information at the **end** (recency) gets strong attention  
- Information in the **middle** gets significantly less attention ("lost-in-the-middle" effect)

**Practical Implications:**
- Place most important information at start and end of context
- Avoid burying critical details in long middle sections
- Structure documents with key information at boundaries

**Quality Degradation Thresholds:**
- **20-40% of window:** Performance starts degrading subtly
- **60% of window:** Noticeable quality reduction in outputs
- **80%+ of window:** Significant degradation, unreliable responses

### Context Budget Management
**Treating context as a scarce resource requiring strategic allocation.**

**Token Budget Allocation:**
- **System prompt:** 10-20% (essential instructions and constraints)
- **Tool definitions:** 20-30% (functionality descriptions and schemas)
- **Retrieved content:** 30-40% (external knowledge and documents)
- **Conversation history:** 20-30% (relevant prior exchanges)
- **Current query:** 5-10% (immediate user request)

**Budget Monitoring:**
- Track token usage per context component
- Set alerts at 60% capacity
- Implement automatic compaction before quality degrades
- Monitor output quality metrics as context fills

## Core Context Engineering Patterns

### 1. Strategic Information Placement
**Position information based on attention patterns.**

**Front-Loading Pattern:**
```
Context Structure:
1. Most critical constraints and requirements (beginning)
2. Supporting context and background information (middle)  
3. Specific current task and recent relevant info (end)
```

**Implementation:**
- Place unbreakable rules and constraints at the very beginning
- Position task-specific requirements at the end
- Use middle sections for supporting context that's helpful but not critical

### 2. Hierarchical Context Compression
**Compress information at different granularities based on relevance.**

**Compression Levels:**
- **Full retention:** Current task, recent conversation, critical constraints
- **Summary compression:** Older conversation turns, background context
- **Keyword extraction:** Very old context, tangentially relevant information
- **Omission:** Information that adds no value to current task

**Implementation Strategy:**
```
Recent (last 3 turns): Full message content
Medium (4-10 turns): Summarized key points and decisions  
Older (10+ turns): Keywords and critical decisions only
Ancient: Omitted unless specifically relevant
```

### 3. Contextual Relevance Filtering
**Include only information that directly impacts current task quality.**

**Relevance Assessment Criteria:**
- **Direct impact:** Information needed to complete current task
- **Constraint relevance:** Rules that govern current task execution
- **Background context:** Information that significantly improves output quality
- **Historical context:** Previous decisions that affect current approach

**Filtering Process:**
1. Identify current task requirements
2. Score each context item for relevance (0-10)
3. Include items above threshold (typically 7+)
4. Compress items in middle range (4-6)
5. Omit items below threshold (0-3)

### 4. Progressive Context Disclosure
**Reveal information incrementally as task complexity increases.**

**Disclosure Levels:**
- **Level 1:** Basic task requirements and constraints
- **Level 2:** Additional context for edge cases and nuances
- **Level 3:** Full background knowledge and historical context
- **Level 4:** Meta-information about the task and process

**Triggering Conditions:**
- Move to next level when current level proves insufficient
- User explicitly requests more detail or context
- Task complexity increases beyond current context level
- Error patterns suggest missing information

### 5. Context Sectioning and Tagging
**Organize context into clearly labeled, purposeful sections.**

**Standard Section Template:**
```
## CORE CONSTRAINTS
[Unbreakable rules and requirements]

## CURRENT TASK
[Specific immediate objective]

## RELEVANT BACKGROUND
[Supporting context that impacts quality]

## RECENT CONVERSATION
[Last few exchanges for continuity]

## TOOLS AND CAPABILITIES  
[Available functions and their purposes]
```

**Tagging System:**
- Use consistent headers for easy parsing
- Tag information by type (requirement, constraint, context, history)
- Mark information by importance level (critical, important, helpful)
- Include relevance scope (current task, general project, background)

## Advanced Context Patterns

### 6. Dynamic Context Routing
**Route different types of information through different context channels.**

**Multi-Channel Architecture:**
- **System channel:** Static constraints and capabilities
- **Task channel:** Current objective and requirements
- **Memory channel:** Relevant historical information
- **Knowledge channel:** External information and documents

**Benefits:**
- Prevents channel interference and confusion
- Allows independent optimization of each information type
- Enables specialized compression strategies per channel
- Simplifies context debugging and management

### 7. Context State Machines
**Model context as evolving states with transitions.**

**Context States:**
- **Planning state:** Focus on requirements gathering and approach design
- **Execution state:** Emphasize current task details and constraints
- **Review state:** Highlight evaluation criteria and quality checks
- **Debugging state:** Surface error information and diagnostic context

**State Transitions:**
- Explicit user commands ("let's start implementing")
- Automatic based on task progression 
- Error conditions that require different information priorities
- Natural conversation flow cues

### 8. Attention-Aware Document Processing
**Structure documents to work with LLM attention patterns.**

**Document Restructuring:**
- **Executive summary at top:** Key points and conclusions
- **Core content in middle:** Detailed information and analysis
- **Action items at bottom:** Specific next steps and requirements

**Multi-Document Strategies:**
- Place most relevant documents at context boundaries (start/end)
- Use document summaries instead of full text for less critical sources
- Implement document relevance ranking and selection
- Create synthetic documents that combine key points from multiple sources

## Context Management Implementation

### Automated Context Curation
**Systematic approaches to context selection and compression.**

**Content Scoring System:**
```
Relevance Score = 
  (Direct Task Relevance × 0.4) +
  (Recency Weight × 0.3) + 
  (Information Density × 0.2) +
  (User Priority × 0.1)
```

**Compression Algorithms:**
- Extract key facts and decisions from longer content
- Maintain entity relationships and important context
- Preserve causal chains and logical dependencies
- Include enough detail for continuity and understanding

### Context Quality Monitoring
**Track context effectiveness and adjust strategies.**

**Quality Metrics:**
- Output relevance to context information provided
- Consistency of responses with context constraints
- User satisfaction with contextually-informed responses
- Frequency of context-related errors or misunderstandings

**Monitoring Implementation:**
- Log context composition for each interaction
- Track correlation between context patterns and output quality
- Monitor user corrections that suggest context issues
- A/B test different context curation strategies

### Context Handoff Patterns
**Maintain context continuity across sessions and systems.**

**Session Handoff:**
```
Session Summary:
- Key decisions made: [list]
- Current state: [description]
- Next steps: [priorities]
- Important context: [critical information to retain]
- Open questions: [unresolved issues]
```

**System Integration:**
- Standardized context export/import formats
- Context versioning for reproducibility
- Shared context stores for multi-agent systems
- Context validation and integrity checks

## Domain-Specific Applications

### Long-Form Content Creation
**Managing context for extended writing projects.**

**Patterns:**
- Maintain character sheets and plot outlines in persistent context
- Use chapter/section summaries to preserve narrative continuity
- Include style guides and tone requirements in system context
- Rotate detailed scene information while keeping story arc visible

### Code Development
**Context management for programming tasks.**

**Patterns:**
- Keep current file content and immediate dependencies in full context
- Use code summaries and interfaces for broader codebase context
- Include relevant documentation and examples, not entire manuals
- Maintain consistent variable naming and architectural patterns

### Research and Analysis
**Context curation for complex analytical tasks.**

**Patterns:**
- Curate relevant sources based on specific research questions
- Use citation networks to identify most important references
- Include methodology descriptions and evaluation criteria
- Maintain research question focus throughout analysis

### Customer Support
**Context management for service interactions.**

**Patterns:**
- Include customer history relevant to current issue
- Provide product documentation specific to customer's situation
- Include escalation procedures and common resolution patterns
- Maintain issue tracking and resolution context

## Troubleshooting Context Issues

### Common Context Problems

**Information Overload:**
- Symptoms: Generic responses, loss of specificity, ignoring constraints
- Solutions: Aggressive filtering, hierarchical compression, sectioned organization

**Context Pollution:**  
- Symptoms: Responses influenced by irrelevant information, confusion between contexts
- Solutions: Relevance filtering, clear sectioning, context cleaning

**Attention Scattering:**
- Symptoms: Missing critical requirements, inconsistent application of constraints
- Solutions: Strategic placement, constraint emphasis, attention-aware structuring

**Context Staleness:**
- Symptoms: Responses based on outdated information, ignoring recent updates
- Solutions: Recency weighting, context refresh patterns, staleness detection

### Diagnostic Techniques

**Context Auditing:**
- Review context composition for completed tasks
- Identify which context elements were actually used in responses
- Find correlation between context patterns and response quality
- Test context variations to find optimal composition

**A/B Context Testing:**
- Compare different context curation strategies
- Measure output quality with different information prioritization
- Test various compression levels and techniques
- Evaluate user satisfaction with different context approaches

## Success Metrics

You're applying context engineering effectively when:
- AI responses consistently reflect the most important information
- Output quality remains high even in long conversations
- Context constraints are reliably followed throughout interactions
- Information handoffs between sessions maintain continuity
- Users rarely need to repeat critical information

The goal is creating AI interactions that feel like working with someone who has perfect memory management and always focuses on what matters most.
