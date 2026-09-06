# Data dictionary

Three raw files, three grains. All CMS columns are 2024 full-year aggregates: no claim dates,
no individual claims, no diagnoses.

## provider (MUP_PHY_R26_P05_V10_D24_Prov.csv), one row per NPI, 1.30M rows

Annual summary for every clinician or organization that billed Medicare Part B fee-for-service.

### Identity and location
| column | meaning |
|---|---|
| Rndrng_NPI | National Provider Identifier. Primary key, join key to LEIE |
| Rndrng_Prvdr_Last_Org_Name | Last name (individual) or organization name |
| Rndrng_Prvdr_First_Name, _MI | First name, middle initial. Blank for organizations |
| Rndrng_Prvdr_Crdntls | Credentials as enrolled, e.g. M.D., NP |
| Rndrng_Prvdr_Ent_Cd | I = individual, O = organization |
| Rndrng_Prvdr_St1, _St2, _City, _Zip5 | Practice address |
| Rndrng_Prvdr_State_Abrvtn, _State_FIPS | State as letters and federal numeric code |
| Rndrng_Prvdr_RUCA, _RUCA_Desc | Rural-urban commuting area code and label |
| Rndrng_Prvdr_Cntry | Country, nearly always US |
| Rndrng_Prvdr_Type | Billing specialty. Peer-group key |
| Rndrng_Prvdr_Mdcr_Prtcptg_Ind | Y if provider accepts Medicare fee schedule as full payment |

### Yearly totals, all services
| column | meaning |
|---|---|
| Tot_HCPCS_Cds | Distinct procedure codes billed |
| Tot_Benes | Distinct beneficiaries served |
| Tot_Srvcs | Total services billed |
| Tot_Sbmtd_Chrg | Dollars the provider asked for |
| Tot_Mdcr_Alowd_Amt | Dollars Medicare agreed to, including patient share |
| Tot_Mdcr_Pymt_Amt | Dollars Medicare actually paid |
| Tot_Mdcr_Stdzd_Amt | Payment with geographic price adjustment removed |

### Same seven measures split by drug vs. medical
| column | meaning |
|---|---|
| Drug_Tot_HCPCS_Cds ... Drug_Mdcr_Stdzd_Amt | The seven totals, drug codes only |
| Med_Tot_HCPCS_Cds ... Med_Mdcr_Stdzd_Amt | The seven totals, non-drug services only |
| Drug_Sprsn_Ind, Med_Sprsn_Ind | Suppression flag: group blanked when under 11 beneficiaries |

### Beneficiary demographics (counts)
| column | meaning |
|---|---|
| Bene_Avg_Age | Mean patient age |
| Bene_Age_LT_65_Cnt, _65_74_Cnt, _75_84_Cnt, _GT_84_Cnt | Patients per age band. Under 65 = disability or ESRD |
| Bene_Feml_Cnt, Bene_Male_Cnt | Sex counts |
| Bene_Race_Wht_Cnt, _Black_Cnt, _API_Cnt, _Hspnc_Cnt, _NatInd_Cnt, _Othr_Cnt | Race/ethnicity counts per enrollment records |
| Bene_Dual_Cnt, Bene_Ndual_Cnt | Patients with and without Medicaid dual eligibility |

### Beneficiary chronic conditions (percent of panel)
| column | meaning |
|---|---|
| Bene_CC_BH_*_Pct (11) | Behavioral: ADHD/conduct, alcohol/drug, tobacco, Alzheimer's/dementia, anxiety, bipolar, mood, depression, personality, PTSD, schizophrenia/psychosis |
| Bene_CC_PH_*_Pct (15) | Physical: asthma, afib, cancer (6 types), CKD, COPD, diabetes, heart failure, hyperlipidemia, hypertension, ischemic heart, osteoporosis, Parkinson's, arthritis, stroke/TIA |
| Bene_Avg_Risk_Scre | Mean HCC risk score. 1.0 = national average. High billing with low risk score is a red flag |

## provider_service (PHY_R26_P05_V10_D24_Prov_Svc.csv), one row per NPI x HCPCS x place of service, 9.78M rows

Same providers broken out by what they billed. Billing mix lives here.

| column | meaning |
|---|---|
| (first 17 columns) | Identical to provider table, repeated per row. Join to provider instead |
| HCPCS_Cd | Procedure code, e.g. 99213 |
| HCPCS_Desc | Plain-English description. Embedding target for the retrieval layer |
| HCPCS_Drug_Ind | Y if the code is a drug |
| Place_Of_Srvc | F = facility, O = office. Same code pays differently in each |
| Tot_Benes | Distinct patients who received this code from this provider |
| Tot_Srvcs | Times billed |
| Tot_Bene_Day_Srvcs | Distinct patient-days billed. Tot_Srvcs much larger = repeated same-day billing |
| Avg_Sbmtd_Chrg, Avg_Mdcr_Alowd_Amt, Avg_Mdcr_Pymt_Amt, Avg_Mdcr_Stdzd_Amt | Per-service charge, allowed, paid, standardized dollars |

## leie (UPDATED.csv), one row per exclusion action, 84K rows

OIG List of Excluded Individuals and Entities. Label source only. Downloaded 2026-09-06.

| column | meaning |
|---|---|
| LASTNAME, FIRSTNAME, MIDNAME | Individual's name |
| BUSNAME | Business name when the excluded party is an entity |
| GENERAL | Broad category, e.g. IND- LIC HC SERV PRO, OTHER BUSINESS |
| SPECIALTY | OIG free-text specialty. Not aligned to CMS provider types |
| UPIN | Pre-2007 provider ID. Obsolete, nearly always blank |
| NPI | NPI, or 0000000000 when unknown. ~8.8K of 84K rows have a real one |
| DOB | Date of birth YYYYMMDD, blank for businesses |
| ADDRESS, CITY, STATE, ZIP | Last known address |
| EXCLTYPE | Statutory authority, e.g. 1128a1. Decides whether the row counts as fraud |
| EXCLDATE | Exclusion effective date YYYYMMDD. Timing filter |
| REINDATE | Reinstatement date, 00000000 if still excluded |
| WAIVERDATE, WVRSTATE | State waiver date and state, if granted |

### EXCLTYPE codes used in labeling
| code | meaning | label |
|---|---|---|
| 1128a1 | Felony, program-related crime (Medicare/Medicaid fraud) | positive |
| 1128a2 | Felony, patient abuse or neglect | positive |
| 1128a3 | Felony, healthcare fraud, any payer | positive |
| 1128a4 | Felony, controlled substances | positive |
| 1128b7 | Fraud, kickbacks, prohibited activities (civil) | positive |
| 1128b4 | License revoked or surrendered | dropped (ambiguous) |
| everything else | | dropped |
