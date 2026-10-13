# TrendPulse — automated YouTube trending-video website

TrendPulse is a static website designed to help visitors discover popular YouTube videos throughout the current week. It refreshes the current country-specific YouTube `mostPopular` chart approximately every six hours, regenerates crawlable HTML pages, and deploys via GitHub Pages.

**Hosting can be free.** Complete the one-time YouTube API setup, GitHub Pages setup, and Adsterra setup below. After that, the scheduled workflow handles routine updates without your intervention.

## Included

- Search-focused homepage using the phrase **YouTube trending videos this week**.
- Country charts across 52 major markets in North America, Latin America, Europe, Africa, the Middle East, and Asia-Pacific; homepage defaults to the US chart.
- Separate YouTube most-popular charts for every category the API marks assignable in each selected market, plus indexable country/category pages when that category returns videos.
- Country-specific category pages when enough videos exist in a category.
- Pre-rendered HTML, mobile-responsive layout, metadata, canonical URLs, sitemap, and `robots.txt`.
- Search, sort, YouTube thumbnail cards, direct links to original videos, and visible last-updated time.
- Three Adsterra placements: top banner, in-feed, and lower-page placement.
- Privacy policy, terms, methodology, and contact pages (owner customization required).
- Automated GitHub Actions workflow that fetches the current chart in the runner and publishes updated static pages every six hours, without committing successive snapshots to repository history.

## An important accuracy/policy note

YouTube's official `videos.list` API supports the `chart=mostPopular` chart, but does **not** provide an official seven-day ranking. TrendPulse displays the current regional chart snapshot and refreshes it throughout the week; it does not claim the returned order is an official weekly chart.

Current YouTube API developer policies also place restrictions on aggregating API data and creating derived analytics metrics. Because a custom cross-channel “views gained over seven days” score can require additional approval, it is intentionally **not** implemented in this default project. Review the [YouTube API Developer Policies](https://developers.google.com/youtube/terms/developer-policies) and [Developer Policies Guide](https://developers.google.com/youtube/terms/developer-policies-guide) before adding historical metrics, archives, or other derived scores.

## One-time setup

### 1. Upload to GitHub

Create a **public** repository (GitHub Pages is available for free public repositories), upload all files including the hidden `.github` folder, and use `main` or `master` as the default branch. Do not put your API key in any committed file.

### 2. Create the YouTube API key

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create or select a project.
2. Enable **YouTube Data API v3**.
3. Create an API key and restrict it to YouTube Data API v3 if possible.
4. In GitHub, open **Settings → Secrets and variables → Actions → New repository secret**.
5. Name the secret exactly `YOUTUBE_API_KEY` and paste the key as the value.

The key is used by the GitHub Actions runner and is not inserted into the public website HTML.

### 3. Enable GitHub Pages

Open **Settings → Pages** and set **Build and deployment → Source** to **GitHub Actions**. Then open **Actions → Update weekly trends and deploy → Run workflow**. The first run should fetch the regional charts and publish the site. Routine runs are scheduled at 17 minutes past every six hours (UTC).

If auto-detection doesn't match your public URL or you use a custom domain, add a repository Actions variable named `SITE_URL` with your canonical HTTPS URL, such as `https://example.com`. The canonical metadata and sitemap use this value, so configure it before submitting your sitemap.

### 4. Add Adsterra ads

1. Register as an Adsterra publisher and submit your public site URL for approval.
2. Choose an ad format in the Adsterra dashboard and copy the specific code they provide for the approved website.
3. Paste the code into the relevant file:
   - `ads/top.html`
   - `ads/in-feed.html`
   - `ads/sidebar.html`
4. Commit and push. The next GitHub Actions run rebuilds the website with the ad code.

The placeholders do not generate revenue. An Adsterra account, site approval, valid ad-unit code, and real human traffic are required. Don't use somebody else's ad code or artificial traffic. Review Adsterra's current publisher policies and ensure that ad/cookie disclosures and any required consent controls match your setup.

### 5. Customize policies and contact details

Before launch, edit the Privacy, Terms, and Contact text in `scripts/build_site.py` so the owner/contact details and disclosures are accurate for your setup and audience. A consent gate links to the privacy policy, YouTube Terms of Service, and Google Privacy Policy. The starter text is not legal advice.

### 6. Ask Google to discover the website

1. Add and verify the site in [Google Search Console](https://search.google.com/search-console/about).
2. Submit `https://YOUR-SITE/sitemap.xml` using your actual canonical domain.
3. Use URL Inspection to request crawling of the homepage and inspect the country/category pages after deployment.

There is no way to guarantee that Google will index the site, or rank it for **“youtube trending videos.”** It is a competitive query. Make the site worth returning to with original explanations, useful category pages, internal links, and honest data descriptions. Avoid thin, near-duplicate pages and artificial traffic.

## Regions and categories

The default configuration covers 52 markets. A refresh first asks YouTube which video categories are assignable in each country, then fetches the current most-popular chart for each of those categories. Categories with returned videos receive their own country/category page; empty categories are omitted rather than publishing empty pages. The data is replaced on each run, not archived. The larger coverage uses more YouTube Data API quota than the four-country starter setup, so monitor quota usage in Google Cloud Console after the first full run.

## How it refreshes

- GitHub Actions fetches the official current `mostPopular` chart for each configured country and each category marked assignable by YouTube for that country.
- `data/current.json` is written temporarily in the runner and is not committed to Git history; each workflow begins from the source tree and refreshes it again.
- The build script generates crawlable pages from that data and adds a sitemap and robots file.
- The Pages artifact is deployed automatically. No paid server or database is required. If a workflow run fails, the currently deployed site remains until a later successful deployment.

The workflow does not preserve historical rankings. API limits, regional chart availability, or a failed API request can delay updates. The API key is required for a populated production build. If it is missing, the local script can build an empty preview, but the scheduled production workflow should be configured with the secret and run manually once to initialize the site.

## Local build

Requirements: Python 3.10 or newer. No third-party Python packages are needed.

```bash
python scripts/build_site.py --out _site
```

To fetch fresh chart data locally, set `YOUTUBE_API_KEY` in your shell first, then run:

```bash
python scripts/update_trends.py
python scripts/build_site.py --out _site
```

Never commit the API key.

## Launch checklist

- [ ] Add `YOUTUBE_API_KEY` as a GitHub Actions secret.
- [ ] Enable GitHub Pages with GitHub Actions as the publishing source.
- [ ] Run the workflow and confirm deployment.
- [ ] Set `SITE_URL` if URL inference is incorrect or you use a custom domain.
- [ ] Submit your site to Adsterra and paste your own ad codes into `ads/*.html`.
- [ ] Update the Privacy, Terms, and Contact pages for your real site and region.
- [ ] Submit `sitemap.xml` in Google Search Console.

This is a ready-to-configure starter project, not a guarantee of ad approval, visitors, Google rankings, or earnings.
