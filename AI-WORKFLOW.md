# AI Workflow & Meta Log

This document tracks how I used AI tools during this project, what I delegated, and specifically where the AI failed and had to be corrected.

---

## 1. Data Generation (The Empty String Bug)
**Date:** 2026-07-31

**What I Delegated:** 
I used AI (Gemini) to quickly scaffold the boilerplate Python script (`data_generator.py`) to generate the ~3,000 poles and 40 DTs. I gave it the exact mathematical constraints (60% missing topology, 9% missing devices).

**Where the AI Failed:**
The AI wrote logic that assigned an empty string `""` to the `seq_on_line` variable for the 60% of transformers that needed missing topology. However, in the very next block of code, its tree-building loop tried to calculate the position of the *next* pole by doing `seq_on_line = parent_pole["seq_on_line"] + 1`. 

Because it was blindly trying to add an integer `1` to an empty string `""`, the script immediately crashed with a `TypeError`. The AI confidently wrote broken mathematical logic.

**How I Caught & Fixed It:**
I ran the script locally, caught the Python traceback, and immediately spotted the logical gap. I then prompted the AI with the traceback and the specific flaw I identified, instructing it to implement a hidden, internal integer tracker (`_seq_on_line`). The AI generated the corrected tree-generation loop using this tracker. This allowed the script to mathematically build the physical tree in memory, and I verified that the final filter successfully scrubbed the internal tracker to export the required blank strings to the CSV. 

---

## 2. Architectural Brainstorming (The Missing Topology Problem)
**Date:** 2026-07-31

**What I Delegated:** 
While mapping out the Fault Localization algorithm, I hit a conceptual roadblock regarding the core constraint: "How can the algorithm find a fault if 60% of the wiring data is missing?" I used the AI as a sounding board, asking it to brainstorm algorithmic solutions based on the data we *did* have available (the 100% complete GPS coordinates).

**How it helped:**
The AI suggested a "Geometric Minimum Spanning Tree (MST)" to infer the topology based on physical proximity (the logic being that copper wire is expensive, so utilities connect to the closest adjacent pole). I reviewed this approach and approved it as mathematically sound. I then directed the AI to refine this idea by adding a product feature: any faults localized on an inferred MST tree must be visually flagged with a "Low Confidence" warning in the Control Room UI, so engineers aren't misled by guessed data. This proved the AI is excellent for bouncing algorithmic theories, provided I guide the final product logic.

---

## 3. Algorithmic Debugging (The Silent Failure Trap)
**Date:** 2026-07-31

**What I Delegated:** 
We were discussing the core Boundary Detection algorithm. The AI proposed a simple rule: "Trace UP from a dark pole until you hit a live pole. The wire between them is what broke." 

**Where the AI Failed:**
I immediately realized the AI's logic was flawed and challenged it with a hypothetical: *What if the wire broke at A->B, but Pole B's sensor is dead?* Pole B stays silent, so the database still thinks it is "live". Pole C (further down) screams that it is dark. If the AI just traces UP from C, it hits B, thinks B is live, and incorrectly concludes the fault is B->C! The AI had completely missed the "hidden failure" edge case.

**How I Caught & Fixed It:**
I reasoned with the AI that we cannot trust a silent node. The AI then attempted to fix it by saying: "If Pole B's other child, Pole D, is also dark, it proves all of B's children are dark."
I caught *another* logical error in the AI's reasoning. I pointed out: *If D is dark, it doesn't prove ALL children are dark. What if B has a third child, E, that is still live?* 

By aggressively questioning the AI's logic, I forced it to refine the algorithm until we arrived at the mathematically perfect **"Implied State"** rule:
- If ANY child is live, the parent MUST be live (power is flowing through it).
- Only if ALL children are dark can we imply the parent is dark. 

I then instructed the AI to write this exact "Implied State" post-order traversal into the `graph_engine.py` to mathematically prove the state of silent sensors before attempting to find the boundary. This interaction highlighted the danger of blindly trusting AI algorithms for physical systems—you must always aggressively test its logic against real-world physics.

---

## 4. Final Algorithmic Polish (The Lying Sensor & Massive Failures)
**Date:** 2026-07-31

**What I Delegated:**
After finalizing the Silent Sensor logic, I reviewed the assignment brief's constraints one final time. I challenged the AI on three specific edge cases it had missed in its architecture:
1.  **The Lying Sensor:** What if a node isn't silent, but actually explicitly sends a `power_lost` event because its own lamp circuit broke, even though power is still flowing through it?
2.  **Feeder & DT Faults:** The AI was only programmed to find broken spans. It had no concept of a Distribution Transformer blowing up or a Feeder tripping.
3.  **Out-of-Order Execution:** The AI forgot to implement the sequence check to handle the +/- 90s clock skew.

**How it helped:**
Because I laid out the precise constraints from the brief, the AI generated a final `implementation_plan.md` to completely overhaul the engine. 
- It upgraded the "Implied State" rule to forcefully override *explicitly* lying sensors. 
- It added group-hierarchy checks to successfully categorize `dt_fault` and `feeder_fault` types instead of returning hundreds of individual span breaks.
- It added the `last_seq` check to the FastAPI endpoint to drop stale, delayed packets.

By acting as the Senior Architect and constantly cross-referencing the AI's output against the product requirements document, I ensured the final localization engine is 100% compliant with every edge case in the brief.
