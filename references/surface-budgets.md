# Surface budgets

Snapshot 2026-09-15 of the Moneyfesting checkout; the live source wins over every row. Character budgets guide drafting; only a measurement (the width suites in [render evidence](render-evidence.md#width-and-copy-suites-as-hooks)) or a render establishes fit. Read this before drafting any widget, shield, accessory, tab, badge, hero or single-line CTA string, and again when a render or a suite reports shrink, wrapping or overflow.

Contents: repo-fixed rows · platform-default rows · catalog microcopy templates · fit verdicts · the accessibility exemption · shortening for fit · what a budget cannot decide.

## Repo-fixed rows

Exact constraints read from a modifier, a test or a design document. Cite the row as `budgetSource: repo` in the packet's `layout` field; `scripts/scan_layout_constraints.py` reports the same modifiers as `budgetSource: scanner` and a mismatch between the two is a finding against the row, never a fact about the view.

| Screen > control | Source (checkout path:line) | Lines · font · floor · width |
|---|---|---|
| Start Focus widget > action capsule | `Manifesting/Foundation/WidgetSupport/StartFocus/StartFocusWidgetTile.swift:18-23` | 1 line · 14pt semibold · floor 0.6, tightening on · systemSmall 158pt minus 12pt tile padding (:33) and 8pt capsule padding per side, about 118pt of text; content margins are disabled (`Manifesting/WidgetsExtension/Widgets/StartFocusWidget.swift:64`) |
| Streak widget (systemMedium) > run-length title | `ManifestingTests/Widgets/StreakWidgetCopyTests.swift:50-53` | 20pt bold · floor 16/20 · column 0.56 x 338 minus 26pt (about 163pt); measured at 1, 12, 123 and 3650 days (`StreakRules.maxTrackedDays`, `Manifesting/Features/FocusTask/Domain/Repositories/FocusSessionRepositoryProtocol.swift:11`) |
| Streak widget (accessoryRectangular) > headline and caption | `Manifesting/Foundation/WidgetSupport/Streak/StreakTiles.swift:250-253, 257-260` | 1 line each · `.headline` and `.caption` · floor 0.8 · 160 x 72 minus the system content margins (:264) |
| Achievements > badge tile name | `Manifesting/Features/Achievements/Business/Shared/View/BadgeTileView.swift:24-25` | 2 lines · `.caption` semibold · floor 0.8 · cap `.accessibility3` (:32); centred under the art at standard sizes, beside it at accessibility sizes (:41-47), so both branches need a render |
| Welcome > headline | `Manifesting/Features/Onboarding/Business/Welcome/View/WelcomeView.swift:126-130` | 2 lines · 32pt heavy · floor 0.6 at standard sizes; unlimited lines, scaled font and floor 1 at accessibility sizes; no cap on the view |
| Paywall > hero (three stacked lines) | `Manifesting/Features/Paywall/Business/SubscriptionPaywall/View/OnboardingSubscriptionPaywallView.swift:314-326` | three one-line `Text`s, no `lineLimit` · `.largeTitle` bold · floor 0.6 (:325) · cap `.accessibility3` (:326); the benefits block caps at `.accessibility2` (:189), so its lines never grow past that |
| Today tasks widget > task row title | `Manifesting/Foundation/PlanWidgetSupport/TodayTasksWidgetView.swift:84-91, 121-124` | 1 line · `.caption` medium · no floor, so overflow truncates · 5 rows on systemLarge, else 2; the timing caption hides on systemSmall at accessibility sizes (:89) |
| Widget gallery frames | `Manifesting/Foundation/WidgetSupport/Streak/StreakWidgetDebugGallery.swift:11-14`; `Manifesting/Foundation/WidgetSupport/FocusRing/FocusRingDebugGallery.swift:11-12` | 158 x 158, 338 x 158, 72 x 72, 160 x 72 points |
| Streak mascot lines (authoring target) | `Docs/Research/MASCOT_WIDGET_STATES.md:345-353` (section 6.9) | at most 20 characters small, 24 medium, authored in Romanian first; type never truncates and never scales below 11pt; at the largest accessibility size the day strip yields first, then the mascot, never the text |

The app ships 61 numeric `minimumScaleFactor` sites from 0.25 to 0.85 and 35 `.dynamicTypeSize(...)` caps (snapshot), so a verdict always uses the row's own floor and cap; a fixed 0.8 or 0.6 threshold would pass text the view truncates and fail text the view scales happily.

## Platform-default rows

Approximate: the width belongs to iOS, not the repo, so a render on the project simulator is required and a character estimate only ranks candidates.

| Surface | Reader in the checkout | Approximate budget |
|---|---|---|
| Tab bar, 4 labels `main.tab.*` (Moneyfesting · Plan · Statistici · Profil in `ro`) | `Manifesting/App/MainRouteBuilder.swift:197-214` | about 70pt each at 10pt, no scaling; iOS truncates with an ellipsis |
| Navigation titles, all `.inline` (8 `.navigationTitle` sites) | `grep -rn navigationTitle Manifesting` | screen width minus about 176pt of bar items at 17pt semibold |
| Alerts (12 `.alert(` sites) | feature views | 270pt sheet, title and message wrap; two side-by-side buttons about 120pt each, three or longer titles stack |
| Notification banners (6 `notifications.*` keys) | `Manifesting/Features/Notifications/Data/Services/NotificationsManager.swift`; expanded UI in `MoneyfestingNotificationContentExtension/` | collapsed banner shows the title and about 2 lines of body |
| Screen Time shield title and body | `Manifesting/Foundation/ShieldSupport/ShieldMessageCatalog.swift` (25 pairs) | OS-owned layout and button geometry; the gallery approximates it (`Docs/Research/SCREEN_SHIELD_RESEARCH/README.md:34`), unverified beyond that |

A platform-default row passes only with render evidence; when the measured text sits within 10% of the estimate, capture the next larger content size too, because the estimate is not precise enough to call it.

## Catalog microcopy templates

Numeric first, at most 5 characters after the number, no space before a unit the locale writes glued (snapshot values):

- `paywall.price.perWeek`: `%@ /wk` -> `%@ /săpt.`
- `paywall.discountBadge`: `%lld%% OFF` -> `-%lld%%` (the sign replaces the word; a local reader knows `-30%` on a badge)
- `share.duration.daysShort`: `%lldd` -> `%lldz`

Uppercase eyebrows expand hardest and cannot shrink into a second line: `insights.mood.mood` `MOOD` -> `STARE DE SPIRIT` is 3.75x (snapshot). When a `textCase(.uppercase)` site receives a long target, prefer the shorter everyday noun over the exact one, and file the row when none exists.

## Fit verdicts

Points, not characters. Record one verdict per string per rendered size in the packet's `fit` field:

- `fits`: measured width at `.large` is inside the budget with the longest reachable value.
- `shrinks(x)`: fits only after scaling to `x`, where `x` is at or above the view's own floor.
- `wraps(n)`: needs `n` lines, within the view's `lineLimit`.
- `overflow`: scaled below the floor, truncated, or wrapped past the design's line count.

Judge legibility at the view's own `minimumScaleFactor` and `lineLimit`, with the longest reachable value from [render evidence](render-evidence.md#expansion-stress). `overflow` is a visual fail. A visible shrink on running text (a body line, a row title, a hero) is an editor finding: shorten or justify in the disposition, since scaled body text reads as a mistake to a local user even when it technically fits. Never propose lowering a floor or raising a line limit to make copy fit; file a layout finding for engineering instead, because the modifier encodes a design decision the translator does not own. The per-locale length trigger lives in the brief (`ro` 1.35x, from `Docs/Archive/I18N_PLAN.md:240`); it marks a string for the render list (`catalog_check` C5), it is not a finding, and 299 of the 1135 `ro` units already exceed it (snapshot), so a trigger alone never blocks a batch.

## The accessibility exemption

Accessibility labels, VoiceOver strings and share-card accessibility text are exempt from shortening and from fit verdicts (visual `not_checked`, by design): they are spoken, so they spell units out and use full sentences. `widgets.focusRing.a11y.firstRun`, `.goalMet` and `.progress` carry `min` and `min.` in `ro` today (snapshot); that is the live violation to fix when those keys are in scope, never a pattern to copy. `ManifestingTests/Widgets/FocusRingCopyTests.swift` (`romanianAccessibilityLabelsAvoidTheCountedNoun`) pins the abbreviation today, so the fix is `ro` plural variations plus that assertion change, an owner decision listed in the report. The same string must not serve as both a visible label and a spoken one when the visible slot forces an abbreviation.

## Shortening for fit

Apply when render evidence or a width suite reports shrink, extra wrapping or overflow, and the row's verdict says the target, not the layout, is the cause; the round-budget rule is in agent-protocol.md `## Tiers, order and batches`.

Functional copy, in this order, stopping as soon as the string fits:

1. Drop what the brief marks droppable (fillers, articles, "please", the possessive the source habitually adds).
2. Drop the object the icon, row or screen title already names ("Start focus session" on the focus tab becomes "Start").
3. Use the brief's short form (locale-briefs/TEMPLATE.md `Short forms and units`), which is the form a local product team already prints, not a new abbreviation.
4. Use a shorter synonym with the same action and the same certainty; "Save" may become "Keep" only when the brief says the two read alike in that slot.

Marketing and authored copy, in this order:

1. Cut intensifiers and second adjectives.
2. Cut the second clause when the first carries the claim.
3. Swap the image for a shorter local one that carries the same meaning and register, the way "raining cats and dogs" becomes "plouă cu găleata"; when no local image fits, state the meaning plainly rather than keep a literal picture that reads as translationese.

In both orders keep deliberate source line breaks (the paywall hero is three lines by design) and the claim's condition: "Not money earned." survives every cut. Shortening may cut words, never facts. A fact that must go moves to a neighbouring element, and the key's comment says where it went ("placeholder moved to `<key>`", which `scripts/catalog_check.py` C1 reads), so the next translator does not put it back.

## What a budget cannot decide

A row says whether text fits, not whether it is right. A `fits` verdict on a truncated meaning, a dropped negation or an abbreviation a local reader would not use is still a fail on meaning or naturalness, and those verdicts stay independent (agent-protocol.md `## Acceptance and evidence`). When the only way to fit is to change what the string claims, the answer is a layout finding or a neighbour move, not a shorter claim.
