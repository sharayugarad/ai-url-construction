# Surgical Coding Principles

**Precise, minimal-change development methodology for reliable systems.**

---
name: Surgical Coding Principles
description: Apply surgical precision to code changes - making minimal, targeted modifications that achieve objectives without introducing unnecessary complexity or risk
user-invocable: true
argument-hint: [development-task]
---

## Core Philosophy

Most software problems are solved with too much code, too much abstraction, and too many changes at once. Surgical coding is about finding the minimal intervention that solves the problem completely.

**Key insight:** The best code change is often 10 lines, not 1000. The best architecture is often boring, not clever.

## The Four Surgical Principles

### 1. Minimal Sufficient Change
**Make the smallest change that completely solves the problem.**

**Before coding, ask:**
- What is the exact problem I'm solving?
- What is the minimal code change that addresses this specific problem?
- Am I solving problems I don't actually have?
- Can I solve this with a configuration change instead of code?

**Implementation:**
- Start with the simplest possible solution
- Add complexity only when the simple solution proves insufficient
- Prefer boring, obvious solutions over clever ones
- Measure twice, cut once - think through the change before implementing

**Example:**
```
❌ Bad: Implement entire user management system with roles, permissions, and admin panel
✅ Good: Add single boolean flag for admin users in existing user table
```

### 2. Single Point of Change
**Each change should modify exactly one thing, in exactly one place.**

**Principles:**
- One logical change per commit/pull request
- One file modified when possible, multiple files only when necessary
- One function/class modified when possible
- Changes should be locally contained with clear boundaries

**Benefits:**
- Easy to review and understand
- Simple to revert if problems arise
- Clear cause-and-effect relationship for debugging
- Reduces risk of introducing unrelated bugs

**Example:**
```
❌ Bad: Fix bug + refactor surrounding code + add new feature
✅ Good: Fix bug in isolated commit, refactor in separate commit, add feature in third commit
```

### 3. Preserve Existing Behavior
**Changes should not affect functionality outside the specific problem being solved.**

**Validation:**
- All existing tests pass after changes
- No regression in performance or behavior
- External interfaces remain unchanged unless explicitly modified
- Dependencies and assumptions of calling code remain valid

**Techniques:**
- Use feature flags for new functionality
- Maintain backward compatibility in APIs
- Add new code paths rather than modifying existing ones when possible
- Extensive testing of edge cases and boundary conditions

### 4. Readable Implementation
**Code should be immediately understandable to future maintainers.**

**Clarity Standards:**
- Variable and function names describe purpose, not implementation
- Code structure mirrors problem structure
- Complex logic includes explanatory comments
- Magic numbers and constants are named and explained

**Readability Test:**
- Someone unfamiliar with the code can understand what it does in 2 minutes
- The purpose of each function is clear from its name and signature
- Complex algorithms include examples or references
- Error conditions and edge cases are handled explicitly

## Implementation Patterns

### The Spike-and-Stabilize Pattern
**Explore the problem space, then implement the minimal solution.**

**Process:**
1. **Spike phase:** Quick, experimental implementation to understand the problem
2. **Analysis phase:** Identify the core requirements and constraints  
3. **Minimal implementation:** Write the simplest code that meets requirements
4. **Stabilization:** Add error handling, tests, and documentation

**Why this works:**
- Prevents over-engineering based on incomplete understanding
- Separates exploration from production implementation
- Reduces risk of solving wrong problem with elegant code

### The Constraint-First Pattern  
**Define what you won't do before deciding what you will do.**

**Constraint Categories:**
- **Scope constraints:** Exactly what functionality to include/exclude
- **Performance constraints:** Acceptable latency, throughput, resource usage
- **Compatibility constraints:** Systems that must continue working unchanged
- **Maintenance constraints:** How complex can this reasonably be to maintain

**Example:**
```
Constraints for user authentication:
- Scope: Login/logout only, no password reset or 2FA
- Performance: <100ms login validation
- Compatibility: Must work with existing session system
- Maintenance: Junior developer should be able to debug issues
```

### The Interface-First Pattern
**Design the calling interface before implementing functionality.**

**Process:**
1. Write code that calls the function you're about to implement
2. Design function signature based on how you want to use it
3. Write tests based on the interface design
4. Implement functionality to satisfy tests and interface

**Benefits:**
- Ensures implementation serves actual needs, not imagined ones
- Results in clean, intuitive APIs
- Prevents feature creep during implementation
- Makes testing straightforward

## Code Change Classifications

### Type 1: Bug Fixes
**Correcting incorrect behavior to match specifications.**

**Surgical approach:**
- Identify exact line causing incorrect behavior
- Modify only that logic, not surrounding code
- Add test case that would have caught the bug
- Verify fix doesn't introduce new problems

### Type 2: Feature Addition
**Adding new functionality without changing existing behavior.**

**Surgical approach:**
- Add new code paths rather than modifying existing ones
- Use feature flags to isolate new functionality
- Ensure new features fail gracefully when not enabled
- Maintain all existing functionality unchanged

### Type 3: Performance Optimization
**Improving efficiency without changing external behavior.**

**Surgical approach:**
- Profile to identify actual bottlenecks, not assumed ones
- Optimize only the measured constraint, not generally
- Maintain identical outputs and error conditions
- Benchmark before and after to verify improvement

### Type 4: Refactoring
**Improving code structure without changing external behavior.**

**Surgical approach:**
- Extract/rename only the minimum necessary for clarity
- Change structure incrementally with tests validating each step
- Preserve all existing behavior exactly
- Focus on readability improvements that will actually help future work

## Quality Gates

### Before Starting
- [ ] Problem is clearly defined and bounded
- [ ] Success criteria are specific and measurable
- [ ] Constraints are explicitly documented
- [ ] Approach is the simplest that could work

### During Development
- [ ] Each change is minimal and focused
- [ ] Existing tests continue to pass
- [ ] New functionality has appropriate test coverage
- [ ] Code is readable and well-documented

### Before Committing
- [ ] Change solves stated problem completely
- [ ] No regression in existing functionality
- [ ] Performance impact is acceptable
- [ ] Future maintainer can understand the change

## Common Anti-Patterns to Avoid

### The Swiss Army Knife
**Problem:** Solving multiple loosely related problems in one change.
**Solution:** Separate into distinct, focused changes.

### The Perfect Solution
**Problem:** Over-engineering for imagined future requirements.
**Solution:** Solve current problem simply, refactor when future needs are concrete.

### The Clever Implementation  
**Problem:** Using obscure language features or complex algorithms unnecessarily.
**Solution:** Choose boring, obvious solutions that future maintainers will understand.

### The Shotgun Surgery
**Problem:** Making small changes across many files for one logical change.
**Solution:** Redesign to localize changes, or accept temporary duplication.

### The Foundation Rebuild
**Problem:** Changing fundamental architecture to solve small problems.
**Solution:** Find surgical intervention within existing architecture.

## Debugging with Surgical Precision

### The Binary Search Method
**Isolate problem by systematically eliminating possibilities.**

**Process:**
1. Identify last known working state
2. Find earliest known broken state  
3. Test midpoint between working and broken states
4. Repeat until you isolate exact change that caused problem

### The Minimal Reproduction
**Create smallest possible example that demonstrates the problem.**

**Benefits:**
- Forces precise understanding of problem
- Eliminates irrelevant complexity
- Makes testing solutions faster
- Documents exact conditions where problem occurs

### The Single Variable Change
**When debugging, change only one thing at a time.**

**Discipline:**
- Make one change, test result, record outcome
- Never make multiple changes simultaneously  
- Revert unsuccessful changes before trying alternatives
- Document what you've tried to avoid repeating failed approaches

## Team Integration

### Code Review Focus
**Review changes for surgical precision, not just correctness.**

**Review questions:**
- Is this the minimal change that solves the problem?
- Are the constraints clearly understood and respected?
- Will this be maintainable by the team?
- Does this change introduce unnecessary complexity?

### Documentation Standards
**Document surgical changes for future reference.**

**Required documentation:**
- Problem being solved
- Alternative approaches considered
- Why this approach was chosen
- Constraints and assumptions
- Testing and validation approach

### Knowledge Sharing
**Share surgical techniques with team members.**

**Techniques:**
- Pair programming on complex surgical changes
- Retrospectives on changes that went well or poorly
- Code review comments that explain surgical thinking
- Team discussions about problem decomposition approaches

## Success Metrics

You're applying surgical principles effectively when:
- Changes are easy to review and understand
- Rollback is straightforward when problems occur  
- Debugging focuses on small, isolated problem areas
- Code complexity grows slowly and predictably
- Team velocity stays high because changes don't break unexpectedly

The goal is sustainable development velocity through precise, minimal interventions rather than heroic debugging of complex changes.
