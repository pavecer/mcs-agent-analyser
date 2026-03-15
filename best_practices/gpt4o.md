# GPT-4o — System Instruction Best Practices

GPT-4o is a legacy, broadly capable multimodal model still used in some Copilot Studio tenants. It benefits from clear scope constraints, grounding requirements, and deterministic response format rules.

---

## 1. Define Persona and Mission First

Start with one explicit role sentence and one mission sentence.

```
You are ServiceDeskBot for [Org Name].
Your mission is to help employees with approved internal IT and access requests.
```

---

## 2. Add Hard Scope Boundaries

Use absolute language:

- Always answer only in approved domain.
- Never provide legal, medical, or financial advice.
- If out of scope, return a standard fallback sentence.

---

## 3. Grounding Rules for Enterprise Use

```
Answer only from provided grounding data or configured knowledge sources.
Do not use external web knowledge unless web browsing is explicitly enabled.
If the answer is missing in sources, say you cannot find it.
```

---

## 4. Keep Output Shape Stable

Define output template for consistency:

```
Summary: <1-2 sentences>
Steps:
1) ...
2) ...
Source: <document or system>
```

---

## 5. Recommended Length

- Typical: 300 to 2,000 chars
- Upper guidance: 8,000 chars

If instructions become too long, split logic into topic-specific prompts.

---

## 6. Common Pitfalls

- Vague language like "usually" or "sometimes"
- Contradictory constraints
- Missing fallback behavior
- No source/grounding requirements
