# Romanian examples

Mined from the shipped `ro` catalog, snapshot 2026-09-15, commit `c8a49dd`. Provenance: owner-accepted agent output under the archived acceptance rule "Romanian written by you, review-agent-checked" (`Docs/Archive/I18N_PROMPT.md:235`), so this is house-style evidence, not a native corpus. Give the file to the forward translator and the final adjudicator only; never to the blind editor or back-translator, because the EN column breaks packet separation. A locale without an examples file gets this one as pattern illustration and its first batch returns six rows in the same format (see `agent-protocol.md` `## A. Forward translator`).

Read the screen column before the pattern: every row is what it is because of where it renders.

## Keep (patterns to reproduce)

| Key | EN | RO | Screen and control | Pattern |
|---|---|---|---|---|
| `onboarding.alert.screenTimeMessage` | In order to proceed you need to tap "Continue" in order to provide "Moneyfesting" access to Screen Time | Ca să continui, apasă „Continuă” pentru a-i oferi aplicației „Moneyfesting” acces la Timp de utilizare | onboarding alert body, before the system Screen Time prompt | drop scaffolding; Apple's own term; "aplicației" carries the case so the brand stays uninflected |
| `onboarding.age.subtitle` | Please select the age group that best represents you. | Alege grupa de vârstă care ți se potrivește. | hint under a questionnaire title | drop "Please"; imperative `tu` |
| `share.screenshot.title` | Share this properly? | Îl distribui ca lumea? | banner title after a screenshot, above "Make a card" | local idiom; a literal "Distribui asta corespunzător?" would sound like a form field. A blind back-translation "Sharing it the proper way?" is an acceptable adaptation |
| `focusTask.templates.powerNap.name` | Power nap | Un pui de somn | task template name in a list | local idiom; "somn scurt de putere" would be a calque |
| `achievements.badge.clockedIn.name` | Clocked in | Primul pontaj | badge name, first completed session | workplace image kept, object changed: "pontaj" is the local clock-in card |
| `onboarding.welcome.slide.ring.headline` | Close your ring.\nBuild your momentum. | Închide inelul.\nPrinde avânt. | welcome headline, two lines, six words max | figurative mapped to the local idiom "a prinde avânt"; a literal "construiește-ți impulsul" would be wrong |
| `widgets.streak.a11y.lapsed` | Streak ended. Start the next one with five minutes of focus. | Seria s-a încheiat. Începe următoarea cu cinci minute de concentrare. | VoiceOver label, streak widget | spoken sentence, outcome reported, no mourning |
| `streakFreeze.usedBody` | We covered %@ with a streak freeze. Your streak held. | Am acoperit ziua de %@ cu un îngheț de serie. Seria ta a rezistat. | sheet body, `%@` is a date | adds "ziua de" so the date placeholder reads as a day; app voice in first-person plural |
| `profile.appUsage.axis.evening` | 06PM | 18:00 | chart axis label | time format |
| `common.durationMinuteUnit` | m | min | compact unit appended to durations ("2h 15m") | unit localization |
| `share.alert.moneyDisclosureTitle` | Show the amount? | Arătăm suma? | confirmation title, first time money goes on a card | app voice, first-person plural for what the app does |
| `screenTime.createRestrictedList.selectedSuffix` | selected | de blocat | fragment after counts ("2 apps and 1 category selected") | permitted fragment adaptation for concatenation; says what happens instead of mirroring "selected" |

## Diagnosis and candidate (never integrate without the protocol)

| Key | RO today | Issue | Candidate |
|---|---|---|---|
| `paywall.benefit.value.detail` | Setează-ți tariful și vezi cum se adună concentrarea. | calque of "watch focus add up"; concentration does not add up in Romanian | Setează-ți tariful și vezi cât valorează orele tale de concentrare. |
| `paywall.benefit.streak.title` | Serii care iartă. | personified English fragment ("Streaks that forgive"); Romanian puts the user or the outcome first. It renders inline before its detail as one `Text` (`Manifesting/Features/Paywall/Business/SubscriptionPaywall/View/OnboardingSubscriptionPaywallView.swift:178`), so keep it a short lead-in no stronger than the detail's condition | Poți rata o zi fără să-ți pierzi seria. |
| `paywall.button.restore` | Restaurează | bare verb, reads as restoring a file | Restaurează achizițiile (the verb stays unverified until Apple's ro Subscriptions wording is read; `locale-briefs/ro.md` Platform terms) |
| `share.alert.photoAccessDeniedTitle` | Acces la Poze necesar | English word order | E nevoie de acces la Poze |
| `achievements.category.payroll.name` | Statul de plată | payroll-document register for a badge family about showing up | Pontaj (pairs with "Primul pontaj") |
| `widgets.streak.copy.frozen.small` | Acoperit cu îngheț. | agreement: the covered thing is yesterday (zi, feminine); the medium line already says "Ieri a fost acoperită" | Acoperită de un îngheț. |
| `focusTask.templates.creativeBurst.name` | Explozie de creativitate | preference: noun stack; both acceptable | Rafală de idei |
| `focusTask.alert.deleteTask.title` + `.message` | Șterge sarcina / Sigur vrei să ștergi această activitate? | one alert, two words for the task (glossary `task`) | Sigur vrei să ștergi această sarcină? |
| `screenTimeReport.missingWage` | Setează-ți câștigul pe oră în Profil ca să vezi valoarea acestui timp. | "câștig" is a money-outcome word; the source says hourly wage (glossary `hourly_rate`) | Setează-ți tariful orar în Profil ca să vezi valoarea acestui timp. |
| `insights.savings.forecast` | Estimare viitoare | "future estimate" says the idea twice, and a bare "Estimare" would repeat the month-end label heard right after it ("Estimare la sfârșitul lunii") | Prognoză (open decision `forecast` in `glossary/ro.json`; check the card label width) |
| `paywall.winBack.title` | Oferta ta unică | "unică" reads as unique while the source promises an offer shown once; this is a claim on a paywall title, so a blind back-translation "Your unique offer" is a meaning finding, not a style note | Ofertă valabilă o singură dată |

Left out on purpose: the notification-permission "last step" line (an invariant change, not wording), `onboarding.notificationsSetup.motivationOff` without its emoji (contradicts the archived guide), and anything that is only a glossary choice, which lives in `glossary/ro.json`.
