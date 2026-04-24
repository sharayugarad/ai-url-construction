# LLM System Design Patterns

**Architectural patterns and design principles for building reliable LLM-powered systems.**

---
name: LLM System Design Patterns
description: Apply proven architectural patterns for building LLM systems including RAG, caching, guardrails, and defensive UX design
user-invocable: true
argument-hint: [system-design-task]
---

## Core Philosophy

Demos are easy, but production systems are hard. LLMs introduce unique challenges: they're non-deterministic, can hallucinate, fail in subtle ways, and violate traditional software consistency principles.

**Key insight:** Success requires architectural patterns that embrace LLM characteristics rather than fighting them.

## Essential System Patterns

### 1. Evaluation-First Architecture
**Build measurement into the system from day one.**

**Pattern:** Start every LLM system with task-specific evaluations, not generic benchmarks.

**Implementation:**
- Define success criteria before building features
- Create evaluation datasets that reflect real user tasks
- Use evaluations to guide prompt engineering, model selection, and fine-tuning
- Run evaluations continuously as system evolves

**Example:** Instead of measuring "helpfulness," create evals for "correctly schedules meeting within business hours" or "extracts all required fields from invoice."

### 2. Retrieval-Augmented Generation (RAG)
**Add external knowledge to overcome training data limitations.**

**When to Use:**
- System needs recent information beyond training cutoff
- Domain-specific knowledge not well-represented in training data
- Need to ground responses in authoritative sources
- Want to update knowledge without retraining models

**Architecture Components:**
- **Document indexing:** Chunk documents, generate embeddings, store in vector database
- **Retrieval system:** Query embedding, similarity search, relevance ranking
- **Context integration:** Merge retrieved docs with user query
- **Generation:** LLM generates response using both query and retrieved context

**Key Challenges:**
- **Lost-in-the-middle:** LLMs can't effectively use documents in middle of long contexts
- **Retrieval quality:** Semantic search may miss relevant documents
- **Context limits:** Too many documents exceed context window
- **Hallucination:** LLM may ignore retrieved docs and generate false information

**Best Practices:**
- Place most relevant documents at beginning and end of context
- Use hybrid search combining semantic and keyword matching
- Implement re-ranking to improve document ordering
- Add attribution to trace responses back to source documents

### 3. Caching and Optimization
**Reduce latency and costs for repeated queries.**

**Caching Strategies:**
- **Exact match caching:** Store responses for identical prompts
- **Semantic caching:** Cache responses for semantically similar queries
- **Prefix caching:** Cache common prompt prefixes to reduce processing
- **Embedding caching:** Store embeddings for frequently accessed documents

**Implementation Considerations:**
- Cache invalidation for updated information
- Privacy concerns with caching user data
- Storage costs vs compute cost tradeoffs
- Cache hit rate optimization

### 4. Guardrails and Safety
**Prevent harmful or inappropriate outputs.**

**Input Guardrails:**
- Content filtering for inappropriate queries
- Prompt injection detection and mitigation
- Rate limiting and abuse prevention
- Input validation and sanitization

**Output Guardrails:**
- Content moderation for generated responses
- Factual accuracy checks against known databases
- Bias detection and mitigation
- Toxicity and harm prevention

**Business Logic Layer:**
- Rule-based constraints for business requirements
- Template validation for structured outputs
- Workflow compliance checking
- Domain-specific validation rules

### 5. Defensive UX Design
**Design interfaces that handle AI unpredictability gracefully.**

**Core Principles:**
- **Manage expectations:** Clearly communicate AI capabilities and limitations
- **Provide transparency:** Show confidence levels, data sources, reasoning steps
- **Enable easy correction:** Allow users to quickly fix or redirect AI outputs
- **Graceful degradation:** Handle failures without breaking user workflow

**Specific Patterns:**
- **Progressive disclosure:** Start simple, allow users to request more detail
- **Confidence indicators:** Show uncertainty when model is unsure
- **Source attribution:** Link outputs to underlying data sources
- **Undo/redo functionality:** Allow easy reversal of AI actions
- **Human escalation:** Clear paths to human assistance when AI fails

### 6. Structured Output Generation
**Ensure outputs integrate cleanly with downstream systems.**

**Techniques:**
- **Schema-constrained generation:** Force outputs to match predefined JSON schemas
- **Template-based generation:** Use structured templates with fill-in-the-blank patterns
- **Multi-step validation:** Generate, validate, and regenerate if needed
- **Type-safe parsing:** Use strongly typed parsers to catch malformed outputs

**Benefits:**
- Easier integration with existing systems
- Reduced parsing errors in downstream applications
- More reliable automated processing
- Better error handling and debugging

## Advanced System Patterns

### 7. Multi-Agent Architectures
**Coordinate multiple specialized LLMs for complex tasks.**

**Patterns:**
- **Pipeline architecture:** Sequential processing through specialized agents
- **Hierarchical architecture:** Supervisor agent coordinating worker agents
- **Collaborative architecture:** Agents working together on shared tasks
- **Competitive architecture:** Multiple agents proposing solutions, best one selected

**Coordination Mechanisms:**
- Shared memory for agent communication
- Message passing between agents
- Central orchestrator for workflow management
- Consensus mechanisms for decision making

### 8. Context Management
**Handle long conversations and large document processing.**

**Strategies:**
- **Sliding window:** Keep recent context, discard older content
- **Summary compression:** Compress older context into summaries
- **Hierarchical contexts:** Maintain multiple context levels (session, conversation, task)
- **External memory:** Store important information in external systems

**Implementation:**
- Automatic context pruning when approaching limits
- Important information extraction and persistence
- Context relevance scoring for retention decisions
- User control over context management

### 9. Human-in-the-Loop Workflows
**Integrate human oversight at critical decision points.**

**Integration Points:**
- **Review gates:** Human approval before critical actions
- **Quality control:** Human validation of outputs before delivery
- **Edge case handling:** Human intervention for unusual scenarios
- **Feedback collection:** Human ratings for continuous improvement

**Design Considerations:**
- Minimize human cognitive load
- Clear escalation criteria and procedures
- Efficient review interfaces and workflows
- Feedback integration for system learning

## System Architecture Considerations

### Reliability and Robustness
- **Graceful degradation:** System continues functioning when components fail
- **Circuit breakers:** Prevent cascading failures from external services
- **Retry logic:** Handle transient failures with exponential backoff
- **Fallback mechanisms:** Alternative approaches when primary methods fail

### Scalability Patterns
- **Async processing:** Handle long-running LLM calls without blocking
- **Load balancing:** Distribute requests across multiple model instances
- **Batching:** Group requests for more efficient processing
- **Resource pooling:** Share expensive resources across multiple requests

### Security Considerations
- **Input sanitization:** Prevent prompt injection and malicious inputs
- **Output filtering:** Remove sensitive information from responses
- **Access controls:** Ensure users can only access appropriate functionality
- **Audit logging:** Track system usage for security and compliance

### Monitoring and Observability
- **Performance metrics:** Track latency, throughput, error rates
- **Quality metrics:** Monitor output quality and user satisfaction
- **Usage patterns:** Understand how system is being used
- **Cost tracking:** Monitor token usage and computational expenses

## Integration Patterns

### API Design for LLM Systems
- **Async interfaces:** Handle long-running generation tasks
- **Streaming responses:** Provide real-time output as it's generated
- **Webhook notifications:** Notify clients when async tasks complete
- **Versioning:** Handle model updates without breaking clients

### Database Integration
- **Vector databases:** Store and search document embeddings
- **Hybrid storage:** Combine relational and vector data
- **Caching layers:** Reduce database load for frequent queries
- **Backup strategies:** Handle data persistence for generated content

### Third-Party Service Integration
- **API rate limiting:** Respect external service constraints
- **Failure handling:** Graceful degradation when services unavailable
- **Cost management:** Monitor and control external API usage
- **Security:** Protect credentials and sensitive data in transit

## Testing Strategies

### Unit Testing for LLM Components
- **Deterministic testing:** Test components with fixed inputs/outputs
- **Mock external services:** Isolate LLM-specific logic
- **Regression testing:** Prevent quality degradation over time
- **Performance testing:** Validate latency and throughput requirements

### Integration Testing
- **End-to-end workflows:** Test complete user journeys
- **Cross-component testing:** Validate component interactions
- **Load testing:** Ensure system handles expected traffic
- **Chaos testing:** Validate resilience to component failures

### Evaluation-Based Testing
- **Automated quality assessment:** Run evaluations in CI/CD pipelines
- **A/B testing:** Compare different approaches systematically
- **Shadow testing:** Test new models against production traffic
- **Canary deployments:** Gradual rollout with quality monitoring

## Common Anti-Patterns to Avoid

### The Magic Black Box
**Problem:** Treating LLM as infallible oracle without validation or constraints.
**Solution:** Always validate outputs, implement guardrails, design for failure modes.

### Over-Prompt Engineering
**Problem:** Trying to solve all problems with increasingly complex prompts.
**Solution:** Use systematic approaches like RAG, fine-tuning, or architectural solutions.

### Context Stuffing
**Problem:** Cramming maximum information into context window without considering attention limitations.
**Solution:** Curate context based on relevance, use external memory systems.

### Evaluation Neglect
**Problem:** Building systems without systematic measurement of quality and performance.
**Solution:** Implement evaluation from the start, use metrics to drive improvements.

## Success Metrics

You're applying these patterns effectively when:
- System behavior is predictable and reliable across different inputs
- Quality degrades gracefully under edge conditions
- Performance scales appropriately with increased usage
- Maintenance and debugging are systematic rather than trial-and-error
- User experience remains consistent despite underlying AI unpredictability

The goal is building LLM systems that feel like reliable software products, not research experiments.
