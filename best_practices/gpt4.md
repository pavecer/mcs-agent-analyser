# GPT-4 — System Instruction Best Practices

GPT-4 is a legacy high-capability profile still present in some environments. Use explicit persona, strict scope, and grounding requirements for stable enterprise behavior.

---

## 1. Role, Purpose, Constraints

Always include:

- Role statement
- Primary purpose
- Out-of-scope behavior

```
You are PolicyBot for [Org Name].
Your purpose is to answer policy questions using approved internal documents.
If a question is outside policy scope, state that and direct users to the right team.
```

---

## 2. Grounding Requirement

```
Answer only from available internal sources.
Do not invent policy details.
Cite the source document title when possible.
```

---

## 3. Safety and Privacy

- Never expose secrets or internal-only identifiers
- Redact unnecessary personal data
- Refuse harmful or prohibited requests per policy

---

## 4. Length Guidance

- Typical: 300 to 2,500 chars
- Upper guidance: 8,000 chars

---

## 5. Common Pitfalls

- Overly broad mission without boundaries
- No explicit uncertainty behavior
- Contradictory tone/format rules
