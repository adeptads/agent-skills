![AdeptAds](assets/logo.svg)

# AdeptAds Google Ads

**Your next Google Ads campaign starts in Claude.**

Bring your website, a goal and a budget. Claude works with AdeptAds to turn your brief into a campaign.

AdeptAds multi-agent workflows research your offer, plan targeted ad groups, write the ads and create images where the campaign needs them. Build Search, Display or Performance Max campaigns in your chosen Google Ads account. New campaigns arrive paused. You look them over and decide when they go live.

Already running ads? Add groups, keywords, search themes or locations. Check results, pause campaigns, or change budgets and bidding from the same conversation. Additions to a running campaign can go live immediately; new locations wait for your approval in the AdeptAds dashboard.

Free to install. You need an AdeptAds account, connected Google Ads access and available trial or paid-plan credits. Google ad spend is separate. Autopilot setup stays in the AdeptAds dashboard.

### Try it

- "Build a Search campaign for my website. Help me choose the audience and budget."
- "Find useful keywords to add to this campaign. Show me the scope before making changes."
- "Show my campaign results for the last 30 days and suggest what to do next."

### Get connected

```sh
claude plugin marketplace add adeptads/agent-skills
claude plugin install adeptads-google-ads@adeptads
```

Start a new session and use `/mcp` to complete AdeptAds OAuth sign-in.

Connect Google in AdeptAds and choose the intended Google Ads account before making changes.

### Your data and control

This package connects your agent to the hosted AdeptAds MCP service at https://api.adeptads.ai/mcp. Your requests and relevant account and campaign context are sent to AdeptAds to run the selected tools and workflows against your connected Google Ads account. Authentication uses AdeptAds OAuth; keep credentials out of chat.

AdeptAds emails the account owner about agent-triggered starts, bidding strategy changes, removed limits, large spend-related increases, and changes it could not verify. Alerts do not replace your approval.

[Support](https://www.adeptads.ai/#about-contact) · [Privacy](https://www.adeptads.ai/privacy-policy) · [Terms](https://www.adeptads.ai/terms-of-service) · [Source](https://github.com/adeptads/agent-skills) · [MIT license](LICENSE)

The license covers this client package. The hosted AdeptAds service remains subject to its own terms and billing.
