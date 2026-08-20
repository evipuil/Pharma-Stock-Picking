# Manual Extraction Log — Wave 1

**Date:** 2026-08-19  
**Reviewer:** manual_curation_v1  
**Command:** `python -m src.cli apply-extractions`

## Summary

| Program | Verified studies | Rejected | Key sources |
|---------|------------------|----------|-------------|
| C014 epacadostat | 2 | 0 | PMID 20124451, 20197554 (INCB024360 xenograft) |
| C009 sacituzumab | 2 | 12 | PMID 21372224 (hRS7-SN-38/IMMU-132), 21467164 |
| C011 tivozanib | 1 | 0 | PMID 20799147 (review; xenograft in rats) |
| C007 neratinib | 6 | 2 | PMID 15173008 (breast xenograft primary) + 5 mechanism/lung |
| C005 rucaparib | 1 | 2 | PMID 20978505 (AG-014699 xenograft) |

**Total verified:** 12 animal studies  
**Leakage audit:** 10/10 passed (verified studies only)

## Quality decisions

### C009 — literature cleanup
Auto-PubMed search returned 19 papers mentioning SN-38/irinotecan generically. **All rejected** except:
- **21372224** — primary IMMU-132 (anti-Trop-2 IgG-SN-38) xenograft + monkey PK/efficacy paper (2011)
- **21467164** — combination chemoimmunotherapy including hRS7-SN-38

### C005 — post-t0 exclusion
- **24216281** rejected: PK methods paper published **2014-01-01** after t0 **2013-10-30** (look-ahead violation)

### C007 — indication mismatch flagged
- **15173008** scored highest translational relevance (HER-2 breast xenograft → NEfERT-T program)
- Lung GEMM papers retained for mechanism/replication signal but `endpoint_clinical_similarity = 0`

### Reporting gaps (NULL in database)
Across all 12 studies, **randomization, blinding, and sample size** were not reported in abstracts — stored as 0/NULL, not imputed.

## Outputs

- Structured extractions: `configs/manual_extractions.yaml`
- CSV summary: `data/processed/manual_extraction_summary.csv`
- Program aggregates updated in `program_preclinical_features`

## Re-run

```bash
python -m src.cli apply-extractions
python -m src.preclinical.export_summary
```
