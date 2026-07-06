#!/usr/bin/env python3
"""Inject the PostHog analytics snippet into a built Dashdown site.

Dashdown's page template has no head-injection hook, so we add analytics as a
post-build step: walk the static export and insert the PostHog loader right
before each page's </head>.

Config comes from env vars (set them on the repo — key as a secret, host as a
variable):
  POSTHOG_KEY   PostHog *project* API key (phc_...). Public/write-only — safe to ship.
  POSTHOG_HOST  API host. Default https://us.i.posthog.com (use https://eu.i.posthog.com for EU).

If POSTHOG_KEY is unset/empty the script is a no-op (so the build never breaks
before analytics is configured).
"""

import os
import sys
from pathlib import Path

# Official PostHog web snippet (queues calls until array.js loads), with the
# project key and host filled in below.
SNIPPET = """<!-- PostHog analytics (injected at build time) -->
<script>
  !function(t,e){{var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){{function g(t,e){{var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){{t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){{var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e}},u.people.toString=function(){{return u.toString(1)+".people (stub)"}},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug getPageViewId captureTraceFeedback captureTraceMetric".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])}},e.__SV=1)}}(document,window.posthog||[]);
  posthog.init('{key}', {{api_host:'{host}', person_profiles:'identified_only', defaults:'2025-05-24'}})
</script>
"""


def main() -> int:
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    key = os.environ.get("POSTHOG_KEY", "").strip()
    host = os.environ.get("POSTHOG_HOST", "").strip() or "https://us.i.posthog.com"

    if not key:
        print("POSTHOG_KEY not set — skipping analytics injection.")
        return 0

    snippet = SNIPPET.format(key=key, host=host)
    pages = sorted(dist.rglob("*.html"))
    injected = 0
    for page in pages:
        html = page.read_text(encoding="utf-8")
        if "posthog.init(" in html:  # idempotent — don't double-inject
            continue
        if "</head>" not in html:
            continue
        page.write_text(html.replace("</head>", snippet + "</head>", 1), encoding="utf-8")
        injected += 1

    print(f"Injected PostHog into {injected}/{len(pages)} page(s) (host {host}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
