# Voice card

Snapshot 2026-09-15, catalog commit `c8a49dd`. Tags: [test] a pinned test (executable truth), [comment] the catalog comment on the named key, [archive] an archived plan (a claim to verify before relying on it), [inferred] read off the shipped copy, not policy. Route: the translator and adjudicator get the whole card; blind reviewers get only the target-language banned words from the locale brief's `## Money frame` and the persuasion categories from `## Persuasion limits` named as categories (countdown or dated deadline, social proof, guarantee, shaming, medical claim, privacy promise, hype noun), never as English phrases, because the English lines here would break packet separation.

## Voice

- Second person, present tense, one idea per line, dry warmth. Everyday words a local user understands on first read, since the copy sits next to money and a timer, not in an ad. [inferred]
- No superlatives, no unsourced statistics, no ratings, reviews or user counts: `PaywallSocialProof.ratingSummary` is `nil` and `testimonials` is `[]` by design. [test: `ManifestingTests/Paywall/PaywallCopyTests.swift:9-10`]
- The notification screen quotes no statistic ("more likely", "șanse mai mari") and promises no Live Activity. [test: `ManifestingTests/Onboarding/OnboardingCopyTests.swift:12-30`]
- The "with Moneyfesting" sentence stays a hedge ("could", ro "pot"), never "You'll improve". [test: `ManifestingTests/Onboarding/OnboardingCopyTests.swift:38-49`]
- Keep emoji present in the source; add none. [archive: `Docs/Archive/I18N_PLAN.md` section 7]
- Exclamation marks are banned only where a test pins it (the widgets how-to screen). The three `en` lines carrying "!" (`plan.dailyPlan.futureEmptyMessage`, `plan.dailyPlan.timelinePotentialSuffix`, `streakFreeze.info.body`) are flags to record, not a licence to add more. [test: `ManifestingTests/Onboarding/OnboardingWidgetsStepTests.swift:200-215`]
- Sentence case for body text and controls; ALL CAPS section headers and widget rows (`insights.mood.mood` = "MOOD") are a layout convention the locale brief decides. [archive: `Docs/Archive/I18N_PLAN.md` section 7]

## Money frame

Time has a price at the user's own rate; the app never pays, earns, saves or loses money. The legal line (owner, 2026-09-16): no copy, in the UI or in a quote, may state or imply that focusing, blocking apps, planning or using Moneyfesting makes the reader money; the app shows what time is worth and nudges its use. Affirmations are the reader's own voice and may speak of money and abundance ("I attract money easily") as long as they tie no money outcome to the app. Banned as an outcome word in app copy, in every locale: earn, pays you, make money, cash out, wealth, income, guaranteed. A negated disclaimer ("Not money earned.") is the frame itself, not an outcome. [test: `ManifestingTests/Paywall/PaywallCopyTests.swift:80-93` for the hero in en and ro; `ManifestingTests/Onboarding/OnboardingWidgetsStepTests.swift:200-215` for the widgets screen in en and ro, which also bans track, monitor, you missed, midnight and "!"] Each locale brief's `## Money frame` gives the target forms of this section: fixed phrases, banned words with grep stems, the widgets-screen words and the sanctioned words (ro: `references/locale-briefs/ro.md`).

"Earned" is fine for freezes and badges ("One earned freeze", `achievements.badge.*.earned`) [comment: `paywall.benefit.streak.detail`, `achievements.badge.clockedIn.earned`]. Sanctioned: worth, value, price, costs, adds up, estimated [archive: `Docs/Archive/APP_UPDATE_PLANS/04_app_store_marketing.md:44`, citing a `WelcomeViewModel` rulebook no longer in code]. "A freeze covers one day, not two" is never strengthened [comment: `paywall.benefit.streak.detail`]. The wage footer claims no national average [test: `ManifestingTests/Onboarding/OnboardingCopyTests.swift:72-82`].

Fixed phrases, one target form each; `glossary/<tag>.json` `time_value_disclaimer` enforces the first row:

| Source | Keys |
|---|---|
| Not money earned. | `achievements.badge.*.earned` (7), `achievements.category.wages.description`, `widgets.cash.description`, `widgets.focusRing.a11y.money`, `widgets.monthlyTimeValue.description` |
| Estimated value of time, not money earned. | `insights.savings.disclaimer` |
| Time value, not earnings. | `insights.savings.compactDisclaimer` |
| It is not a source of income. | `onboarding.hourlyWage.disclaimer` |
| Not money lost. | `onboarding.withoutMoneyfesting.fourthLine` |

## Surface rules

- Welcome headlines: two lines joined by `\n` [test: `ManifestingTests/Onboarding/WelcomeCarouselTests.swift:92-97`], six words or fewer [`Docs/Research/ONBOARDING_CAROUSEL_RESEARCH.md:33`, research, not a test].
- Streak widget lines report outcomes; they never praise effort, never mourn, never say "open the app", because a freeze is spent on the user's behalf and asking them to open the app to protect the day they did not open it is incoherent. [archive: `Docs/Archive/WIDGETS_PLAN.md` section 9.2; `Docs/Archive/STREAK_FREEZE_PLAN.md:29-31`] `Manifesting/Foundation/WidgetSupport/FocusRing/FocusRingCopy.swift:127` legitimately says "Open the app to set one": that widget has no goal yet.
- Shields: calm, one small next step, no app name, no claim to detect failure or mood, no exclamation. [inferred from `Manifesting/Foundation/ShieldSupport/ShieldMessageCatalog.swift` and `Docs/Research/SCREEN_SHIELD_RESEARCH/RESEARCH_SYNTHESIS.md:63`; not policy]
- Notifications: the title is the brand (`notifications.*.title` = "Moneyfesting"), one plain body, no trial, billing date or deadline the scheduler does not own. [test: `ManifestingTests/Onboarding/OnboardingCopyTests.swift:99-116`]
- Widgets how-to: the pick step never names the widget ("Focus Streak", ro "serie de focus"); the steps name the installed app. [test: `ManifestingTests/Onboarding/OnboardingWidgetsStepTests.swift:170-192`]

## Persuasion limits (all locales)

Allowed: loss framing about the user's own time, the real price ladder, the one-time offer exactly as `PaywallLadder` implements it, true reassurance. Banned: countdowns or dates the code does not schedule, "today only", social proof, "lowest price ever" without a claim-ledger row, guarantees, shaming, medical claims, privacy promises beyond what the code does, hype nouns (greatness, empire, wealth). A locale brief may soften intensity, never raise it, because locales with emphatic marketing norms import intensity the product avoids. [inferred; ladder in `Manifesting/Features/Paywall/Domain/Entities/PaywallLadder.swift`, `hasProducts = false` at :32]

## Brand and fixed names

- `Moneyfesting` stays exactly as written in every language and script: no transliteration into Arabic, Hebrew, Chinese, Japanese or Korean script, no declension glued on beyond the locale's normal hyphen rule; the brand row of each brief's `## Platform terms` records how the language carries case and where quotes apply (ro: "aplicației Moneyfesting", never "Moneyfesting-ul").
- Coach names and quote authors stay as authored [archive: `Docs/Archive/I18N_PLAN.md` section 7; no coach name exists in the catalog at snapshot 2026-09-15, so the rule is dormant]. Attributed quotations port only as labelled translations and never as the speaker's own words; authored affirmations carry their English original through `pairId` [`Data/quotes/SCHEMA.md`; rules in `references/project-context.md` `## Content policy`].
- Apple product names take Apple's own localization, recorded per locale in the brief's `## Platform terms` table; a generic phrase sharing their words ("time on screen") is a different concept and stays generic.
- The restricted-apps group name ships as the Swift literal "No Restricted Apps" (`Manifesting/Features/Plan/Data/Repositories/ToDoTaskRepository.swift:333`), unlocalized: flag it, never translate it in place.

## Source lines to flag, not fix

Re-verify against the live catalog, record the flag in findings, then translate faithfully:

- `onboarding.notificationsSetup.message`: "wisdom of top billionaires ... achieve greatness" (hype nouns).
- `moneyfesting.details.stopConfirmationMessage`: guilt plea ("leave only if you really need to").
- `onboarding.screenTimePermission.footer`: "100% on your phone" (privacy promise beyond code).
- `paywall.onboardingSubscription.heroLineThree`: "Start free." renders at `Manifesting/Features/Paywall/Business/SubscriptionPaywall/View/OnboardingSubscriptionPaywallView.swift:317` while `PaywallLadder.hasProducts` is `false`.
- `paywall.winBack.urgency`, `paywall.lastChance.urgency`: "it's gone", "lowest price we offer", with the ladder step held only in memory (`Manifesting/Features/Paywall/Business/SubscriptionPaywall/ViewModel/OnboardingSubscriptionPaywallViewModel.swift:52`).
- `plan.dailyPlan.futureEmptyMessage`, `plan.dailyPlan.timelinePotentialSuffix`, `streakFreeze.info.body`: exclamation.
- `screenTimeReport.missingWage` (`ro` only): "câștigul pe oră" is an outcome word for the hourly rate; the source says "hourly wage".
