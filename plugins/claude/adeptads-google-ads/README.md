# AdeptAds Google Ads

**Your next Google Ads campaign starts in Claude.**

AdeptAds multi-agent workflows turn your website and brief into Google Ads campaigns, with research, strategy, targeted groups, ad copy and creative assets where supported. Create and expand campaigns, start or pause serving, change daily budgets and bidding, and inspect performance from your agent.

Sign in through AdeptAds OAuth, connect Google, and select the intended account. New campaigns are created paused and start serving only after you confirm. UNIT/CONTENT expansion publishes to Google Ads. Geographic expansion returns a proposal for dashboard approval before publishing. Existing AdeptAds credits and billing apply; Google ad spend is separate. Autopilot setup is outside this package.

Source: https://github.com/adeptads/agent-skills

AdeptAds emails the account owner about agent-triggered starts, bidding strategy changes, removed limits, large spend-related increases, and changes it could not verify. Alerts do not replace your approval.

Free to install. Campaign workflows use your available AdeptAds credits and plan allowances. Google ad spend is separate.

[Privacy](https://www.adeptads.ai/privacy-policy) · [MIT license](LICENSE)

The license covers this client package. The hosted AdeptAds service remains subject to its own terms and billing.

Installation:

```sh
claude plugin marketplace add adeptads/agent-skills
claude plugin install adeptads-google-ads@adeptads
```

Start a new session and use `/mcp` to complete AdeptAds OAuth sign-in.
