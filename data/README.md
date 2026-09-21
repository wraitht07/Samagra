# BIS Standards High-Quality Evaluation Dataset

Curated dataset of **360** Indian Standards (IS) focused on procurement, certification and common tender errors.

## Directory Structure

```
data/
├── standards.json              # 360 cleaned, domain-tagged standards (core corpus)
├── relationships.json          # Cross-standard relationships (supersession, code-vs-product, sibling parts)
├── regulations.json            # Key QCOs / Orders that make standards mandatory
├── evaluation_queries.json     # 10 hard evaluation questions with expected answers & traps
├── audit_cases.json            # 10 realistic tender audit / defect cases
├── sample_tenders/
│   ├── concrete_aggregate_tender.txt
│   ├── protective_helmet_tender.txt
│   └── industrial_valve_tender.txt
└── README.md
```

## Domain Coverage

| Domain                    | Approx. Count |
|---------------------------|---------------|
| Civil Engineering         | ~153          |
| Mechanical Engineering    | ~55           |
| Electrical Engineering    | ~50           |
| Electronics & IT          | ~17           |
| Chemical Engineering      | ~25           |
| Environmental Engineering | ~25           |
| Food & Agriculture        | ~17           |
| Textile Engineering       | ~15           |
| Automotive Engineering    | ~3            |

## Intentionally Included “Nasty” / Edge Cases

| Standard                  | Trap                                      |
|---------------------------|-------------------------------------------|
| IS 456:2000               | Code of practice treated as product       |
| IS 1786:2008 vs 1985      | Edition + Fe500 / Fe500D grade confusion  |
| IS 383:2016               | Ambiguous certification status            |
| IS 13252 (Part 1):2010    | CRS (R-number) vs Scheme-I ISI Mark       |
| IS 16046 Part 1 vs Part 2 | Nickel vs Lithium battery mix-up          |
| IS 4151:2015              | Amendments ignored in BOQs                |
| IS 14756:2024             | Standard year vs QCO date mismatch        |
| IS 1417:2016              | Hallmarking ≠ Scheme-I ISI                |
| IS 302 (Part 1):2008/2024 | Major edition change + MSME deadlines     |
| IS 2062:2011              | Wrong year / missing quality class        |
| IS 10500:2012             | Water quality spec treated as product mark|
| IS 2190 vs IS 15683       | Code of practice vs product standard      |

## Quality Rules Applied

- All synthetic / demo records removed
- Internal duplicates and cross-file overlaps collapsed
- Scope length and verification flags used as quality filters
- Certification type (Scheme-I / CRS / Hallmarking / none) explicitly recorded
- Mandatory status left `null` when genuinely ambiguous

## Intended Use

- Retrieval & ranking evaluation for procurement / compliance assistants
- Detection of code-vs-product, CRS-vs-ISI, edition and grade errors
- Audit-case simulation for tender document review

Generated for strict quality over quantity (final standing: 360 records).
