# AI System Evaluation

**Systematic methodology for measuring, debugging, and improving AI applications.**

---
name: AI System Evaluation
description: Apply proven evaluation methodologies to measure AI system performance, identify failure patterns, and drive systematic improvements
user-invocable: true
argument-hint: [ai-system-or-task]
---

## Core Philosophy

Most teams spot-check AI outputs by hand instead of measuring systematically. This leads to shipping changes without knowing their impact and being unable to prioritize improvement efforts effectively.

**Key insight:** Evaluation is not overhead—it's the foundation that makes everything else possible. Without evals, you can't distinguish improvements from regressions.

## The Four-Step Evaluation Methodology

### Step 1: Data Collection and Analysis
**Look at real data before building evaluation criteria.**

**Manual Review Process:**
1. Collect 50-100 representative traces/outputs
2. Review each trace and write open-ended notes about failures
3. Don't try to categorize initially—just observe and document
4. Look for patterns in how and where the system breaks

**Trace Definition:** Complete record of all actions, messages, tool calls, and data retrievals from initial user query through final response.

**What to Note:**
- First failure you observe in each trace (upstream errors cause downstream issues)
- Context where errors occur (specific workflows, edge cases, data types)
- Patterns across multiple failures
- Surprising successes as well as failures

### Step 2: Failure Taxonomy Creation
**Group similar failures into distinct categories.**

**Categorization Process:**
1. Take your open-ended notes from Step 1
2. Group similar failure types together
3. Name each category with specific, actionable terms
4. Count failures in each category to identify priorities
5. Continue until reaching theoretical saturation (new traces don't reveal new failure modes)

**Good Failure Categories:**
- "Date parsing failure" (specific, actionable)
- "Context overflow in multi-turn conversation" (specific, actionable)
- "Hallucinated API endpoint" (specific, actionable)

**Bad Failure Categories:**
- "AI made a mistake" (too vague)
- "Output quality issue" (not actionable)
- "User didn't like it" (no diagnostic value)

### Step 3: Binary Evaluation Design
**Create simple, unambiguous tests for each failure category.**

**Binary over Likert:** Instead of 1-5 ratings, use pass/fail criteria. This forces clearer thinking and more consistent labeling.

**Evaluation Criteria Examples:**
- "Does the response include a specific number?" (Yes/No)
- "Did the system correctly parse the date format?" (Yes/No)  
- "Is the API endpoint valid and reachable?" (Yes/No)
- "Does the response stay within the specified character limit?" (Yes/No)

**Each criterion must be:**
- Unambiguous (two people reviewing same output get same result)
- Specific to important system behavior
- Directly related to user value
- Measurable without domain expertise

### Step 4: Systematic Improvement Loop
**Use evaluation data to drive targeted improvements.**

**Improvement Process:**
1. Run evals on current system to establish baseline
2. Identify highest-priority failure categories
3. Make targeted changes to address specific failure modes  
4. Re-run evals to measure impact
5. Iterate based on what moved the metrics

**Focus Areas:**
- Fix highest-frequency failures first
- Address failures that block user workflows
- Improve failures with clearest intervention paths

## Evaluation Implementation Patterns

### LLM-as-a-Judge Approach
**Use another LLM to evaluate outputs systematically.**

**Best Practices:**
- Start with clear, binary evaluation criteria
- Provide specific examples of good/bad outputs
- Use structured prompts with consistent format
- Validate LLM judgments with human spot-checks
- Measure inter-rater reliability between human and LLM evaluators

**Template:**
```
Evaluate this AI assistant response:

CRITERIA: [specific, binary criterion]
USER QUERY: [original query]
AI RESPONSE: [response to evaluate]

EVALUATION:
- Does the response meet the criteria? (YES/NO)
- Explanation: [brief reasoning]
- Confidence: (HIGH/MEDIUM/LOW)
```

### Code-Based Evaluations
**When possible, use deterministic code checks.**

**Examples:**
- API response validity (HTTP status, JSON structure)
- Output format compliance (character limits, required fields)
- Factual accuracy (verifiable against known database)
- Performance metrics (response time, token usage)

**Benefits:**
- Completely reliable and consistent
- Fast to run at scale
- No ambiguity in scoring
- Can be automated in CI/CD pipelines

### Human Evaluation Workflows
**When human judgment is necessary.**

**Annotation Guidelines:**
1. Create specific rubrics with examples
2. Train annotators on edge cases
3. Measure inter-annotator agreement
4. Use multiple annotators for important decisions
5. Spot-check for annotator drift over time

**Efficient Sampling:**
- Don't evaluate everything—strategic sampling is sufficient
- Focus on edge cases and boundary conditions
- Oversample rare but critical failure modes
- Use clustering to ensure diverse coverage

## Advanced Evaluation Techniques

### Root Cause Analysis
**Go beyond surface-level failure classification.**

**Analysis Process:**
1. Identify systematic failure patterns
2. Trace failures back to root causes
3. Distinguish correlation from causation
4. Test hypotheses about why failures occur

**Common Root Causes:**
- Insufficient context for complex decisions
- Training data gaps for specific domains
- Prompt ambiguity leading to inconsistent interpretation
- Tool/API limitations in specific scenarios

### Multi-Step Pipeline Evaluation
**For agentic systems with multiple components.**

**Component-Level Testing:**
- Test each component in isolation
- Identify where in the pipeline failures occur
- Measure error propagation across components
- Validate assumptions about component interactions

**End-to-End Testing:**
- Test complete user workflows
- Measure cumulative success rates
- Identify compound failure modes
- Validate that component improvements translate to system improvements

### Regression Testing
**Prevent improvements in one area from breaking others.**

**Test Suite Management:**
- Maintain representative test cases covering main functionality
- Run full evaluation suite before deploying changes
- Track metrics over time to identify degradation
- Balance comprehensive coverage with execution speed

## Production Deployment Patterns

### Evaluation Gates in CI/CD
**Automated quality controls in development pipelines.**

**Implementation:**
1. Run evaluation suite on every code change
2. Set minimum thresholds for deployment approval
3. Automatically flag significant metric changes
4. Require human review for threshold violations

### A/B Testing for AI Systems
**Controlled rollouts with measurement.**

**Setup:**
- Deploy changes to subset of users
- Measure both business metrics and evaluation metrics
- Compare treatment vs control groups
- Scale successful changes gradually

### Continuous Monitoring
**Ongoing measurement in production.**

**Monitoring Framework:**
- Real-time evaluation of production outputs
- Alerts for metric degradation
- Regular sampling and human review
- Performance tracking over time

## Common Pitfalls and Solutions

### Generic Evaluation Trap
**Problem:** Using generic criteria like "helpfulness" or "correctness" instead of product-specific measures.
**Solution:** Focus on specific product problems your system needs to solve. Evaluate "human handoff failure" not "helpfulness."

### Tools-First Mindset
**Problem:** Focusing on evaluation dashboards and frameworks before understanding what to measure.
**Solution:** Start with manual review and clear criteria. Add tooling only when manual process is proven valuable.

### Insufficient Sample Size
**Problem:** Making decisions based on small, unrepresentative samples.
**Solution:** Collect enough data to reach statistical significance. Use stratified sampling to ensure coverage.

### Annotator Bias
**Problem:** Human evaluators introducing systematic biases.
**Solution:** Use multiple annotators, measure agreement, provide clear guidelines, and rotate reviewers regularly.

## Integration with Development Workflow

### Eval-Driven Development
**Design evaluation criteria before building features.**

Process:
1. Define what success looks like before coding
2. Create evaluation criteria early in development
3. Use evals to guide implementation decisions
4. Validate that final implementation meets evaluation criteria

### Feature Development Cycle
1. **Define:** Clear success criteria and evaluation approach
2. **Build:** Minimal implementation focused on success criteria
3. **Evaluate:** Run systematic evaluation to measure performance
4. **Iterate:** Use evaluation insights to drive improvements
5. **Deploy:** Launch with evaluation monitoring in place

### Team Collaboration
- Share evaluation criteria across engineering and product teams
- Use evaluation data to prioritize feature work
- Include domain experts in evaluation design
- Make evaluation results visible to stakeholders

## Success Metrics

You're applying this skill effectively when:
- You can quickly identify where your AI system is failing
- Changes to the system have measurable, predictable impacts
- Team discussions focus on concrete metrics rather than subjective impressions
- Improvement efforts are prioritized based on data rather than intuition
- System quality improves systematically over time

The goal is to transform "this seems wrong" into "here's exactly what's failing and here's how to fix it systematically."
