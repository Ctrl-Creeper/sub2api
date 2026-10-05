# BNDS AI普及计划 frontend theme

Direction: a quiet API workspace with the four colors from Beijing National Day
School's official color logo: orange-red #e8340c, yellow #f5a100, green #81b934,
and blue #0b75be. Red drives actions (a darker #cf2e0b gives small white button
labels sufficient contrast), blue anchors navigation and the authentication
brand panel, and yellow/green provide secondary and chart accents. Light mode
uses cool white surfaces; dark mode uses blue charcoal. Keep semantic
error/success colors recognizable, restrained shadows and 8–12px corners.

Source: https://www.bnds.cn/images/logo_fo.png (official color logo), linked
from https://www.bnds.cn/. Colors were sampled from opaque flat-color pixels;
they are observed web asset values, not a claim about official print standards.
The school logo itself is not included in the app; BNDS AI普及计划 uses its own four-color open-book mark.

Surfaces: shared user/admin shell, inputs/buttons/tables/dialogs, dashboard
statistics, default and compact home, and every page using AuthLayout.
Desktop authentication uses a blue brand panel and a white form panel; mobile
stacks them. Keep the existing form slots and all auth controls. The homepage
keeps its content and links, with open feature columns instead of glass cards.
The navigation keeps its width, menu order, collapse and mobile overlay behavior.

Typography: locally available system sans; deliberate UI sizes, stronger numeric
hierarchy, tabular numbers, modest heading tracking. Keep the existing icon set.
No raster assets or external font downloads are required.

Branding: BNDS AI普及计划 replaces only the empty/default Sub2API display name. Preserve
custom site names, logos, subtitles and custom homepage content. This is a
frontend presentation change; storage keys, APIs and backend configuration stay
compatible. Remove upstream project navigation, repository/release/documentation links and proxy advertisements. Preserve custom operator documentation and functional OAuth provider links.

Verification: production build, existing routing/auth/home/component tests,
desktop/mobile browser checks, light/dark theme, shell collapse and navigation.
Image Gen is unavailable in this environment; this written specification is the
reference, with rendered screenshots used for visual review.

## Visual review

Reviewed in the built-in Paseo browser at 1440×1000 and 390×844. Checked the
school-logo palette, heading and control typography, spacing/corner treatment,
vector logo, chart colors and responsive stacking. Inspected a saved rendered
dashboard screenshot with view_image. Login, home, key usage, dashboard and admin account
management retain their existing labels and controls; intentional copy changes
are the default display name and shared fallback subtitle, onboarding text follows the configured display name, plus the existing
site name now also appearing in the homepage header. No generated image concept
was available, so the written design above is the reference.

Verified password reveal, login-to-dashboard using temporary API fixtures,
light/dark switching, sidebar collapse/expand, and mobile drawer. Existing custom
homepage mode is kept outside the default homepage styling. Production build
and changed-file ESLint pass; routing, authentication, homepage, table,
sidebar, dashboard and branding tests pass (93 relevant tests, plus the build's
3 locale completeness checks). The live backend integration was not exercised;
port 8080 belongs to an unrelated local application.

Color revision validation: changed-file ESLint and production build pass.
Rechecked login/home at 1440×1000 and 390×844, including dark-mode switching;
no horizontal overflow. Computed login-panel blue is rgb(11, 117, 190), matching
the logo sample. White text contrast is 5.19:1 on the primary button and 4.88:1
on the blue authentication panel. This revision changes presentation colors;
the 93 behavioral tests above were run for the preceding layout/branding work.

Brand revision: default display name is BNDS AI普及计划, with an open-book icon
and the fallback subtitle 让 AI 成为每个人的学习伙伴. Previous Relay and Sub2API
defaults resolve to this name. Long brand names wrap in the sidebar and mobile
public navigation. Technical identifiers and backend acknowledgement phrases
remain compatible. Legal agreement contents remain intact; the external
repository shortcut is removed.

Brand revision review: Paseo snapshots and screenshots confirm the requested
name, subtitle, open-book icon, original school palette and responsive spacing
at 1440×1000 and 390×844. The mobile login screenshot was inspected with
view_image. Home was checked in both light and dark modes; no horizontal
overflow or upstream project links remain in its rendered anchors. The
written design remains the reference for this small update. Intentional copy
changes are the requested brand, fallback subtitle and removal of project
shortcuts; custom operator content and functional provider links are preserved.
Changed-file ESLint, production build and 141 related tests pass.

Homepage copy revision: replace generic gateway and multi-model marketing with
official GPT service, student pricing and visible usage costs in both Chinese
and English. Default and compact home subtitles use localized GPT/student copy;
operator-configured subtitles remain supported. The default homepage displays
GPT only, with an OpenAI chat-completions example. Remove unused pain-point,
comparison, free-trial and additional-provider copy. Existing homepage tests
(13), locale completeness checks (3), changed-file ESLint and production build
pass. This update changes homepage presentation and copy.

## Editorial layout revision — implementation brief

Direction: a campus publication, using the existing four-color book mark and
school palette. White surfaces in light mode, deep navy in dark mode; no raster
assets, new slogans, fake statistics or external fonts. Image Gen is unavailable
in this session, so the written brief is the design reference; verify the actual
screens with the built-in browser and inspect its screenshots with view_image.

Home: preserve the current header controls, site name/subtitle, GPT-only offer,
CTA destinations and custom-home precedence. Set the brand name as a large,
left-aligned headline. A blue GPT typography panel occupies the smaller right
column, with the existing API example beneath. Replace the three-icon feature
grid with three numbered horizontal rows, using the existing official-service,
student-price and usage-billing copy. Mobile stacks the model panel after the CTA.

Auth: replace the two-column blue-panel/form frame with a centered masthead
above a rectangular form surface. Keep every form slot, validation, OAuth,
verification, agreement and footer control. Brand heading 28–32px, body 14px,
inputs and primary action at least 44px tall. The form grows with its content.

Workspace: preserve menu order and the collapsed/mobile navigation states.
Desktop navigation becomes an inset navy rail, offset 16px from the viewport,
with a four-color top edge. Main content starts at 288px (collapsed: 96px).
Use an open page heading, more square panel geometry, and statistics arranged
as a single ledger band with separators, prominent figures and colored top rules.
Tables, charts, balances and all functional controls retain their data and order.

Signature details: four-color rules, numbered service rows, rectangular form
surfaces, ledger statistics. System sans typography; restrained shadows. Mobile
uses the existing overlay navigation and compact two-column statistics. Verify
home/login/dashboard at 1440×1000 and 390×844, both themes, login controls,
sidebar collapse and mobile drawer, and existing frontend behavior tests.

### Layout review ledger

Reference: the editorial implementation brief above; the available environment
has no Image Gen tool, so there is no generated concept image. Paseo's built-in
browser rendered the real production bundle; screenshot PNGs were inspected
using view_image. QA files are temporary and are removed after verification.

- Copy: Chinese and English retain the official-GPT/student-price offer, three
  service descriptions, existing navigation and CTA destinations. No new slogan,
  price amount, statistic or provider claim was added. The provider heading and
  terminal window are consolidated into the model panel as specified.
- Composition: large left-aligned homepage brand, smaller blue GPT panel, numbered
  service rows; auth masthead sits above the form. These match the written brief.
- Typography: homepage title is 76px on desktop, 44px on mobile; form inputs are
  46px tall. Statistics are 26px/23px with tabular numbers; labels remain legible.
- Palette and assets: original four-color book SVG, white homepage, blue GPT
  panel and navy navigation; no new raster imagery or external fonts.
- Geometry: desktop sidebar sits at (16px,16px), main starts at 288px; collapsed
  navigation is 72px wide and main starts at 96px. Mobile content starts at zero,
  closed navigation ends at zero, and the open drawer spans 256px.
- Responsive behavior: desktop 1440×1000 and mobile 390×844 were inspected for
  home, login and dashboard. English home also fits at 320×740. No horizontal
  overflow; balances, costs and token counts remain visible, with mobile wrapping.
- Interaction: homepage CTA reaches login; password reveal works; fixture-backed
  login reaches dashboard. Theme switching, navigation collapse/expand and mobile
  menu navigation to API keys work. Live backend integration was not exercised.

Validation: 199 existing auth/home/navigation/dashboard/router tests, the build's
3 locale checks, changed-file ESLint, and production build pass. Screenshot review
caught the dark border override; the affected scoped selectors were corrected and
the production bundle rebuilt. No remaining deviations from the written brief
other than using code-native design instead of an unavailable generated concept.
