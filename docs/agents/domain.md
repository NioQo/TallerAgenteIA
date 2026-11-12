# Domain docs

This project uses a single domain context. Engineering agents working in this repository should follow these rules.

## Before exploring

- Read `GLOSSARY.md` at the repository root when it exists.
- Read relevant decisions in `docs/adr/` when that directory exists.
- If these files do not yet exist, proceed without calling out their absence. Create or update domain documentation when a domain term or decision is actually established.

## Use the glossary vocabulary

Use domain terms as defined in `GLOSSARY.md` in tickets, specifications, code, tests, and proposals. Avoid synonyms that conflict with the glossary. If a needed concept is missing, identify the gap rather than silently inventing terminology.

## Flag decision conflicts

If proposed work conflicts with a recorded ADR, surface the conflict explicitly instead of silently overriding the decision.

## Layout

```text
/
├── GLOSSARY.md
├── docs/
│   ├── adr/
│   └── agents/
└── .scratch/
```
