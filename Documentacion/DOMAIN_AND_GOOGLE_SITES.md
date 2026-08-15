# Domain and Google Sites Setup

Domain purchased at Porkbun:

```text
loopnopalsolutions.xyz
```

Current public Google Site:

```text
https://sites.google.com/view/loopnopalsolutions/history
```

## Recommended URL Plan

Use the root domain for the company website:

```text
https://www.loopnopalsolutions.xyz
```

Use a subdomain for the live traffic simulation:

```text
https://simulation.loopnopalsolutions.xyz
```

## Connect the Domain to Google Sites

1. Open Google Sites.
2. Open the Loop Nopal Solutions site.
3. Click Settings.
4. Go to Custom domains.
5. Add `www.loopnopalsolutions.xyz`.
6. Google will ask you to verify domain ownership.
7. In Porkbun DNS, add the TXT verification record Google provides.
8. Return to Google Sites and finish verification.
9. In Porkbun DNS, add this CNAME:

```text
Type: CNAME
Host: www
Answer/Value: ghs.googlehosted.com
TTL: Automatic or 3600
```

10. Publish the site again.

Google Sites custom URLs require a subdomain such as `www`. To make the root domain
`loopnopalsolutions.xyz` work too, use Porkbun URL forwarding from the root domain to
`https://www.loopnopalsolutions.xyz/`.

## Point the Simulation Subdomain

After deploying `Website/Site/` to a static host, create a DNS record in Porkbun:

```text
Type: CNAME
Host: simulation
Answer/Value: your-static-host-target
TTL: Automatic
```

Examples of possible static hosts:

```text
GitHub Pages
Cloudflare Pages
Netlify
Vercel
```

## Add the Square Simulation Link in Google Sites

1. Open the Google Site page where the link should appear.
2. Click Insert.
3. Choose Embed.
4. Choose Embed code.
5. Paste the contents of `Website/google-sites-square-link.html`.
6. Confirm that the button opens:

```text
https://simulation.loopnopalsolutions.xyz/
```

7. Publish the Google Site.
