# Locale decisions

## Briefs

Fill `references/locale-briefs/TEMPLATE.md` for each target; `references/locale-briefs/ro.md` is a complete brief and the model for the next one. The translator and the final adjudicator receive the brief whole; the editor never sees it, because its keys and English would break packet separation (`references/agent-protocol.md` `## Packet separation`): the blind packet carries the target-only term list that `scripts/build_context_packet.py --glossary` builds from `glossary/<locale>.json`, and the coordinator appends the brief's imported-shape markers to the editor prompt as the target-only pattern lines of `## Audience and register`, never the key column. Verify uncertain terminology with primary local sources and the current Apple interface in that language (`## Platform terms` below); do not copy competitor slogans. Keep one source per fact: control forms are rows in `glossary/<locale>.json` (`scripts/term_audit.py` reads them; the brief's table mirrors them and must match), platform terms live in the brief's `## Platform terms` table with a glossary row only for terms `term_audit.py` must police (ro: `screen_time`, whose forbidden form is the English name), tone examples live in `references/examples-ro.md`, budgets in `references/surface-budgets.md`.

## Currency list interpretation

Read `CurrencyCatalog.options` in `Manifesting/Foundation/Localization/CurrencyOption.swift` each run; at snapshot 2026-09-15 (lines 48-84) it holds 32 currencies and 53 region codes, EUR alone 21 and CHF 2. Currencies are audiences, not languages: RON -> ro is safe, SAR -> ar needs a Gulf readability brief, EUR maps to 21 regions. The table is illustrative; re-read the file before quoting it in a handoff.

| Currency (regions) | Candidate languages | Note |
|---|---|---|
| USD (US), GBP (GB), AUD (AU), NZD (NZ), SGD (SG), ZAR (ZA); EUR for IE and MT | `en`, the shipped source | store-metadata variants only when that surface is in scope; do not add every official language of SG or ZA |
| BRL (BR), MXN (MX) | `pt-BR`, `es-MX` | never merged with `pt-PT` or `es-ES` to save effort |
| EUR (AT, BE, BG, HR, CY, EE, FI, FR, DE, GR, IE, IT, LV, LT, LU, MT, NL, PT, SK, SI, ES) | `de`, `fr`, `it`, `es-ES`, `pt-PT`, `nl`, `el`, `fi`, `bg`, `hr`, `et`, `lv`, `lt`, `sk`, `sl` | BE, LU, CY, MT and IE need an audience choice before a language is named |
| RON, PLN, DKK, HUF, SEK, NOK, ISK | `ro`, `pl`, `da`, `hu`, `sv`, `nb`, `is` | |
| CHF (CH, LI) | `de-CH`, `fr-CH` or `it-CH` | audience choice; no regional variant is selectable in-app (`AppLanguage.supportedLanguageCodes`, `Manifesting/Foundation/Localization/AppLanguage.swift:6`) |
| ILS (IL) | `he` | currency-implied and a standing preference |
| SAR, AED, EGP, MAD, KWD, QAR, BHD, OMR | `ar` | shared written Arabic with audience-specific review; a currency implies neither a dialect nor market fit |
| CNY (CN), TWD (TW), HKD (HK) | `zh-Hans`; `zh-Hant` with a Taiwan brief; `zh-Hant` with Hong Kong wording | verify script and region resolution in the bundle first |
| JPY, KRW, TRY | `ja`, `ko`, `tr` | |

This is a candidate mapping for clarification, not an authorized target set or proof of demand. Name derived candidates as derived when they differ from the owner's list; honor the current task's targets; do not expand regional variants on your own. App resource tags, formatting locales and App Store Connect language labels are three different lists: check `references/store-metadata.md` when metadata is requested, and treat the absence of a metadata locale as no bar to an in-app localization.

## Standing owner preferences (recorded 2026-09-12)

Hebrew `he`, Italian `it`, Norwegian Bokmål `nb`, Russian `ru`. Currency evidence now covers `he` (ILS), `it` (EUR/IT) and `nb` (NOK); `ru` has no currency evidence and stays a preference. A preference is a candidate to raise when establishing the assignment, not an authorization to translate.

## Voice choices that need locale review

- **English:** US product register; contractions fine; no "Please" or "In order to" scaffolding (14 en keys carry "Please" at snapshot 2026-09-15); numerals for counts; Apple US platform terms (Screen Time, Focus, Home Screen, Face ID). One capitalization convention, pinned from the catalog majority: sentence case for buttons, body and screen titles (314 of 413 two-to-four-word en strings, 61 of 89 button strings, 67 of 111 title strings), Title Case only where a string mirrors an Apple label; report the current mix as one finding rather than legislating line by line. Keep the fixed "Not money earned" disclaimers verbatim. `en` is a locale for audit mode (SKILL.md `## Establish the assignment`).
- **Gender in UI copy:** prefer verb forms with invariable participles, imperatives or achievement nouns over predicate adjectives and role nouns aimed at the reader; never slash forms or doubled endings. The stored profile gender (`Manifesting/Features/User/Domain/Entities/Gender.swift`) is not a copy input without a product decision. Romance locales: second-person imperatives and present tense are neutral. Hebrew: unpointed second-person past, infinitive CTAs, nominal headlines; avoid present-tense participles. Arabic: masdar CTAs, unvowelled past, nominal headlines. Where no neutral form exists, record the locale's accepted default in the brief with the keys it touches.
- **Arabic:** contemporary, friendly Modern Standard Arabic, Saudi-focused with a Gulf readability pass; no bureaucratic syntax, no unrequested dialect slang. A Gulf review does not establish Egyptian or Moroccan suitability. Check address and gender, finance and manifestation connotations, natural CTA verbs, digit preference and mixed Latin/Arabic display in context.
- **Hebrew:** contemporary Israeli Hebrew; one consistent, natural gender strategy without inventing the reader's gender or stacking alternatives everywhere. Review controls and affirmations separately. Test RTL with the Latin brand, currency, numerals and punctuation.
- **Romanian:** keep the informal `tu`, comma-below ș/ț and the gender-neutral authored-affirmation policy (app `CLAUDE.md:43`); UI copy is gender-neutral too. Verify financial terms against the time-value concept instead of assuming literal equivalents fit. Full brief in `references/locale-briefs/ro.md`.
- **Portuguese/Spanish variants:** pin one register and local vocabulary per variant; shared meaning does not make UI copy interchangeable. Keep variant-specific glossary entries.
- **Japanese/Korean:** agree a politeness level and a concise UI style; inspect line breaking and font fallback. Prefer a familiar local term to an automatic phonetic loanword.
- **Chinese:** distinguish script from regional vocabulary; Traditional Chinese for Taiwan needs Taiwan wording, not converted characters.
- **Other European locales:** decide address and register locally; allow natural inflection and compounds. Do not assume a universal text-expansion percentage; each brief sets its own length trigger.

## Platform terms

Harvest once per locale and record rows as English | Apple target term | where seen | date in the brief's Platform terms section, the one home for platform terms; add a `glossary/<locale>.json` term row only where `term_audit.py` must police a form (ro: `screen_time`).

Set the project simulator's device language, because the in-app override (`AppLanguage.overrideCode`, `Manifesting/Foundation/Localization/AppLanguage.swift:9-22`) and `-welcomePreviewLanguage` (same file, lines 79-91) change only app strings and leave Apple's own screens in English. Use Settings > General > Language & Region on the simulator, or the CLI:

```sh
SIM=79405175-1BEC-48D3-A8DC-F8358E356C6C
xcrun simctl spawn "$SIM" defaults write .GlobalPreferences AppleLanguages -array ro
xcrun simctl spawn "$SIM" defaults write .GlobalPreferences AppleLocale ro_RO
xcrun simctl shutdown "$SIM" && xcrun simctl boot "$SIM"
```

This is simulator configuration, not the `AppleLanguages` app-implementation override that app `CLAUDE.md:42` forbids; reboot only this simulator (`CLAUDE.md:7-8`) and restore its language when done.

Read, in the target language: Settings > Screen Time and the Screen Time access alert; the Focus settings, noting the term because a locale may use the app's own focus word for the system mode; the notification permission alert; the Photos add-only alert, whose usage string is an unlocalized build setting (`INFOPLIST_KEY_NSPhotoLibraryAddUsageDescription`, `Manifesting.xcodeproj/project.pbxproj:9488`) so only Apple's chrome localizes and the English string is a finding; the Health permission sheet (`Manifesting/Foundation/Localization/InfoPlist.xcstrings`, `NSHealthShareUsageDescription` and `NSHealthUpdateUsageDescription`); Home Screen Edit, Add Widget, Done and Customise, since the `onboarding.widgets.howTo.*` mirrors resolve against the device language at runtime (their catalog comments say so) and the catalog value must equal Apple's label; App Store > Account > Subscriptions and Settings > Apple Account > Subscriptions for trial, renewal and restore wording (the StoreKit purchase sheet has no restore control; `paywall.button.restore` is app-owned).

Rule: verbatim for the app's mock alerts (`onboarding.screenTimePermission.alertTitle`, `alertMessage`, `onboarding.notificationPermission.alertTitle`) and the howTo mirror labels; default for matching controls; deviate only with a recorded reason. Seed ro from I18N_PLAN section 7 and the catalog; mark "Restaurează" unverified until the Subscriptions sheet is read. From the same session write three brief lines: preferred CTA mood and person, formality, fragment tolerance.

## Plurals

Consult current Unicode CLDR plus the actual Xcode and runtime behavior for the target; the resource locale selects the plural rules (app `CLAUDE.md:42`). Exercise representative values for every reachable category, including zero, dual and fractions where relevant, and the boundary values the locale's rule makes surprising (Romanian: 101 is `few`, 120 is `other`). Arabic has six cardinal categories; do not copy that set to Hebrew or assume every language needs English's pair. Preserve agreement around numbers and interpolated names, and check that every plural category carries the same claim as the source.

## RTL

Test semantic leading/trailing layout, intentional image direction, mixed-script numbers, prices and timers, punctuation and VoiceOver order. Do not reverse strings or mirror every icon. Do not insert invisible directional controls indiscriminately; inspect the specific rendering issue and coordinate a tested implementation fix. `Moneyfesting` stays in Latin script inside RTL text.
