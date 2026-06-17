# Verified Reasoning Coach

CiTT's tutor direction is student-agency-first, not answer-first. The solver and verifier still own truth, but the student must first commit a reasoning frame before the system reveals final values.

## Product Claim

CiTT is a personalized, verification-grounded apprenticeship system for biomedical instrumentation problem solving. It lets students make incomplete and even wrong attempts, then uses deterministic solvers, verification checks, and coaching feedback to help them discover the next step themselves before revealing final answers.

This addresses two risks at once:

- Hallucinated numerical answers are blocked because numbers come from solver and verifier output.
- Student dependence is reduced because the default interaction is a local nudge, not a final answer.

## Three Laws

1. Truth must be verified.

   Numerical answers, units, signs, phasors, currents, and powers must come from the solver/verifier path or be compared against it.

2. Thinking must be student-owned.

   The student commits a current frame before seeing a solution path. The coach checks that frame and asks the student to choose the next move.

3. Feedback must be local.

   The coach returns one current blocker or next move. It does not correct every issue in one pass.

## Learning Loop

```text
Commit -> Check -> Nudge -> Choose -> Reflect
```

- Commit: the student submits a plan, unknown, first equation, assumption, confidence estimate, preferred representation mode, or freeform attempt.
- Check: CiTT parses and solves the problem internally, then compares the attempt against verified hidden truth.
- Nudge: the response includes one targeted hint and one next question.
- Choose: the student selects the next method move.
- Reflect: the response updates a lightweight student model and reflection journal.

## Hint Ladder

- Level 0: reflection only
- Level 1: conceptual nudge
- Level 2: method choice
- Level 3: equation scaffold
- Level 4: numerical checkpoint without final values
- Level 5: full verified reveal

The `/reasoning_coach` endpoint defaults to withholding final values. Level 5 reveal is allowed only after the student has committed a reasoning frame and the hidden packet has a `PASS` verification badge.

If a submitted `StudentProfile` shows low independence or a high hint budget, the coach can intentionally cap non-reveal hints to a smaller level so the next turn still belongs to the student.

## API

`POST /reasoning_coach`

```json
{
  "problem_text": "A 10 V voltage source is connected in series with R1 = 2 kOhm and R2 = 3 kOhm. Find the voltage across R2 and the current through the circuit.",
  "mode": "demo",
  "requested_hint_level": 1,
  "representation_mode": "physical_intuition",
  "student_commitment": {
    "attempt_text": "I think this is a divider, but I am not sure about current direction.",
    "confidence_percent": 45
  },
  "student_profile": {
    "strengths": [],
    "recurring_misconceptions": {
      "sign_convention": 2
    },
    "hint_preference": "conceptual_nudges",
    "independence_level": "medium",
    "hint_budget_used": 2,
    "completed_attempts": 0
  }
}
```

Response fields:

- `verification_badge`: hidden solver/verifier status, without exposing final values.
- `student_frame`: parsed view of the student's partial thinking.
- `local_check`: one local blocker or next-step status.
- `nudge`: hint level, message, representation prompt, next question, and student choices.
- `profile_update`: updated misconception counts, strengths, hint budget, and independence level.
- `adaptive_practice`: small follow-up prompts targeted at the current misconception.
- `reflection`: compact learning journal entry with `today_i_learned` bullets.
- `solution_packet`: `null` until Level 5 reveal is allowed.

`student_frame.source` is:

- `heuristic` for deterministic local extraction.
- `gemini` when Gemini successfully classified the student's partial reasoning.
- `gemini_fallback` when Gemini mode was requested but unavailable or invalid, and deterministic extraction was used.

Representation modes:

- `diagram`
- `kcl_equation`
- `physical_intuition`
- `units_magnitude`
- `biomedical_context`

## Misconception Tags

The first implementation detects common learning issues with deterministic heuristics:

- `common_mode_as_differential`
- `inappropriate_divider_shortcut`
- `sign_convention`
- `capacitor_dc_behavior`
- `ideal_op_amp_input_current`
- `unit_prefix`
- `aliasing_nyquist_misread`

These tags are intentionally small and teachable. They are returned in `profile_update.recurring_misconceptions`, so a UI, instructor dashboard, or future persistence layer can track patterns across attempts.

## Adaptive Practice

When a local issue maps to a misconception tag, the response includes two deterministic `adaptive_practice` prompts. They are deliberately smaller than the original problem and target one misconception at a time.

Example:

```json
{
  "id": "diff_common_split_1",
  "target_misconception": "common_mode_as_differential",
  "prompt": "An instrumentation amplifier sees +1.01 V and +0.99 V at its two inputs. Before calculating output, name Vdiff and Vcm.",
  "goal": "Practice separating the small differential signal from the shared common-mode level.",
  "representation_mode": "biomedical_context",
  "source": "deterministic_template"
}
```

## Instructor Dashboard

`POST /instructor_dashboard`

```json
{
  "student_profiles": [
    {
      "strengths": [],
      "recurring_misconceptions": {
        "sign_convention": 3,
        "unit_prefix": 1
      },
      "hint_preference": "diagram",
      "independence_level": "medium",
      "hint_budget_used": 3,
      "completed_attempts": 1
    }
  ]
}
```

The response summarizes class-level patterns from the submitted profiles:

- `student_count`
- `cohort_independence`
- `misconception_summary`
- suggested intervention for each misconception

This endpoint is stateless. It does not store student data; it aggregates what the caller sends.

## Current Boundary

The coach layer is not a new truth engine. It delegates parsing and verification to the existing pipeline, then shapes the visible tutoring response. Future work can replace or augment the deterministic student-frame extraction with an LLM, but final numerical authority must remain solver/verifier-grounded.

Current LLM boundary: Gemini may classify the student's partial reasoning in `gemini` and `gemini_strict` modes, but its schema has no answer fields and its prompt forbids solving. If Gemini is unavailable, the coach falls back to deterministic heuristics and returns a warning.

Current persistence boundary: student profiles and dashboard inputs are portable payloads, not database-backed records. A production system can persist those profiles later without changing solver authority.
