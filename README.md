# Communications Strategy Tool for Mission-Driven Organizations

## Process Overview

```
                    Layer 0
              ┌─────────────────┐
              │  Org Context &  │
              │     Intake      │
              └────────┬────────┘
                       │
                       ▼
                    Layer 1
              ┌─────────────────┐
              │  Social Media   │
              │     Audit       │
              └────────┬────────┘
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
         Layer 2    Layer 2b   Layer 2c
       ┌─────────┐┌─────────┐┌─────────┐
       │Benchmark-││  Brand  ││Strategy │
       │  ing     ││  Audit  ││& Plan   │
       └─────┬───┘└────┬────┘└────┬────┘
             │         │          │
             └─────────┼──────────┘
                       ▼
              ┌─────────────────┐
              │  Final Output:  │
              │ Strategy + Brand│
              │ Recommendations │
              └─────────────────┘
```

## Vision

An AI-assisted tool that develops **communications strategy for NGOs, mission-driven organizations, and public-interest initiatives**. The system moves from **understanding** an organization's current communications landscape, through **analysis and benchmarking**, to **strategic planning** — producing actionable quarterly communication plans tailored to the organization's mission, resources, and constraints.

The tool is oriented toward **external communications** — how the organization presents itself and engages audiences across public channels. The scope is strategy development; actual content production and execution would be handled separately.

## Layers

The system is structured in layers. Layers 0 and 1 are sequential. After Layer 1, three processes run in parallel: benchmarking (Layer 2), brand audit (Layer 2b), and strategy development (Layer 2c). All three feed into the final output.

### Layer 0: Organization Context & Intake

Before any analysis, the system gathers key contextual information about the organization through a short set of intake questions. This includes:

* organization mission and focus areas
* size and staffing (especially communications capacity)
* budget available for marketing and communications
* current platforms and channels in use
* key audiences and stakeholders
* any existing communications strategy or goals

This context shapes everything that follows — the audit interprets data in light of the organization's actual resources, and the strategy is grounded in what is realistically achievable.

### Layer 1: Social Media Audit

The system ingests historical content and metrics across platforms (e.g., website, YouTube, Substack, X/Twitter, Facebook, LinkedIn, Bluesky) and produces a **structured analysis of activity, engagement, and strategic patterns over time**. It identifies:

* posting history and thematic patterns
* engagement performance
* growth trajectories
* the implicit strategy reflected in the content

The tool interprets this data through a **non-profit communications lens**, producing:

* clear graphics and engagement timelines
* thematic summaries
* a narrative interpretation of what the organization has actually been doing

The goal is to answer: *What have we actually been doing on social media, and how well has it worked?*

### Layer 2: Benchmarking Against Peer Organizations

The system identifies comparable actors such as:

* NGOs
* research collectives
* intellectual networks
* mission-driven media projects

Selection criteria include:

* thematic domain
* audience scale
* budget level
* funding model

The tool performs the same audit on these peers and generates **comparative insights** about:

* engagement performance
* growth rates
* posting strategies
* platform focus

This provides context for interpreting the organization's own performance and answers: *How does our performance compare to peers with similar constraints? What strategic patterns or mistakes emerge from the data?*

### Layer 2b: Brand Audit & Distillation

Using the content gathered in Layer 1, the system distils the organization's **existing brand** as expressed across its communications. This includes:

* **Narrative** — the core story the organization tells about itself, its mission, and its theory of change
* **Tone of voice** — formal vs informal, academic vs accessible, urgent vs reflective, etc.
* **Stylistic sense** — visual and verbal patterns, recurring language, framing choices

The brand audit also includes an **optional critique**, which may surface two kinds of findings:

1. **Inconsistency** — the brand is not coherent across platforms or over time. The audit distils the best approximation of the brand but flags where messaging, tone, or framing diverges, with specific examples. This is often the most valuable finding for organizations whose communications have been managed by rotating staff or volunteers.

2. **Brand recommendations** — suggestions for what the brand *should* be, including proposed narrative, tone, and style, or a set of options to choose from. This is the beginning of a brand development process, not a finished brand guide, but it gives the organization a concrete starting point.

This layer runs in parallel with benchmarking and strategy development, since it draws on the same Layer 1 content but addresses a distinct question: *Who are we, as expressed through our communications — and is that coherent?*

### Layer 2c: Strategy & Communications Planning

Given the audit findings, benchmarking insights, and organizational context (from Layer 0), the system produces a **communications strategy and quarterly action plan**. This is not a full strategy document — it is a synthesis of what the data suggests the organization should focus on.

The strategy layer includes:

* **Quarterly focus areas** — what communications should emphasize in each quarter (3, 6, 9 months out)
* **Campaign direction** — the general shape of a communications campaign, including themes and messaging priorities
* **Distal events and opportunities** — external events, cycles, or moments the organization should plan around
* **Content recommendations** — what kinds of content to produce (newsletters, reports, social posts, video) given what has worked and what peers are doing
* **Budget-informed advice** — recommendations scaled to the organization's actual communications budget and capacity
* **Learnings and shifts** — based on years of accumulated activity and content, what patterns suggest the organization should do differently

The output is **strategic and high-level** — it nudges direction (e.g., "in Q1, focus on X") rather than producing finished content. Actual content production and execution is out of scope for this tool and would be handled by a separate system.

## Prototype (Minimum Viable Version)

The first prototype focuses on **Layer 1: simple automated auditing and visualization**.

### Platforms (initial priority)

* YouTube
* Substack
* Bluesky
* X / Twitter (optional)
* Facebook (optional)

### Output

For each platform, produce **2–3 core visualizations**, such as:

* audience growth timeline
* engagement rate over time
* posting frequency over time

In addition, generate:

* a concise narrative summary of activity
* a snapshot of current status (followers, engagement, content volume)

The prototype goal is simply to answer:

> What has been happening across my platforms over the last five years?

## Open Questions

1. **Data access**

   * Are there existing analytics platforms (e.g., Hootsuite, SocialBlade, TubeBuddy, Substack analytics exports) with APIs that provide this data?
   * Leveraging such APIs may reduce the need for scraping.

2. **Platform access constraints**

   * Which platforms provide historical analytics via API?
   * Some platforms restrict historical data access.

3. **Benchmark identification**

   * How should peer organizations be selected?
   * Manual list vs automated similarity detection.

4. **Data horizon**

   * Can reliable data be obtained for the full **five-year period**, or will limits exist depending on platform APIs?

5. **Data ingestion approach**

   * Should the system rely on:

     * direct API connections
     * manual exports
     * third-party analytics services?

6. **Intake design**

   * What is the minimum set of intake questions needed to meaningfully shape the audit and strategy?
   * Should intake be conversational (interactive Q&A) or form-based?

7. **Brand audit depth**

   * How much of brand distillation can be automated from content analysis vs requiring human input?
   * Should brand recommendations be presented as a single proposal or multiple options?

8. **Strategy scope**

   * How specific should quarterly plans be? High-level themes only, or down to suggested post cadences and content types?
   * How should the tool handle organizations that lack a clear existing strategy to build on?
