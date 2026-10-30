# Baba Memes Tracker

A phone-friendly site that shows the Baba Memes Page followers, views and posting schedule.
It re-reads Facebook every 30 minutes on GitHub and the page reloads itself every 10 or 30
minutes (or on the "Refresh now" button).

Files: `index.html` (the site), `data.json` / `history.json` (numbers, written by the job),
`schedule.json` (the queued reels), `scripts/fetch_stats.py` (reads the Graph API),
`.github/workflows/update.yml` (runs every 30 minutes and publishes the site).

## One-time setup

1. **GitHub repo**: create a public repository (for example `baba-memes-tracker`) and push this folder.
2. **Turn on the site**: repo Settings, Pages, Source = GitHub Actions. The link is
   `https://<your-github-name>.github.io/<repo-name>/`.
3. **Meta developer app**: at developers.facebook.com create an app (type Business), add the
   Pages API, and in the Graph API Explorer make a User token with `pages_show_list`,
   `pages_read_engagement`, `read_insights`. Exchange it for a long-lived token, then call
   `me/accounts` to get the Page token for Baba Memes (Page tokens made from a long-lived user
   token do not expire).
4. **Add to GitHub** (repo Settings, Secrets and variables, Actions):
   - Variable `FB_PAGE_ID` = `100085147324156`
   - Secret `FB_PAGE_TOKEN` = the Page token. Never put it in a file or in the repo.
5. Actions tab, "Update and publish tracker", Run workflow. After that it runs every 30 minutes.

## Notes

- GitHub can delay scheduled runs by a few minutes, and pauses them if a repo has no activity for 60 days.
- If a metric name has changed on Facebook's side, the site lists it under "Some numbers could not be read"
  and keeps the last good value; followers still update.
- `schedule.json` is updated when new reels are queued; the site marks a reel "Went live" once its time passes.
- The repo is public, so keep only numbers and the schedule in it.
