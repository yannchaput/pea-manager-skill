# PEA Eligibility Reference

## Eligible Domiciles

| Status | Countries/Regions |
|--------|-------------------|
| **EU (eligible)** | AT, BE, BG, HR, CY, CZ, DK, EE, FI, FR, DE, GR, HU, IE, IT, LV, LT, LU, MT, NL, PL, PT, RO, SK, SI, ES, SE |
| **EEA (eligible)** | IS, LI, NO (+ all EU) |
| **French overseas (eligible)** | GP, MQ, GF, RE, YT, PM, BL, MF, NC, PF, WF, TF |
| **Not eligible** | US, CH, UK (post-Brexit), JP, CN, CA, AU, HK, SG, etc. |

## Key Rules

- **Synthetic swap ETFs** domiciled in eligible countries (e.g., Ireland IE, Luxembourg LU) are PEA-eligible even when tracking US indices — they use derivatives rather than holding US securities directly
- **UK-domiciled** stocks/ETFs: not eligible post-Brexit unless a specific bilateral agreement applies
- **Verify with ISIN**: the first two characters of the ISIN identify the country of domicile (FR = France, IE = Ireland, LU = Luxembourg, etc.)
- **ISIN prefix is a first-pass filter only**: eligibility also depends on the issuer's registered office and tax status. A few EU-ISIN stocks are *not* eligible (e.g. Ahold Delhaize NL0011794037 was flagged non-eligible by the user's broker on 2026-10-15). **Always confirm in the broker's PEA-eligible flag before recommending a buy** — prefer French (FR) issuers when eligibility is unverified.
- **PEA tax**: nothing is due on a sale inside the plan. On a withdrawal the plan's net gain (value minus contributions) is charged: after 5 years, 18.6% social charges and no income tax (rate since 2026-01-01, LFSS 2026); before 5 years, 31.4% PFU (12.8% + 18.6%) and the withdrawal closes the plan, save legal exceptions. Rates checked 2026-11-15 on secondary sources and service-public.gouv.fr F2385 (closure rule)
- **Contribution limit**: €150,000 per plan

## Quick Eligibility Check

1. Get the ISIN for the stock/ETF
2. Check the first two characters against the eligible countries table above
3. If ISIN starts with a code from EU, EEA, or French overseas → eligible
4. If ISIN starts with US, CH, UK, JP, CN, CA, AU, HK, SG → NOT eligible
5. For ETFs tracking US indices: if domiciled in IE or LU with "swap" or "synthétique" in the name → eligible
