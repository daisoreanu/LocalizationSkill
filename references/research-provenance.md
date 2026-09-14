# Research provenance

Reviewed 2026-09-12. These instructions are an original synthesis; no third-party runtime or bulk skill text is bundled. Community workflows provide useful mechanisms, not proof of translation quality. Verify sources again when changing their adopted behavior.

| Inspected source | Adopted mechanism | Deliberately omitted |
|---|---|---|
| [Anthropic skill creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) | Focused skill plus references; realistic evaluation, independent comparison and iteration | Claude-specific CLI/model assumptions; automatic approval questions |
| [Localize Anything](https://github.com/xueyang-dev/localize-anything/blob/main/skills/localize-anything/SKILL.md), [context/memory](https://github.com/xueyang-dev/localize-anything/blob/main/skills/localize-anything/references/memory-and-context.md) | Surface inventory, concept glossary, separate structural/linguistic/visual evidence | Custom orchestration CLI and mandatory human-confirmation machinery |
| [Fidelity Translator](https://github.com/Tasdax123/claude-fidelity-translator/blob/main/plugins/fidelity-translator/skills/fidelity-translator/SKILL.md) | Translator/critic/revision/backtranslation pattern and pinned terminology | English-similarity acceptance threshold; its nonmarketing scope and provider settings |
| [Translate Book](https://github.com/deusyu/translate-book/blob/main/SKILL.md) | Neighbor context, shared glossary, selective review invalidation | Book conversion and document/entity machinery |
| [neo.ai Translator](https://github.com/theneoai/awesome-skills/blob/main/skills/persona/creative/translator/SKILL.md) | Brand/market brief, meaningful creative alternatives and local idiom | Persona boilerplate and self-awarded verification labels |

The community repositories present MIT licensing/attribution. Follow each repository's actual license and preserve notices if future revisions copy substantial material. This package borrows workflow ideas and links to the originals.

## Primary references for maintenance

- [Apple localization](https://developer.apple.com/localization/) and [Code-along: Explore localization with Xcode](https://developer.apple.com/videos/play/wwdc2025/225/): catalog workflow, translator context and platform surfaces. Keep repository conventions where they intentionally differ from generic examples.
- [Apple StoreKit displayPrice](https://developer.apple.com/documentation/storekit/product/displayprice): preserve runtime-localized purchase prices when the app uses them.
- [Unicode CLDR plural rules](https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html): target-specific plural behavior; verify against the shipping runtime.
- [Microsoft locale guides](https://learn.microsoft.com/en-us/globalization/reference/microsoft-style-guides): language/region conventions, including Arabic, Hebrew and regional Portuguese/Spanish. Use alongside Moneyfesting's own voice.
- [MQM error typology](https://www.themqm.org/mqm-pillars/typology/): separate accuracy, linguistic, style, audience/locale and presentation findings. The acceptance criteria here are Moneyfesting-specific, not MQM certification.
- [Smartling transcreation](https://help.smartling.com/hc/en-us/articles/4641758074523-What-is-Transcreation): intent/tone adaptation and creative alternatives. This does not demonstrate conversion lift for this app.
- [Experts, Errors, and Context](https://aclanthology.org/2021.tacl-1.87/): contextual professional evaluation research; it does not establish that AI personas equal native professional reviewers.
- [Rethinking Round-Trip Translation for Machine Translation Evaluation](https://aclanthology.org/2023.findings-acl.22/): round-trip evaluation research, not a certificate of native UI naturalness.

The fresh target-only agents, explicit leakage prevention, bounded revision loop, version-linked evidence and highest-capability adjudicator are proposed workflow controls. Test their behavior and disclose unavailable stages; do not describe the arrangement as scientifically proven or native-human validation.
