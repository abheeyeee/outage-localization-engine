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
