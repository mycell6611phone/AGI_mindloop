Overview

The repository centers on agi_mindloop/core_loop.py, which orchestrates a multi-stage reasoning cycle: load configuration, collect user input, plan and critique via LLM calls, choose and execute an action in a sandbox, optionally store the experience, and emit telemetry before repeating for a configured number of cycles.
Initialization Phase

    Configuration – load_config converts config/config.yaml into dataclasses describing runtime parameters, LLM defaults, model endpoints, persona location, prompt directory, memory settings, and safety thresholds.

Interface – Interface() tries to launch a Tk chat UI but falls back to headless I/O if Tk is unavailable, exposing get_input/send_output for the core loop.

Engine bundle – main builds four Gpt4AllAPIEngine instances (neutral, mooded, summarizer, coder) using model names from the config, packaging them into an EngineBundle for downstream components.

Personas – PersonaRegistry retrieves the neutral baseline and the active persona prompt text from the persona directory, defaulting to empty or fallback strings when files are missing.

Prompts – PromptLoader reads stage-specific prompt files when present, otherwise serves internal defaults for planner, critic, explainer, judge, and curation stages.

Generation options & memory pool – The loop copies the configured generation defaults into a GenOptions object and starts an empty experience pool for later curation.

Sandbox – A Sandbox instance whitelists specific binaries and enforces CPU/memory limits, translating action strings like sh: or ! into safe subprocess calls; everything else becomes a no-op record.
Per-Cycle Data Flow

    Telemetry & input – Each loop iteration logs cycle.start, then blocks on Interface.get_input, which either waits for GUI text or returns a stub “demo input” in headless mode.

Planning – make_plan composes the persona system prompt with the planner stage system text, formats the user prompt with the current input plus recall (currently a stub string), and submits it to the mooded engine; the stripped response is the plan.

Self-critique – critique repeats the persona+critic prompt composition to have the mooded engine assess the plan for risks and improvements.

Action selection

    choose_action loads the evaluation prompt and delegates to decide_actions, passing both persona and neutral system prompts and the two engines.

decide_actions evaluates each candidate action (here just do:<input>) twice via _eval: once with persona B, once with neutral A. _eval builds a JSON-only prompt and calls each engine; parse_eval extracts label, reason, utility, and risk from the response.

The neutral judge can veto on risk ≥ veto_risk; otherwise persona approval is required. Among acceptable options, the routine maximizes a blended expected value (70% persona, 30% neutral).

Action execution – If an ActionDecision is returned, _execute_action_decision formats it: do: actions become simulated notes, sh:/! commands run through the sandbox; string actions are passed similarly. Sandbox runs enforce allowlisting and resource limits, returning success/failure metadata.

Explanation – explain contacts the neutral engine with the explainer prompt (response currently unused) and constructs a deterministic textual summary of input, plan, and critique for auditing.

Memory gate – should_store asks both neutral and persona engines to judge the combined transcript using the judge prompt; neutral responses can veto on risk, while persona approval controls acceptance. Accepted explanations are appended to the pool for future training.

Training stub – curate_if_needed currently returns placeholders for validated/rejected/pending memories without mutating the pool, signaling a future hook for self-training curation.

User feedback – The loop normalizes the sandbox result into a short summary and pushes it through the interface (GUI bubble or console print).

Stability monitoring – The code computes a drift metric comparing action utilities/risks to baseline means and logs both checks and violations, guarding against runaway behavior; errors in this block are logged but non-fatal.

Cycle completion – log("cycle.end") closes the iteration before the next loop begins.
External Interactions

    LLM backend – Gpt4AllAPIEngine sends POST requests to a local GPT4All REST server with the composed messages and generation parameters, handling transport and response validation; swapping to OpenAI would require instantiating OpenAIEngine or using agi_mindloop.llm.build_engines.

Telemetry – All telemetry uses a simple UTC timestamped log function, writing events and structured metadata to stdout for later ingestion.
Data Flow Summary

    Config → main initialization → interface/personas/prompts/engines/sandbox.

Each cycle: input → plan (make_plan) → critique (critique) → evaluate actions (decide_actions/parse_eval) → sandbox execution → explanation (explain) → memory vote (should_store/parse_judgment) → curation stub → user feedback → stability telemetry.
