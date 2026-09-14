# Moneyfesting project context

Snapshot inspected 2026-09-12. Paths are relative to the Moneyfesting checkout and can move. Current source and repository instructions take precedence over these observations or old plans.

## Discovery map

| Surface | Starting points | Why it affects translation |
|---|---|---|
| Shared app/extension UI | `Manifesting/Foundation/Localization/Localizable.xcstrings`, feature `*Strings.swift` / `*LocalizedStrings.swift` | Literal keys, context, placeholders, plurals, computed accessors |
| Language selection | `Manifesting/Foundation/Localization/AppLanguage.swift`, `AppLanguageStore.swift` | Current support is `en`, `ro`; lookup, formatting, persisted overrides and content language differ |
| Currency | `Manifesting/Foundation/Localization/CurrencyOption.swift`, `AppCurrency.swift`, `CurrencyPickerStrings.swift` | `CurrencyCatalog.options` is a currency/region inventory, not target languages; display currency is a user choice |
| Onboarding | `Manifesting/Features/Onboarding/Business`, especially coordinator/routes, Welcome, PersonalGoal and rate/income setup | Read actual route order and state; headings, explanations and CTA must agree |
| Tasks and focus | `Manifesting/Features/Plan`, `Manifesting/Features/FocusTask`, `Manifesting/Features/Moneyfesting` | Verify timer/session/task meanings at call sites; follow pause, break, stop, completion and failure states |
| Insights and streaks | `Manifesting/Features/Insights`, `Manifesting/Foundation/InsightsSavings`, widget sources | Estimated focus/time value and progress can be mistaken for money earned |
| Subscription | `Manifesting/Features/Paywall` | Preserve trial eligibility, billing period, terms and purchase behavior; inspect the live implementation before asserting a StoreKit integration |
| Quotes and affirmations | `Data/quotes/SCHEMA.md`, `Data/quotes/quotes-v2.json`, `Manifesting/Features/Quotes` | Different content kinds have different provenance, translation and persistence rules |
| Screen Time shields | `Manifesting/Foundation/ShieldSupport/ShieldMessage.swift`, `ShieldMessageCatalog.swift`, `ShieldPresentationCopy.swift`; `Manifesting/ScreenTimeShieldConfigurationExtension` | EN/RO fields and language branches exist outside `.xcstrings`; catalog completeness does not cover these |
| System surfaces | `Manifesting/WidgetsExtension`, Screen Time action/configuration extensions, notifications, app intents | Target membership, runtime locale and space limits differ from the main app |
| Shared/exported copy | `Manifesting/Features/Share`, bundled images and actual store assets if supplied | Quote attribution, image text, share cards and App Store metadata need explicit surface scope |

Search for hardcoded English and `== "ro"`/fallback switches as discovery clues, then classify actual user-facing strings. Exclude internal identifiers, logs, debug-only fixtures, currency codes, and `shouldTranslate: false` content unless their real role warrants a change. Reuse a term across matching meanings; do not assume identical English such as “Done” or “Save” has the same role everywhere.

## Product and engineering invariants

Moneyfesting links purposeful focus, plans/tasks, aspirations and quotes to the estimated value of time. Onboarding/paywall explanations distinguish that value from income. Verify each metric's calculation and the state's actual behavior before choosing language such as saved, earned, lost, invested, or recovered. Preserve aspiration without adding guarantees, guilt, diagnoses, or financial advice.

Inspect `Manifesting/Foundation/WidgetSupport/StreakWidgetCopy.swift` and `FocusRingCopy.swift`: freeze coverage is not completed focus, a five-minute streak threshold differs from a user's daily goal, and a trailing 30-day value differs from today's result. `Manifesting/Foundation/InsightsSavings/InsightsSavingsStrings.swift` separates recorded value, estimates of earlier days and month-end forecasts. Preserve these distinctions across compact labels and accessibility explanations.

Keep separate: app language, device formatting region, chosen time-value currency, and storefront purchase price. Do not select SAR for every Arabic reader or USD for every English reader. If a live StoreKit price is used, preserve its localized display output; do not translate, convert, or hardcode it into prose. Translating purchase copy does not authorize implementing or changing billing.

The current project requires literal catalog keys and computed localized accessors. App copy resolves through `String(localized: LocalizedStringResource(..., locale: AppLanguage.localizationLocale))`. `AppLanguage.effectiveLocale` handles display formatting. Preserve deferred resources for system-owned widget/intent metadata. Do not replace this with manual `.lproj` selection, cached translations, `AppleLanguages` overrides, or a forced relaunch.

Adding target resources does not itself enable a locale. Inspect support allowlists, language-picker names, regional/script resolution, quote-language selection and extension switches. Test region-specific variants rather than assuming an existing base-language implementation supports them. App sources use explicit Xcode project membership; verify both app variants and consuming extensions for any new/moved resource or source file.

Read current `CLAUDE.md` for build schemes and the project-owned simulator. For actual app checks it currently requires `-skipMacroValidation` and `BUILD_ACTIVE_RESOURCES_ONLY=NO`; do not operate unrelated simulators. This skill's own creation or preparation mode requires no app build.

## Content policy

Read `Data/quotes/SCHEMA.md` before touching quote content. At inspection:

- Published attributed quotations remain in their published language. A blanket localization request does not establish a new translated-quotation attribution policy.
- Original affirmations have reviewed EN/RO pairs and stable `pairId`; Romanian affirmations are gender-neutral. New target-language content needs a deliberate schema/curation approach that preserves identity and provenance.
- Scripture uses canonical corpus verification and language-independent `canonicalReference`; preserve the corpus/reference relationship. Do not manufacture an “official” translation or silently substitute a paraphrase.
- Preserve quote IDs, favorites, hidden links, author/source metadata, verification distinctions, and category-specific English fallback. Do not reseed user data to introduce translations.
- User-created quotes/tasks/names remain user content. Translate their surrounding controls; preserve the content unless translation of it was explicitly requested.

If a future user requests a policy change, make that precise before generating the affected attributed/religious material. Continue ordinary UI localization independently.
