# Locale decisions

Create a brief for each target: resource tag, audience/region, written register, pronouns/politeness, gender strategy, preferred product/UI terms, numeral/punctuation conventions, and any regional exclusions. Use contemporary local product language; official locale guides are references, not a mandate to copy Microsoft's brand voice. Verify uncertain terminology with primary local sources and current Apple interfaces; do not copy competitor slogans.

## Currency list interpretation

Inspect `CurrencyCatalog.options` in `Manifesting/Foundation/Localization/CurrencyOption.swift` each run. The inspected catalog contained 25 currencies and 34 region codes. These suggest audiences, not a one-to-one language list. The user explicitly added Hebrew and previously mentioned Italian, Norwegian and Russian; currency omissions do not cancel those preferences.

| Observed currency/regions | Candidate language interpretation |
|---|---|
| USD, GBP, AUD, NZD; EUR/IE | Shared international English `en`; separate store metadata variants only when in scope |
| BRL / MXN | `pt-BR` / `es-MX` |
| EUR: ES, PT, NL, BE, DE, FR, AT, FI, GR | `es-ES`, `pt-PT`, `nl`, `de`, `fr`, `fi`, `el`; Belgium/other multilingual markets need an explicit audience choice |
| RON, PLN, DKK, HUF, SEK, ISK | `ro`, `pl`, `da`, `hu`, `sv`, `is` |
| SAR, AED, EGP, MAD, KWD | Shared written Arabic `ar` is a candidate, with audience-specific review; currency does not imply dialect or universal market fit |
| CNY / TWD | `zh-Hans` / `zh-Hant` with a Taiwan brief for the latter; verify supported resource tags and script/region fallback |
| JPY, KRW, TRY | `ja`, `ko`, `tr` |
| ZAR / SGD | English can cover the existing international baseline; do not silently add every official language |
| Explicit user additions/preferences | Hebrew `he`; retain Italian `it`, Norwegian Bokmål `nb` and Russian `ru` as candidates even though IT/NOK/RUB are absent |

This is a candidate mapping for clarification, not a frozen authorized target set or proof of profitability. French, Greek, or Chinese candidates derived from currencies should be identified as such when they differ from a user's explicit list. Honor the current task's targets. Do not expand regional variants automatically or merge Spain/Mexico and Brazil/Portugal to save effort.

App resource tags, formatting locales and App Store Connect language labels are distinct. Verify current Apple metadata support when that surface is requested; absence of a metadata locale does not by itself prohibit an in-app localization. Do not gate Arabic language design on Apple TV availability, GDP, or unverified market claims.

## Voice choices that need locale review

- **Arabic:** default proposal is contemporary, friendly Modern Standard Arabic, Saudi-focused with a Gulf readability pass. Avoid bureaucratic syntax and unrequested local-dialect slang. MSA is a writing choice, not a profit prediction; a Gulf review does not establish Egyptian/Moroccan suitability. Check gender/address, finance/manifestation connotations, natural CTA verbs, digit preferences and mixed Latin/Arabic display in context.
- **Hebrew:** use contemporary Israeli Hebrew; choose a consistent, natural gender strategy without inventing the reader's gender or inserting cumbersome alternatives everywhere. Review actual controls and affirmations separately. Test RTL with Latin brands, currency, numerals and punctuation.
- **Romanian:** retain the project's informal `tu`, comma-below ș/ț, and gender-neutral authored-affirmation policy. Verify financial terms against the time-value concept instead of assuming literal equivalents fit.
- **Portuguese/Spanish variants:** pin one register and local vocabulary per variant; shared meaning does not imply interchangeable UI copy. Keep variant-specific glossary entries.
- **Japanese/Korean:** agree a consistent politeness level and concise UI style; inspect line breaking and font fallback. Do not use phonetic loanwords automatically when a familiar local term is clearer.
- **Chinese:** distinguish script from regional vocabulary; Traditional Chinese intended for Taiwan needs Taiwan wording, not merely converted characters.
- **Other European locales:** decide address/register locally; allow natural inflection and compounds. Do not force English capitalization, clipped English sentence fragments, or a universal text-expansion percentage.

For plurals, consult current Unicode CLDR plus the actual Xcode/runtime behavior for the target. Exercise representative values for every reachable category, including zero/dual/fractions where relevant. Arabic has six cardinal categories; do not copy that category set to Hebrew or assume every language needs English's pair. Preserve grammatical agreement around numbers and interpolated names.

For RTL, test semantic leading/trailing layout, intentional image direction, mixed script numbers/prices/timers, punctuation and VoiceOver order. Do not reverse strings or mirror every icon. Do not insert invisible directional controls indiscriminately; inspect the specific rendering issue and coordinate a tested implementation fix.
