# Layer 0: Organization Intake — Specification

## Purpose

Layer 0 is the entry point for the communications strategy tool. Before any audit or analysis can happen, we need to know *who* we're working with. This layer gathers foundational information about the organization through an interactive session and produces a structured brief (`brief.md`) that all subsequent layers consume.

## Goals

1. **Identify the organization** — name, website, mission
2. **Discover online presence** — automatically find social media handles from the website, confirm with user
3. **Gather context** — size, comms capacity, audiences, existing strategy
4. **Produce a brief** — a single `brief.md` file that serves as the input for Layer 1+

## Interactive Flow

```
Start
  → Ask: Organization name
  → Ask: Website URL
  → Auto-discover social media handles from website
     (scan for links to YouTube, Substack, Bluesky, X/Twitter, Facebook, LinkedIn, etc.)
  → Present discovered handles to user for confirmation/correction
  → Ask: Brief description of the organization (1-3 sentences)
  → Ask: Mission / theory of change
  → Ask: Key audiences
  → Ask: Team size and comms capacity
  → Ask: Approximate comms/marketing budget
  → Ask: Any existing comms strategy or goals?
  → Ask: Anything else relevant?
  → Generate brief.md
```

## Auto-Discovery of Social Media Handles

Given a website URL, the agent should:

1. Fetch the homepage and any obvious pages (about, contact, footer)
2. Extract links matching known social media URL patterns:
   - `youtube.com/c/` or `youtube.com/@` or `youtube.com/channel/`
   - `*.substack.com` or links to substack
   - `bsky.app/profile/`
   - `twitter.com/` or `x.com/`
   - `facebook.com/`
   - `linkedin.com/company/` or `linkedin.com/in/`
   - `instagram.com/`
3. Present the discovered handles and ask the user to confirm, correct, or add missing ones

## Output: `brief.md`

The output file should be structured as:

```markdown
# Organization Brief

## Organization
- **Name:** ...
- **Website:** ...
- **Description:** ...

## Mission & Focus
...

## Online Presence
| Platform | Handle/URL | Status |
|----------|-----------|--------|
| Website | https://... | Active |
| YouTube | @handle | Active |
| Substack | name.substack.com | Active |
| ... | ... | ... |

## Audiences
...

## Team & Capacity
- **Team size:** ...
- **Comms staff/capacity:** ...
- **Approximate comms budget:** ...

## Current Strategy
...

## Additional Context
...
```

## Design Decisions

- **Interactive, not form-based**: The intake is conversational. The agent asks questions one at a time (or in small groups) and can ask follow-ups based on answers.
- **Auto-discovery first**: Rather than asking the user to list all their social media, we try to find them automatically and then confirm. This reduces friction and catches accounts the user might forget to mention.
- **Minimal required fields**: Only name and website are strictly required. Everything else is optional but encouraged — the more context, the better the downstream analysis.
- **Output is a file**: The brief is written to `brief.md` in the project directory, making it available to all subsequent layers as a structured input.
