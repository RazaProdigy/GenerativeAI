# Iterative Workflow Implementation - Changes Summary

## Overview

The RAG Question Generator has been enhanced with an **iterative optimization workflow**. Questions are now refined through multiple iterations based on evaluation feedback until they meet quality standards or reach the maximum iteration limit.

## Key Changes

### 1. New Component: Question Optimizer Agent

**File:** `rag_question_generator/agents/question_optimizer.py`

- Created a new `QuestionOptimizerAgent` class
- Takes unapproved questions and their evaluation feedback
- Uses LLM to optimize questions based on specific improvement suggestions
- Preserves approved questions while refining unapproved ones
- Returns all questions in the same order to maintain consistency

### 2. Enhanced Workflow State

**File:** `rag_question_generator/graph/multi_agent_workflow.py`

Added new state fields to `WorkflowState`:
- `current_iteration`: Tracks the current iteration number
- `max_iterations`: Maximum allowed iterations (default: 5)
- `optimization_feedback`: Stores feedback for optimization

### 3. Modified Workflow Graph

**File:** `rag_question_generator/graph/multi_agent_workflow.py`

**New Workflow Structure:**
```
retrieve → generate → evaluate → [decision] → optimize → [loop back to evaluate]
                                      ↓
                                  finalize → END
```

**Key Methods Added:**
- `_should_optimize()`: Conditional routing logic
  - Routes to "finalize" if all questions approved OR max iterations reached
  - Routes to "optimize" if questions need improvement
- `_optimize_questions()`: Optimizer node
  - Optimizes questions based on evaluation feedback
  - Increments iteration counter
- `_prepare_optimization_feedback()`: Creates feedback summary for unapproved questions

**Updated Methods:**
- `_evaluate_questions()`: Now tracks iterations and prepares optimization feedback
- `run_workflow()`: Accepts `max_iterations` parameter (default: 5)
- `get_workflow_status()`: Returns iteration tracking info

### 4. API Changes

**File:** `rag_question_generator/api/models.py`

Updated `QuestionRequest` model:
- Added `max_iterations` field (default: 5, range: 1-10)

**File:** `rag_question_generator/api/endpoints.py`

Updated `/generate/questions` endpoint:
- Passes `max_iterations` to workflow execution

### 5. Module Exports

**File:** `rag_question_generator/agents/__init__.py`

- Added `QuestionOptimizerAgent` to exports

### 6. Documentation Updates

**File:** `README.md`

- Updated architecture diagram with iterative loop
- Added detailed explanation of iterative workflow
- Updated API documentation with `max_iterations` parameter
- Enhanced evaluation criteria section
- Added reference to new test script

### 7. New Test Script

**File:** `test_iterative_workflow.py`

- Comprehensive test for iterative optimization workflow
- Shows iteration progress and optimization results
- Displays evaluation metrics across iterations
- Provides detailed output of approved questions

## How It Works

### Workflow Flow

1. **Initial Generation**: Questions generated from retrieved documents
2. **First Evaluation**: Questions evaluated against quality criteria
3. **Decision Point**: 
   - ✅ All approved? → Finalize and return
   - ❌ Some unapproved? → Continue to optimization
4. **Optimization**: Unapproved questions refined based on feedback
5. **Re-evaluation**: Loop back to evaluation (step 2)
6. **Termination**: Process ends when:
   - All questions meet standards, OR
   - Maximum iterations (default: 5) reached

### Iteration Tracking

- `current_iteration` starts at 1
- Increments after each optimization
- Workflow continues while `current_iteration < max_iterations`
- Prevents infinite loops while allowing quality improvements

### Evaluation Feedback Loop

1. Evaluator identifies issues:
   - Low clarity scores
   - Difficulty mismatches
   - Content accuracy problems
   - Low educational value
2. Generates specific improvement suggestions
3. Optimizer receives:
   - Original questions
   - Evaluation scores
   - Detailed feedback
   - Improvement suggestions
4. Optimizer refines questions addressing each issue
5. Re-evaluated in next iteration

## Benefits

1. **Higher Quality**: Multiple refinement opportunities ensure better questions
2. **Automatic Improvement**: No manual intervention needed
3. **Controlled Iterations**: `max_iterations` prevents infinite loops
4. **Feedback-Driven**: Optimization based on specific evaluation criteria
5. **Transparent**: Iteration tracking shows optimization progress
6. **Flexible**: Configurable iteration limits for different use cases

## API Usage

### Before (Sequential):
```json
{
  "concept": "machine learning",
  "num_questions": 5
}
```
Result: Generated → Evaluated → Filtered (no optimization)

### After (Iterative):
```json
{
  "concept": "machine learning",
  "num_questions": 5,
  "max_iterations": 5
}
```
Result: Generated → Evaluated → Optimized (up to 5 times) → Filtered

## Response Enhancements

The workflow status now includes:
```json
{
  "workflow_status": {
    "status": "workflow_completed",
    "current_iteration": 3,
    "max_iterations": 5,
    "optimization_feedback": "...",
    "questions_generated": 5,
    "questions_approved": 5,
    ...
  }
}
```

This shows:
- How many iterations were needed
- Whether max iterations was reached
- Specific feedback from evaluations

## Testing

Run the new test script:
```bash
python test_iterative_workflow.py
```

This will:
1. Verify vector store has documents
2. Run workflow with iterative optimization
3. Display iteration-by-iteration progress
4. Show final results and approval metrics
5. Demonstrate optimization effectiveness

## Backward Compatibility

✅ **Fully backward compatible**
- `max_iterations` defaults to 5 if not specified
- Existing API calls work without changes
- Only new functionality added, nothing removed

## Configuration

Adjust `max_iterations` based on your needs:
- **1**: No optimization (immediate finalization after first evaluation)
- **3-5**: Balanced (default: 5)
- **7-10**: Aggressive optimization (may increase API costs)

## Performance Considerations

- Each iteration involves LLM calls for evaluation and optimization
- More iterations = higher OpenAI API costs
- Default of 5 iterations provides good balance
- Questions approved early exit the loop immediately
- Only unapproved questions trigger optimization

## Summary of Files Modified

1. ✨ **NEW**: `rag_question_generator/agents/question_optimizer.py`
2. 🔧 **MODIFIED**: `rag_question_generator/graph/multi_agent_workflow.py`
3. 🔧 **MODIFIED**: `rag_question_generator/api/models.py`
4. 🔧 **MODIFIED**: `rag_question_generator/api/endpoints.py`
5. 🔧 **MODIFIED**: `rag_question_generator/agents/__init__.py`
6. 📝 **MODIFIED**: `README.md`
7. ✨ **NEW**: `test_iterative_workflow.py`
8. ✨ **NEW**: `ITERATIVE_WORKFLOW_CHANGES.md` (this file)

## Next Steps

To use the new iterative workflow:

1. Ensure environment is set up with OpenAI API key
2. Upload a PDF document using `/ingest` endpoint
3. Call `/generate/questions` with optional `max_iterations` parameter
4. Monitor `workflow_status.current_iteration` to see optimization progress
5. Review approved questions that have been refined through iterations

---

**Implementation Date:** October 2025
**Feature Status:** ✅ Completed and Tested

