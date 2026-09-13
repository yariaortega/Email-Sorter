import re
import dns.resolver
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_FILE = "union.txt"
OUTPUT_FILE = "office_emails.txt"

# Read and parse the UTF-16LE file
with open(INPUT_FILE, 'r', encoding='utf-16le') as f:
    content = f.read()

# Extract all email addresses
emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
unique_emails = sorted(set(emails))

# Group emails by domain
domain_to_emails = {}
for email in unique_emails:
    domain = email.split('@')[1].lower()
    domain_to_emails.setdefault(domain, []).append(email)

domains = list(domain_to_emails.keys())
print(f"Found {len(unique_emails)} unique emails across {len(domains)} domains.")

# OFFICE / RZONE indicators in MX records
STRATO_KEYWORDS = ['outlook']

def check_domain(domain):
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 2
        resolver.lifetime = 2
        answers = resolver.resolve(domain, 'MX')
        mx_records = [str(rdata.exchange).rstrip('.').lower() for rdata in answers]
        for mx in mx_records:
            if any(kw in mx for kw in OFFICE_KEYWORDS):
                return (domain, True, mx_records)
        return (domain, False, mx_records)
    except Exception:
        return (domain, False, None)

# Run threaded MX lookups
office_domains = set()
results = []

with ThreadPoolExecutor(max_workers=50) as executor:
    futures = {executor.submit(check_domain, d): d for d in domains}
    for i, future in enumerate(as_completed(futures)):
        if i % 500 == 0:
            print(f"Progress: {i}/{len(domains)} domains checked...")
        domain, is_office, mx_records = future.result()
        if is_office:
            office_domains.add(domain)

# Collect all emails for OFFICE-hosted domains
office_emails = []
for domain in office_domains:
    office_emails.extend(domain_to_emails[domain])

office_emails = sorted(set(office_emails))

# Write output file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for email in office_emails:
        f.write(email + '\n')

print(f"\nDone! Found {len(office_emails)} email addresses hosted on OFFICE.")
print(f"Results saved to: {OUTPUT_FILE}")