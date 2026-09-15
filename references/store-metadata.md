# Store metadata

Field limits, snapshot 2026-09-15 (re-check in App Store Connect before submission): name 30, subtitle 30, promotional text 170, keywords 100, description 4000, what's new 4000 characters. Report the count next to every value. Store copy uses the same voice, the same locale brief and the same claim ledger as the app; it is the one surface a reader sees before trusting the app, so a translated-sounding line costs more here than anywhere else.

Four rules:

1. No price, trial, rating or user-count claim in name, subtitle or keywords, and none elsewhere without a ledger row that proves it: `PaywallSocialProof.swift:18-20` ships no rating and no testimonials, and `PaywallLadder.hasProducts` is false (`PaywallLadder.swift:32`), so "Free trial" is untrue in promotional text until products exist.
2. Every numeric or feature claim gets a claim-ledger row per locale, recounted against the shipped build, because the archive's counts are already stale: widgets are six (`ManifestingWidgetsBundle.swift:7-12`, the archive says five), badges 24 (`BadgeID.swift`), wallpapers 69 (`Manifesting/Resources/JSONs/themes.json`), quotes en 6359 / ro 637 (`Manifesting/Resources/JSONs/quotes.json`; the archive counted 2,820 / 637). The ro corpus is far smaller than the en one, so ro copy never carries the en number.
3. The non-payment clarifier (the locale's one approved "not a source of income" form, `onboarding.hourlyWage.disclaimer`) sits inside the first 200 description characters; screenshot captions reuse `onboarding.welcome.slide.*` copy verbatim where the slide shows that screen; Apple product names take Apple's local term (ro "Timp de utilizare", where the archive's ro paragraph kept "Screen Time").
4. Keywords are comma-separated without spaces, repeat no word from name or subtitle, list diacritic and plain variants until index behaviour is verified, and are counted after trimming (the archived ro set is 105 characters).

Precedent: `Docs/Archive/APP_UPDATE_PLANS/04_app_store_marketing.md` section E (en and ro values for every field, with counts) and section G (the honesty pass: one row per claim with the implementing file and a verdict). It is archived, so reuse its shape and re-check every claim and count against the shipped build. Its description order still holds: the money frame and clarifier first, then how a session works, app blocking, the streak and its freeze, the widgets, statistics, themes and quotes, subscription disclosure last. Screenshot captures run the welcome carousel with `-welcomeCapture` (`WelcomeCaptureQuoteCatalog.swift:6`) and `-welcomePreviewLanguage <code>`, once per locale.

Locale labels versus resource tags: `references/locale-decisions.md`.

Deliverable: per-locale values for each field, with counts and ledger rows, in the run's coordinator packet (`<run-dir>/coordinator/store.<locale>.json`), through the same translator, blind editor and back-translation passes as Tier A; role C reviews the store packet, no new role. Store copy has no repo home, so it stays in the packet and the report unless the user names a location; never paste it into the catalog.
