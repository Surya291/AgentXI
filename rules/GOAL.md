Agent XI — Autonomous Fantasy Decision Agent

1. Overview

Agent XI is an experimental autonomous AI agent designed to operate in a constrained, dynamic environment (fantasy cricket) and learn decision-making strategies over time through experience, reflection, and memory.

The goal is not just to optimize outcomes, but to observe and understand how an agent can think, adapt, and evolve strategies in a real-world-like setting.

This project treats fantasy cricket as a sandbox for building long-horizon decision-making agents under:
	•	constraints (budget, team composition, transfers)
	•	uncertainty (player performance, availability)
	•	delayed rewards (season-long scoring)

⸻

2. Core Philosophy

Agent XI is built on the belief that:

Intelligence emerges from interaction + memory + reflection, not just static optimization.

Instead of:
	•	pretraining models
	•	hardcoding heuristics

We aim to:
	•	let the agent form beliefs
	•	test strategies through experience
	•	refine behavior over time

⸻

3. Why Fantasy Cricket?

Fantasy cricket provides a near-ideal environment because it combines:
	•	Constrained optimization (team selection rules)
	•	Sequential decision-making (transfers over time)
	•	Delayed rewards (season-long scoring)
	•	Partial observability (uncertain player performance)
	•	Strategy trade-offs (risk vs consistency)

This makes it structurally similar to:
	•	reinforcement learning environments
	•	portfolio optimization
	•	real-world decision systems

⸻

4. High-Level Architecture

Agent XI is built on top of Hermes Agent, which provides:

Hermes Responsibilities (Core Infrastructure)
	•	Memory management (short-term + long-term)
	•	Tool orchestration
	•	Reasoning loop (observe → think → act → reflect)
	•	Task decomposition
	•	Context persistence

👉 We do NOT rebuild agent infrastructure
👉 We extend Hermes with domain-specific intelligence

⸻

5. Agent XI = Domain Layer on Hermes

We build a domain-specific cognition layer on top of Hermes.

5.1 World Interface (Tools)

We expose structured tools to Hermes:
	•	get_player_data()
	•	get_match_schedule()
	•	get_playing_status()
	•	get_fantasy_points(match_id)
	•	optimize_team(players, constraints)

👉 These act as the agent’s senses and actuators

⸻

5.2 Belief System (Critical Layer)

Agent XI does not rely on predefined stats.

Instead, it builds its own internal representation:

For each player:
	•	form
	•	consistency
	•	trust score
	•	risk level
	•	role understanding

👉 These are learned over time via experience

⸻

5.3 Decision Engine

The agent:
	•	evaluates players based on internal beliefs
	•	selects teams under constraints
	•	chooses captain/vice-captain
	•	decides transfers across matches

A mathematical optimizer (ILP/knapsack) ensures:
	•	all constraints are satisfied
	•	outputs are always valid

👉 Optimization = execution layer, not intelligence layer

⸻

6. Continuous Agent Loop

The system operates as a closed-loop autonomous cycle:

Observe → Think → Decide → Act → Receive Feedback → Reflect → Update Memory

Step-by-step:
	1.	Observe
	•	Player data
	•	Match context
	•	Availability signals
	2.	Think
	•	Evaluate player strengths
	•	Form expectations
	•	Build hypotheses
	3.	Decide
	•	Select team
	•	Plan transfers
	•	Choose captain/VC
	4.	Act
	•	Output decisions (user executes externally)
	5.	Feedback
	•	Receive fantasy points after match
	6.	Reflect
	•	Analyze decisions vs outcomes
	7.	Update
	•	Modify player beliefs
	•	Update strategies

⸻

7. Memory System

Memory is the core learning mechanism.

7.1 Player Memory

Tracks:
	•	historical performance (built over time)
	•	consistency
	•	trust
	•	observations

7.2 Match Reflections

After each match:
	•	what worked
	•	what failed
	•	incorrect assumptions

7.3 Strategy Documents (Macro Learning)

The agent maintains evolving strategy docs:

Examples:
	•	when to use transfers
	•	how to select captains
	•	risk vs reward trade-offs

👉 These evolve across simulations and real runs

⸻

8. Learning Approach (No Model Training)

We do NOT:
	•	fine-tune models
	•	use gradient-based RL

Instead, learning happens via:

1. Experience
	•	match outcomes
	•	fantasy points

2. Reflection
	•	structured reasoning about success/failure

3. Memory
	•	persistent knowledge accumulation

👉 This is cognitive learning, not parametric learning

⸻

9. Simulation Environment (Training Phase)

To bootstrap intelligence, we simulate past seasons.

Why Simulation?
	•	Safe environment for experimentation
	•	Reproducible outcomes
	•	Allows multiple strategy trials

⸻

Simulation Setup
	•	Replay past IPL seasons match-by-match
	•	At each step:
	•	agent selects team
	•	environment returns fantasy points
	•	agent reflects and updates memory

⸻

Multi-Season Training
	•	Run across 2–3 past seasons
	•	Accumulate knowledge across runs
	•	Build strategy consistency

⸻

10. Strategy Evolution (Karpathy-Style Auto Research)

We incorporate self-experimentation loops.

Process:
	1.	Define strategy variants:
	•	aggressive
	•	safe
	•	balanced
	2.	Run simulations under each strategy
	3.	Compare outcomes
	4.	Extract insights:
	•	which strategy works when
	•	how to adapt dynamically

⸻

Human-in-the-Loop (Important)

You can:
	•	propose strategies
	•	nudge agent behavior
	•	guide exploration

👉 This creates a hybrid research loop
(agent + human intuition)

⸻

11. Hypothesis-Driven Learning

The agent is encouraged to:

Before match:
	•	form hypotheses

After match:
	•	validate them

Example:
	•	“Top-order batters will dominate”
	•	Validate via results

👉 This mimics scientific reasoning

⸻

12. Knowledge Compression

To prevent memory bloat:

Periodically:
	•	summarize learnings
	•	condense strategies into key rules

Example:
	•	“Avoid high-risk players early season”
	•	“Captaincy should favor consistency”

⸻

13. Deployment Phase (Live Environment)

After simulation training:

Phase 1 — Shadow Mode
	•	Agent suggests teams
	•	No real execution
	•	Compare against baseline

⸻

Phase 2 — Active Mode
	•	Agent provides decisions:
	•	transfers
	•	team
	•	captain/VC
	•	User executes in fantasy app

⸻

Continuous Learning

Even in live mode:
	•	agent continues reflection
	•	updates strategies
	•	evolves behavior

⸻

14. Role of External Signals (RSS / News)

Initially limited to:
	•	player availability
	•	injuries
	•	playing status

Later extensions:
	•	richer contextual signals
	•	qualitative insights

👉 Keeps system grounded while allowing future expansion

⸻

15. Why This Approach?

Hermes Agent
	•	avoids rebuilding agent infrastructure
	•	provides memory + reasoning loop out of the box

⸻

Simulation First
	•	allows safe experimentation
	•	enables strategy discovery

⸻

Memory-Based Learning
	•	mimics human learning
	•	enables long-term adaptation

⸻

Structured Reflection
	•	forces explicit reasoning
	•	improves decision quality

⸻

Optimization Layer
	•	guarantees valid outputs
	•	separates reasoning from constraints

⸻

16. What Makes Agent XI Unique
	•	Not just a solver → a thinking system
	•	Not static → evolves over time
	•	Not rule-based → experience-driven
	•	Not trained → self-improving via memory

⸻

17. Final Definition

Agent XI is an autonomous decision-making agent that learns to operate in a constrained, uncertain environment by continuously forming beliefs, testing strategies, and refining its behavior through experience and reflection.

⸻
