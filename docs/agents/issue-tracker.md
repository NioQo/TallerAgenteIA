# Issue tracker: Local Markdown

Specifications and tickets for this project live as Markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The feature specification is `.scratch/<feature-slug>/spec.md`.
- Implementation tickets are individual files under `.scratch/<feature-slug>/issues/`, numbered from `01` (for example, `01-<slug>.md`).
- Keep issue comments and conversation history in the relevant ticket file under a `## Comments` heading.

## Publishing and fetching work

- When asked to publish a specification or ticket, create the appropriate Markdown file under `.scratch/<feature-slug>/`.
- When asked to fetch a ticket, read the path or ticket number supplied by the user. If only a number is supplied, locate it under `.scratch/`.
