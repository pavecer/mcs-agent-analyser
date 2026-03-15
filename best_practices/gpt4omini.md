# GPT-4o Mini — System Instruction Best Practices

GPT-4o Mini is a legacy compact model profile. It performs best with concise instructions, a narrow scope, and explicit output constraints.

---

## 1. Keep It Short and Direct

- Target 150 to 1,000 chars
- Avoid long multi-section policy prose
- Prefer flat bullet constraints over deep nesting

---

## 2. Single Responsibility Prompt

```
You are ReturnsBot for [Org Name].
You only help with product returns, refund status, and exchange rules.
```

Do not combine unrelated domains in one prompt.

---

## 3. Grounding and Refusal Behavior

```
Use only provided source data.
If answer is not in provided sources, respond with: "I don't have that information in available sources."
```

---

## 4. Deterministic Response Rules

- Always use the same response structure
- Always ask one clarifying question if user intent is ambiguous
- Never speculate

---

## 5. Common Pitfalls

- Prompt too verbose for compact model
- Missing fallback rule
- Ambiguous language without strict constraints
