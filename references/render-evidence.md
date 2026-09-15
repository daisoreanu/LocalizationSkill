# Render evidence

Snapshot 2026-09-15 of the Moneyfesting checkout; the app `CLAUDE.md` and live source win. Use this in `translate` mode for every batch with widget, shield, accessory, hero or single-line CTA strings (before language review, agent-protocol.md `## Tiers, order and batches` step b) and again after integration, and in `audit` mode when a user asks whether copy fits. A string without evidence at `.large` and at its view's cap gets the visual verdict `not_checked`, whatever the language review said.

Contents: build and install · switch the app language · content sizes and caps · galleries and launch arguments · evidence status · what to capture per surface class · capture record · expansion stress · width and copy suites as hooks · constraints to file, not fix.

## Build and install

Build once per batch with the Development scheme (`CLAUDE.md:6-13`), and run only the named suites from `## Width and copy suites as hooks`, never the full `test` action, because any `xcodebuild test` shuts the simulator down when it finishes (`Docs/Research/MASCOT_WIDGET_STATES.md:623-624`) and a full run adds minutes the render step does not need; `UDID` is the project simulator `79405175-1BEC-48D3-A8DC-F8358E356C6C` (`CLAUDE.md:7`), the only one this skill may touch (`CLAUDE.md:8`):

```sh
cd <checkout>
xcodebuild -project Manifesting.xcodeproj -scheme 'Moneyfesting Development' \
  -destination "platform=iOS Simulator,id=$UDID" \
  -skipMacroValidation BUILD_ACTIVE_RESOURCES_ONLY=NO \
  -derivedDataPath "$RUN/build" build
xcrun simctl boot "$UDID" 2>/dev/null || true
xcrun simctl install "$UDID" "$RUN/build/Build/Products/Debug-iphonesimulator/Manifesting.app"
xcrun simctl launch --terminate-running-process "$UDID" com.daisoreanu.Manifesting.dev <launch arguments>
xcrun simctl io "$UDID" screenshot "$RUN/evidence/<key-or-page>-<locale>-<size>[-<state>].png"
```

`RUN` is the run directory `<checkout>/.codex-tmp/localization/<locale>/<run-id>` (gitignored, `.gitignore:2`); `-derivedDataPath` keeps the build out of the shared cache so a second run cannot pick up a stale catalog. The product is `Manifesting.app` (`PRODUCT_NAME = Manifesting` in `Manifesting.xcodeproj/project.pbxproj`; display name "Moneyfesting Dev"); the dev bundle id is `com.daisoreanu.Manifesting.dev`, the production one `com.daisoreanu.Manifesting`. A suite run ends with the device shut down, so boot again before captures that follow one. In Claude Code the XcodeBuildMCP `build_sim`, `install_app_sim`, `launch_app_sim` and `screenshot` tools wrap the same commands; either way, keep the screenshot on disk under `$RUN/evidence/`.

## Switch the app language

- Welcome galleries and captures: `-welcomePreviewLanguage <code>`, honoured only together with `-widgetDebugGallery welcome*` or `-welcomeCapture`, codes limited to `AppLanguage.supportedLanguageCodes` (`Manifesting/Foundation/Localization/AppLanguage.swift:79-91`; `["en", "ro"]` at `:6`). The override is process-only, so ordinary launches and extensions keep the saved preference.
- Everything else, extensions included, reads the app-group default `appLanguageOverride` (`Manifesting/Foundation/Persistence/UserDefaultsKeys.swift:12`; a `String` enum, so the raw key is the case name) in suite `group.com.daisoreanu.Manifesting` (`Manifesting/Foundation/Localization/AppLanguage.swift:94-96`). Set it once in Profile > Language (`Manifesting/Features/Profile/Business/ProfileLanguage/View/ProfileLanguageEditView.swift`) and capture from then on; the app rebuilds its view tree on the change (`Manifesting/App/ManifestingApp.swift:76-79`). Shortcut, unverified until tried in this environment: `xcrun simctl get_app_container "$UDID" com.daisoreanu.Manifesting.dev groups` names the container, write `appLanguageOverride` as a string into `Library/Preferences/group.com.daisoreanu.Manifesting.plist` there, then relaunch, because an external write does not notify the running store.
- Shields: `-shieldPreviewRomanian` selects the `ro` pair and nothing else (`Manifesting/Foundation/ShieldSupport/ShieldDebugGallery.swift:119-121`); a third language needs the struct change noted in project-context.md before any shield can be previewed.
- A locale outside `supportedLanguageCodes` cannot be previewed at all until `Manifesting/Foundation/Localization/AppLanguage.swift:6` changes, so a new language is an engineering flag before it is evidence work. Do not use `-AppleLanguages` or the scheme's App Language: `CLAUDE.md:42` forbids the override, and a stored app-group override wins over the bundle's negotiated language anyway (`Manifesting/Foundation/Localization/AppLanguage.swift:46-48`), so the capture would show the wrong language without saying so.

## Content sizes and caps

```sh
xcrun simctl ui "$UDID" content_size large                                   # .large, the design size
xcrun simctl ui "$UDID" content_size extra-extra-extra-large                 # .xxxLarge, largest standard
xcrun simctl ui "$UDID" content_size accessibility-large                     # .accessibility2
xcrun simctl ui "$UDID" content_size accessibility-extra-large               # .accessibility3
xcrun simctl ui "$UDID" content_size accessibility-extra-extra-extra-large   # .accessibility5, the largest
xcrun simctl ui "$UDID" appearance dark                                      # widgets follow the system; the app forces dark (ManifestingApp.swift:15)
```

Values are those `xcrun simctl help ui` lists; `accessibility-medium` is `.accessibility1`. Render every string at `.large` and at its view's own cap: 35 `.dynamicTypeSize(...)` cap sites and 15 `isAccessibilitySize` branches in four files at snapshot (`Manifesting/Features/Achievements/Business/Shared/View/BadgeTileView.swift:41`, `Manifesting/Features/Onboarding/Business/Welcome/View/WelcomeView.swift:126-130`, `Manifesting/Foundation/PlanWidgetSupport/TodayTasksWidgetView.swift:89,111,123`, `Manifesting/Foundation/DesignSystem/Components/PhoneFanPageDots.swift`). Where a branch switches the layout, capture both sides of the switch, because the string sits in a different frame on each. A view without a cap is captured at `accessibility-extra-extra-extra-large`. Width is the project device only (`CLAUDE.md:7-8`); width variation comes from the gallery frames and the width suites below, never from another simulator.

## Galleries and launch arguments

All DEBUG-only. `-widgetDebugGallery` replaces the app root with a gallery (`Manifesting/App/ManifestingApp.swift:46-62`); the streak-state pin is applied at launch (`:9`).

| Argument | Read in | Values (snapshot) | Shows |
|---|---|---|---|
| `-widgetDebugGallery <page>` | `Manifesting/Foundation/WidgetSupport/Shared/WidgetDebugOverride.swift:38-49` | `shield` · `welcome-capture-plan` · `welcome-capture-ring` · `welcome`, `welcome-0` to `welcome-4`, `welcome-large-0` (`Manifesting/Features/Onboarding/Business/Welcome/PreviewSupport/WelcomeDebugGallery.swift:5,14-15,24-26,33`; `large` pins `.accessibility3`) · `ringSmall`, `ringSmall2`, `ringMedium`, `ringMedium2`, `ringMedium3`, `ringPlain` (`Manifesting/Foundation/WidgetSupport/FocusRing/FocusRingDebugGallery.swift:1`) · `celebrationMilestone`, `celebrationComeback`, `celebrationFirstDay`, `celebrationFreeze`, `celebrationEve`, any other `celebration…` for the default sample (`Manifesting/Features/Achievements/Business/Shared/View/CelebrationDebugGallery.swift:19-33`) · `small`, `small2`, `smallPlain`, `smallPlain2`, `pool`, `medium1`, `medium2`, `medium3`, `accessory`, `artSmall`, `artMedium1`, `artMedium2` (`Manifesting/Foundation/WidgetSupport/Streak/StreakWidgetDebugGallery.swift:1-2,51-76`: `small` holds states 1-6, `small2` 7-9, `medium1-3` four each) | the exact tile, welcome, celebration or shield views in fixed frames |
| `-widgetDebugStreakState <state>[+live]` or `clear` | `Manifesting/Foundation/WidgetSupport/Shared/WidgetDebugOverride.swift:12-15,51-74` | `newHere`, `open`, `cleared`, `atRisk`, `frozen`, `lapsed`, `unavailable` (`Manifesting/Foundation/WidgetSupport/Streak/StreakWidgetState.swift:6-13`) | pins the real Home Screen streak widget through the app-group key; a normal launch clears the pin (`:64-66`) |
| `-welcomePreviewLanguage <code>` | `Manifesting/Foundation/Localization/AppLanguage.swift:79-91` | `en`, `ro` | process-only language for the welcome pages |
| `-welcomeCapture` | `Manifesting/Features/Onboarding/Business/Welcome/PreviewSupport/WelcomeCaptureQuoteCatalog.swift:6-11`; `Manifesting/Foundation/Localization/AppLanguage.swift:84` | flag | one fixed quote per language so captures are reproducible |
| `-shieldPreviewIndex <n>` | `Manifesting/Foundation/ShieldSupport/ShieldDebugGallery.swift:113-117` | 0 to 24 (25 pairs in `Manifesting/Foundation/ShieldSupport/ShieldMessageCatalog.swift`) | one message pair |
| `-shieldPreviewStyle <style>` | `Manifesting/Foundation/ShieldSupport/ShieldDebugGallery.swift:122-126` | `companion`, `calm`, `focused`, `reset`, `regroup` (`Manifesting/Foundation/ShieldSupport/ShieldMessage.swift:4-8`) | the first message of that family |
| `-shieldPreviewRomanian` | `Manifesting/Foundation/ShieldSupport/ShieldDebugGallery.swift:119-121` | flag | the `ro` pair |
| `-shieldPreviewWebsite` | `Manifesting/Foundation/ShieldSupport/ShieldDebugGallery.swift:128` | flag | the website close label instead of the app one |
| `-shieldPreviewLargeType` | `Manifesting/Foundation/ShieldSupport/ShieldDebugGallery.swift:129`, applied at `:33` | flag | the gallery at `.accessibility3` |

Combine freely: `-widgetDebugGallery shield -shieldPreviewStyle calm -shieldPreviewRomanian -shieldPreviewLargeType`. Surfaces without a gallery (tab bar, navigation titles, alerts, rows, paywall, profile, insights) are captured by navigating the installed app in the target language, in Claude Code through XcodeBuildMCP `snapshot_ui` and `screenshot`, otherwise through `simctl io screenshot`; `snapshot_ui` also returns the accessibility tree, which is the evidence for VoiceOver label text and order.

## Evidence status

- `approximate`: any gallery capture. Frames are fixed at 158, 338, 72 and 160 points, plain pages inject ink and cannot reproduce system desaturation (`Manifesting/Foundation/WidgetSupport/Streak/StreakWidgetDebugGallery.swift:2`), the shield gallery does not move the native button whose geometry iOS owns (`Docs/Research/SCREEN_SHIELD_RESEARCH/README.md:34`), and the welcome gallery pins one slide.
- `exact`: a Home Screen or Lock Screen capture of the real widget (placed once by hand, or by the host's UI automation), a real shield, or the real screen reached by navigation. The repo recorded SpringBoard crashing when a widget was placed on this simulator (`Docs/Research/MASCOT_WIDGET_STATES.md:614-619`, x86-64 iOS 26.1; this environment is x86-64 too): if it reproduces, record the attempt in the capture record, use the system widget gallery's preview page, which draws the real WidgetKit snapshot, and keep the status `approximate`.

An `approximate` capture passes a repo-fixed row; a platform-default row in [surface budgets](surface-budgets.md#platform-default-rows) needs an `exact` one, and any measured width within 10% of an approximate budget needs the next larger size captured as well.

## What to capture per surface class

Smallest supported size means `.large` on the project device; largest relevant means the view's own cap, else `accessibility-extra-extra-extra-large`. Locale means the target locale plus `en` for the reviewer's side-by-side.

| Class | Pages or path | Sizes | State coverage |
|---|---|---|---|
| Streak widget (systemSmall, systemMedium, accessoryCircular, accessoryRectangular; `Manifesting/WidgetsExtension/Widgets/StreakWidget.swift:102`) | `small`, `small2`, `medium1-3`, `accessory`; exact through `-widgetDebugStreakState` | `.large`, `accessibility-extra-extra-extra-large` (MASCOT 6.9 defines the yield order there) | all seven states; `open+live`; `smallPlain` for the accented rendering mode |
| Focus ring widget (systemSmall, systemMedium; `Manifesting/WidgetsExtension/Widgets/FocusRingWidget.swift:111`) | `ringSmall`, `ringSmall2`, `ringMedium-3`, `ringPlain` | same | 0%, partial, goal met, no goal, unavailable; the `a11y` labels are recorded from the tree, not rendered |
| Start Focus widget (systemSmall; `Manifesting/WidgetsExtension/Widgets/StartFocusWidget.swift:63`) | `StartFocusWidgetLayoutTests` is the harness; Home Screen for exact | `.large`, largest | ready, not set up, unavailable, 5 to 120 minutes |
| Today tasks widget (small, medium, large; `Manifesting/WidgetsExtension/Widgets/TodayTasksWidget.swift:84`) and Monthly time value (medium; `Manifesting/WidgetsExtension/Widgets/MonthlyTimeValueWidget.swift:58`) and Quotes (small, medium, large; `Manifesting/WidgetsExtension/Widgets/QuotesWidget.swift:76`) | layout suites plus Home Screen | `.large`, largest | full row count (5 on systemLarge), empty and notice states; longest bundled quote |
| Shield | `shield` with each `-shieldPreviewStyle`, both close labels | `.large`, `-shieldPreviewLargeType` | all five families in `en` and the target |
| Welcome | `welcome-0` to `welcome-4`, `welcome-large-0` | `.large`, `.accessibility3` | every slide; regenerate the capture PNGs after copy is final (project-context.md Discovery map, Welcome carousel images) |
| Paywall | navigation, onboarding paywall step | `.large`, `.accessibility2` (benefits), `.accessibility3` (hero) | initial hero with `PaywallLadder.hasProducts` false and true, before/after view, discount screen, restore |
| Celebration | the five `celebration…` pages | `.large`, largest | milestone, comeback, first day, freeze, eve |
| Tab bar, navigation titles, alerts, rows | navigation | `.large`, largest | every alert with its full button set; the longest list row title the catalog can produce |
| Notifications | the app schedules them (`Manifesting/Features/Notifications/Data/Services/NotificationsManager.swift`); the expanded UI is `MoneyfestingNotificationContentExtension/` | `.large` | collapsed banner and expanded content; status `approximate` when pushed with a hand-built payload |
| Share cards and Screen Time report | `ShareCardRenderTests`, `ScreenTimeUsageLayoutTests` are the evidence; a real share sheet capture only for the banner | suite sizes | every `ShareCardFormat`; wages up to 1,000,000 |
| VoiceOver and accessibility labels | `snapshot_ui` tree, or `simctl` with Accessibility Inspector | none | label text and order per screen state; exempt from fit (surface-budgets.md, the accessibility exemption) |

## Capture record

One JSON object per image, appended to `$RUN/coordinator/evidence.json` and merged into the packet's `evidence` field with `scripts/build_context_packet.py --update`:

```json
{"id": "s07", "key": "widgets.streak.dayStreakCount", "locale": "ro",
 "device": "79405175-1BEC-48D3-A8DC-F8358E356C6C iPhone 17 Pro iOS 26.1",
 "page": "medium1", "state": "open+live", "content_size": "accessibility-extra-extra-extra-large",
 "appearance": "dark", "rendering_mode": "fullColor", "sample": "serie de 123 de zile",
 "path": ".codex-tmp/localization/ro/2026-09-15-a/evidence/widgets.streak.dayStreakCount-ro-ax5-open+live.png",
 "status": "approximate", "verdict": "shrinks(0.85)"}
```

`device`, `locale`, `state`, `content_size` and `path` are required; `page` for galleries, `rendering_mode` for widgets, `sample` whenever a placeholder or plural branch was filled. The `verdict` uses the vocabulary in [surface budgets](surface-budgets.md#fit-verdicts). The report line `renders <n> (approximate|exact)` counts these records; the visual verdict passes only when every string that is not `fits` has a record at `.large` and at its cap.

## Expansion stress

Fit verdicts come from the longest reachable value per placeholder and per plural branch, never from the English example in the comment. Use the repo's own samples so the evidence matches what the suites measure:

- Minutes: 5, 10, 95, 100, 120 (`ManifestingTests/Widgets/StartFocusWidgetLayoutTests.swift:13`).
- Streak days: 1, 12, 123 and 3650 (`ManifestingTests/Widgets/StreakWidgetCopyTests.swift:57`, `StreakRules.maxTrackedDays`); in `ro` the `other` branch adds the partitive, so `Serie de 100 de zile` (`achievements.streak.headline`) is longer than `Serie de 12 zile` by more than the digits.
- Names: 40 characters (`Manifesting/Features/User/Domain/Entities/UserProfileValidation.swift:4`).
- Money: `RON 121545`, `BHD 121545.123`, `BHD 720000000.123` (`ManifestingTests/Localization/CurrencyLayoutTests.swift:65`), wages 999, 1000, 999000, 1000000 (`ManifestingTests/ScreenTime/ScreenTimeUsageLayoutTests.swift:37`), formatted through `AppLanguage.effectiveLocale` so the grouping and decimal marks are the locale's.
- Quotes: the longest bundled quote in the locale (`ManifestingTests/Share/ShareCardRenderTests.swift:66` checks it stays inside the square canvas).
- Uppercase eyebrows and unit suffixes: the real catalog values (`STARE DE SPIRIT`, `/săpt.`), not a padded English.

Use real long target values rather than pseudolocalization: padding stretches every string by the same factor and cannot show where Romanian's partitive `de`, a glued unit or an uppercase eyebrow actually lands, and the catalog already holds the real cases (299 of 1135 `ro` units exceed 1.35x at snapshot). `-NSDoubleLocalizedStrings YES` is a plain launch argument that doubles the resolved string; confirm once per environment on one known screen whether this app honours it, record the result in the run, and treat it as a headroom probe for English only. The width suites below are the harness for these values; extend their language arguments only when the user authorizes test changes.

## Width and copy suites as hooks

Run the suite for the surface before any character counting and before a shortening pass, using the `CLAUDE.md:12-13` command with `-only-testing:ManifestingDevTests/<SuiteType>` on the Development scheme (`ManifestingTests/<SuiteType>` on Production, `CLAUDE.md:6`); the suite type is the `struct` name, not the folder. What each one settles in the evidence flow:

| Suite type | Measures | Frame and languages |
|---|---|---|
| `StreakWidgetCopyTests` | run-length title width in the real 20pt bold font against the medium column | 0.56 x 338 minus 26pt; iterates `supportedLanguageCodes`, so a new language is covered without edits |
| `StartFocusWidgetLayoutTests` | duration and action capsule survive OCR at 158pt in both rendering modes | 158 x 158; `["en", "ro"]` |
| `QuoteWidgetLayoutTests`, `MonthlyTimeValueLayoutTests` | quote and time-value tiles per family | 141 and 292 wide; 292 x 141, 338 x 158, 320 wide; `["en", "ro"]` |
| `MoodLayoutTests` | mood card and sheet | 358 x 180; 390 x 780 and 320 x 568 at `.large` and `.accessibility1`; `["en", "ro"]` |
| `ScreenTimeUsageLayoutTests`, `CurrencyLayoutTests` | report rows and currency screens with Vision OCR | 320 and 430 wide, `largeText` variants; `["en", "ro"]` |
| `ShareCardRenderTests` | every share format at device size | 402 x 874; `["en", "ro"]` |
| `FocusRingCopyTests` (`romanianAccessibilityLabelsAvoidTheCountedNoun`, `:116-135`) | a locale-grammar assertion on spoken labels, the pattern for a new locale's rule | copy only |
| `PaywallBeforeAfterTests` | before/after chart ratio and gating (`:19-63`); digits in the hours texts and non-empty benefit rows under `en` (`:76-101`); no width or wording assertion, so a target-language change cannot fail it | no frame; `en` only |
| `PaywallLocalizationTests`, `OnboardingCopyTests`, `OnboardingWidgetsStepTests` | claim invariants and banned words per language | copy only; details in project-context.md `## Verification hooks` |

A green suite is `fits` evidence for exactly the frames it renders and nothing else; a red one is classified as translation or layout before anyone shortens copy, and a material condition is never dropped for fit. Suites cover widgets, share cards, mood, the Screen Time report, currency and the onboarding and paywall claims only; every other surface still needs a capture. For a new language extend every literal `["en", "ro"]` array under `ManifestingTests` (18 files at snapshot, `grep -rl '\["en", "ro"\]' ManifestingTests`); new assertions use `AppLanguageTestSupport.withLanguage` (`ManifestingTests/Localization/AppLanguageTestSupport.swift:11`) and belong to both test targets (`CLAUDE.md:25`), so they are proposed in the report, not added unasked.

## Constraints to file, not fix

- RTL: the app has no `layoutDirection` handling (grep, snapshot). `-AppleTextDirection YES` forces RTL for the whole process and cannot follow the in-app language switch, so an `ar` or `he` capture made that way shows a layout the app cannot ship; file it as an engineering constraint in the report's decisions, not as a fit finding on the copy.
- Shield geometry, tab-bar truncation and alert button stacking belong to iOS; a string that only fits by abbreviating past the brief's short forms is a layout finding with the capture attached.
- Missing evidence is reported as `renders none` or `not_checked`, never as a pass; the honest gap is what lets the owner decide whether to ship.
