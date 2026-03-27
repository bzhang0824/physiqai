# PhysiqAI Training Data Sources Report

**Comprehensive Research on Fitness Transformation Training Data**

*Last Updated: February 3, 2026*

---

## Executive Summary

Training a LoRA or custom diffusion model for fitness transformations requires paired before/after images with consistent quality, proper consent, and legal licensing. This report documents available sources across six categories, with recommendations prioritized by feasibility, cost, and legal compliance.

**Key Finding:** There is no readily available public dataset of fitness transformation photos. Most viable paths require either:
1. Purchasing custom data from specialized providers
2. Building partnerships with fitness apps/gyms
3. Creating synthetic data or crowdsourcing with explicit consent
4. Scraping public sources (with significant legal considerations)

---

## Table of Contents

1. [Scientific Studies & Research Papers](#1-scientific-studies--research-papers)
2. [Fitness Apps with Progress Photos](#2-fitness-apps-with-progress-photos)
3. [Academic Datasets](#3-academic-datasets)
4. [Fitness Communities & Social Media](#4-fitness-communities--social-media)
5. [Commercial Sources](#5-commercial-sources)
6. [Government & Public Health Data](#6-government--public-health-data)
7. [Synthetic Data Alternatives](#7-synthetic-data-alternatives)
8. [Legal Requirements & Compliance](#8-legal-requirements--compliance)
9. [Implementation Strategy](#9-implementation-strategy)
10. [Cost Summary](#10-cost-summary)

---

## 1. Scientific Studies & Research Papers

### Overview
Academic research occasionally includes transformation photos, but these are typically limited in scope and not designed for ML training.

### Key Studies Identified

#### Body Composition Photography Research
- **Source:** PLOS One - "A method for measuring human body composition using digital images"
- **URL:** https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0206430
- **Data:** 2D photographs used to estimate body fatness
- **Quality:** High (standardized capture methodology)
- **Access:** Contact authors for research collaboration
- **Legal:** Requires IRB approval and data sharing agreement
- **Volume:** Limited (~hundreds of subjects)

#### Cambridge 3D BodyShape Study
- **Source:** University of Cambridge - Jesus College
- **URL:** https://www.jesus.cam.ac.uk/articles/body-fat-accurately-predicted-ai-powered-smartphone-app
- **Data:** Smartphone photos used for AI body fat prediction
- **Access:** Research prototype; contact research team
- **Contact:** University of Cambridge research team

#### Instagram Transformation Photo Studies
- **Source:** Taylor & Francis - "#gainingweightiscool" study
- **URL:** https://www.tandfonline.com/doi/full/10.1080/2159676X.2020.1836511
- **Data:** Analysis of transformation photos (interview-based, not image dataset)
- **Access:** Methodological reference only

### Contacts for Academic Partnerships

| Institution | Research Focus | Contact Method |
|-------------|---------------|----------------|
| University of Cambridge | 3D body shape AI | research@jesus.cam.ac.uk |
| Washington University St. Louis | Body composition (BOD POD) | Pediatric Clinical Research Unit |
| Max Planck Institute | Human body 3D datasets | AGORA dataset team |

### Assessment
**Viability: LOW for direct data acquisition**
- Academic data is tightly controlled
- Consent typically limited to specific research purposes
- Not designed for commercial AI training
- Could be valuable for methodology and partnerships

---

## 2. Fitness Apps with Progress Photos

### Overview
Fitness apps collect the most relevant transformation data but access requires partnerships.

### Top Apps with Progress Photo Features

#### MyFitnessPal
- **Company:** Under Armour → Francisco Partners
- **User Base:** 200M+ users
- **Progress Photos:** ✅ Premium feature
- **Data Export:** CSV export for weight/nutrition; photos stay in-app
- **API:** https://www.myfitnesspal.com/api (limited public access)
- **Partnership Contact:** business@myfitnesspal.com
- **Legal:** Would require partnership agreement with explicit user consent
- **Quality:** Variable (user-submitted, no standardization)
- **Volume Potential:** HIGH (millions of transformation photos)

#### Strong App
- **Focus:** Strength training tracking
- **Progress Photos:** ✅ Available
- **API:** No public API
- **Partnership:** Direct outreach required
- **Website:** https://www.strong.app

#### JEFIT
- **Focus:** Workout tracking with community
- **Progress Photos:** ✅ Community sharing feature
- **User Base:** 10M+ downloads
- **Partnership:** business@jefit.com

#### Fitbit (Google)
- **Data:** Primarily numerical metrics
- **Progress Photos:** Limited
- **Note:** Privacy-focused; unlikely partner

### Gym Management Software

#### PerfectGym
- **URL:** https://www.perfectgym.com
- **Data:** Member photos with metrics
- **Access:** B2B partnerships with gym chains
- **Contact:** Through enterprise sales
- **Opportunity:** White-label partnerships with gym chains

#### Trainerize
- **Focus:** Personal trainer platform
- **Progress Photos:** Core feature for client tracking
- **Partnership Potential:** HIGH
- **Contact:** partners@trainerize.com

### Assessment
**Viability: MEDIUM-HIGH (requires significant business development)**
- Best source for authentic transformation data
- Requires negotiated data licensing agreements
- User consent must be explicit for AI training
- Cost likely $50K-500K+ depending on volume and terms

---

## 3. Academic Datasets

### Available Datasets

#### TrainingDataPro/UniqueData Body Measurements Dataset
- **Platform:** Hugging Face / Kaggle
- **URL:** https://huggingface.co/datasets/UniqueData/body-measurements-dataset
- **Content:** 
  - 315 sample images (full dataset requires purchase)
  - Front, side, and selfie photos per person
  - JSON files with 14 body measurements
  - Age, gender, race, profession metadata
- **Quality:** HIGH (standardized poses, good lighting)
- **Access:** 
  - Sample: FREE on Hugging Face
  - Full dataset: PAID (contact vendor)
- **Contact:** https://unidata.pro/datasets/body-measurements-image-dataset/
- **Legal:** Commercial license available
- **Volume:** ~315 subjects in sample; larger sets available
- **Limitation:** Single point-in-time (NOT transformation pairs)

#### Kaggle Body Size Dataset
- **URL:** https://www.kaggle.com/datasets/tapakah68/body-measurements-dataset
- **Content:** Body measurements and photographs
- **Access:** FREE (Kaggle account required)
- **Quality:** Variable
- **Legal:** Check individual license

#### Human Segmentation Dataset (Kaggle)
- **URL:** https://www.kaggle.com/datasets/trainingdatapro/human-segmentation-dataset
- **Content:** 6,700 photos for body segmentation
- **Use Case:** Could be useful for preprocessing/segmentation models
- **Access:** FREE

#### OpenML Body Fat Dataset
- **URL:** https://www.openml.org/d/560
- **Content:** Body composition measurements (no images)
- **Use Case:** Numerical correlation data only

### 3D Human Datasets

#### AGORA Dataset (Max Planck Institute)
- **URL:** https://agora.is.tue.mpg.de/
- **Content:** 3D human poses and body shapes
- **Access:** Research license required
- **Use Case:** Could generate synthetic transformations

#### Facebook SAM 3D Body Dataset
- **URL:** https://huggingface.co/datasets/facebook/sam-3d-body-dataset
- **Content:** Full-body human mesh recovery
- **Access:** Research purposes

#### HumanDataset.com
- **URL:** https://humandataset.com/
- **Content:** 35,000+ scanned human 3D models
- **Pricing:** Commercial licensing available
- **Contact:** Through website
- **Quality:** World's #1 cited commercial human 3D models
- **Use Case:** Generate synthetic body transformations

### Assessment
**Viability: MEDIUM**
- Existing datasets are NOT transformation pairs
- Would need to synthetically generate "before/after" from body shape models
- Good for body understanding, not direct transformation training

---

## 4. Fitness Communities & Social Media

### Reddit Communities

#### r/progresspics
- **URL:** https://www.reddit.com/r/progresspics/
- **Subscribers:** 2M+ members
- **Content:** Before/after transformation photos
- **Volume:** 10,000+ posts with paired images
- **Quality:** Variable (different lighting, poses, angles)
- **Metadata:** Often includes weight, timeframe, height

#### r/Brogress
- **URL:** https://www.reddit.com/r/Brogress/
- **Subscribers:** 500K+ members
- **Content:** Muscle-building transformations
- **Focus:** Athletic/bodybuilding transformations

#### r/loseit
- **Content:** Weight loss journeys (some photos)

### Legal Considerations for Reddit

**Reddit API & Terms:**
- Reddit API requires approval for large-scale access
- Terms prohibit systematic data collection without permission
- Personal images are covered by user privacy expectations
- **hiQ Labs v. LinkedIn** case suggests public data scraping may be legal, but:
  - Photos contain personal biometric data (faces, bodies)
  - GDPR and US state privacy laws apply
  - No consent for AI training use

**Ethical Concerns:**
- Users posted for community support, not AI training
- Reputational risk if discovered
- Potential backlash from fitness community

### Web Scraping Approach (If Pursued)

| Consideration | Details |
|--------------|---------|
| Technical | Python + PRAW library or Pushshift API |
| Rate Limiting | Reddit enforces strict limits |
| Filtering | Need to filter for quality, paired images |
| Estimated Volume | 50K-100K paired images possible |
| Quality Score | 3/10 (inconsistent) |
| Legal Risk | HIGH |
| Recommendation | **NOT RECOMMENDED for commercial use** |

### Instagram & TikTok

**#transformation hashtags:**
- Millions of posts available
- Meta/TikTok actively prohibit scraping
- Legal risk: VERY HIGH
- Recommendation: **AVOID**

### Assessment
**Viability: LOW (legal risk outweighs benefits)**
- Large volume available
- Inconsistent quality makes training difficult
- No consent for AI training
- Recommend exploring only if building a public, research-focused dataset with proper disclosure

---

## 5. Commercial Sources

### Stock Photo Services

#### Getty Images
- **URL:** https://www.gettyimages.com/photos/body-transformation
- **Content:** 4,558+ "body transformation" results
- **Quality:** Professional photography
- **License:** Extended license required for AI training
- **Pricing:** $499+ per image for extended/AI training rights
- **Bulk:** Contact for enterprise pricing
- **Limitation:** Often posed models, not real transformations

#### Shutterstock
- **URL:** https://www.shutterstock.com/search/gym-before-after
- **Content:** Thousands of fitness-related images
- **License:** Standard license does NOT cover AI training
- **AI Training:** Requires separate negotiation
- **API:** Available for enterprise
- **Contact:** enterprise@shutterstock.com

#### Freepik
- **URL:** https://www.freepik.com/free-photos-vectors/fitness-transformation-before-after
- **Content:** Free and premium fitness images
- **License:** Attribution required for free; check AI training rights
- **Quality:** Mixed (includes vectors, not just photos)

#### Unsplash
- **URL:** https://unsplash.com/s/photos/personal-trainer
- **Content:** Free high-quality photos
- **License:** Unsplash License (very permissive)
- **AI Training:** Generally allowed
- **Limitation:** Generic fitness photos, not transformation pairs

### AI Training Data Providers

#### Scale AI
- **URL:** https://scale.com/
- **Service:** Custom data collection and labeling
- **Pricing:** Enterprise (contact for quote)
- **Capability:** Can source custom fitness transformation data
- **Contact:** sales@scale.com

#### Appen
- **URL:** https://www.appen.com/ai-data/data-collection
- **Service:** Custom data collection via global contributor network
- **Features:**
  - Appen Mobile app for photo collection
  - Can collect standardized body photos
  - Proper consent management
- **Pricing:** ~$0.10-$5 per data point
- **Contact:** sales@appen.com

#### LXT (formerly Clickworker)
- **URL:** https://www.clickworker.com/ai-datasets-for-machine-learning/
- **Service:** Custom photo/video datasets
- **Quality:** Can specify requirements
- **Contact:** enterprise@lxt.ai

#### Cogito Tech
- **URL:** https://www.cogitotech.com/
- **Service:** Custom AI training data
- **Focus:** Image annotation and collection

### Custom Photography Services

#### Fitness Photographers (Direct Partnership)
Hiring photographers to create standardized datasets:

| Photographer Type | Cost Per Session | Images/Session | Notes |
|------------------|-----------------|----------------|-------|
| Local fitness photographer | $200-500 | 20-50 images | Need model releases |
| Studio partnership | $150-300/subject | Standardized | Better consistency |
| Gym partnership | Variable | Access to clients | Requires gym agreement |

**Recommended Approach:**
1. Partner with 5-10 gyms/fitness studios
2. Offer free professional photos to members
3. Collect standardized before/after over 3-6 months
4. Budget: ~$50-100 per transformation pair
5. Target: 1,000-5,000 pairs for initial training

### Assessment
**Viability: HIGH (best path for quality + legal compliance)**
- Stock photos: expensive, not real transformations
- Custom collection: most viable path
- Scale AI/Appen: expensive but legally clean
- Gym partnerships: best value for authentic data

---

## 6. Government & Public Health Data

### NHANES (National Health and Nutrition Examination Survey)

- **URL:** https://wwwn.cdc.gov/nchs/nhanes/
- **Administrator:** CDC/NCHS
- **Content:**
  - Anthropometric measurements
  - DXA body composition scans
  - NO photographs included
- **Access:** FREE public download
- **Use Case:** Correlation data for body metrics, not visual training

### NIH Visible Human Project

- **URL:** https://www.nlm.nih.gov/research/visible/visible_human.html
- **Content:** Complete cross-sectional body images
- **Access:** FREE (no license required since 2019)
- **Limitation:** Cadaver data; not applicable for transformation training

### CDC/WHO Health Studies

- Generally contain measurements only
- Photos not included in public health datasets
- Privacy regulations prevent photo sharing

### Assessment
**Viability: VERY LOW**
- Government health data does not include photographs
- Privacy regulations prevent inclusion
- Useful only for anthropometric correlations

---

## 7. Synthetic Data Alternatives

### Synthetic Data Generation

#### NVIDIA Omniverse / Isaac
- **URL:** https://www.nvidia.com/en-us/use-cases/synthetic-data/
- **Capability:** Generate photorealistic synthetic humans
- **Use Case:** Create before/after body transformations procedurally
- **Pricing:** Enterprise licensing

#### Datagen (Acquired by NVIDIA)
- **Focus:** Synthetic data for human-centric computer vision
- **Capability:** Photorealistic body simulations
- **Use Case:** Generate transformation pairs with controlled variations

#### Synthetic Approach
1. Use 3D body models (SMPL, SCAPE)
2. Parametric body modification (fat%, muscle mass)
3. Render photorealistic images with various:
   - Lighting conditions
   - Camera angles
   - Clothing/backgrounds
   - Skin tones

#### Tools for Synthetic Generation

| Tool | Use | Access |
|------|-----|--------|
| MakeHuman | Open-source 3D human generator | FREE |
| Blender + SMPL | 3D body morphing | FREE |
| Unreal MetaHumans | Photorealistic humans | FREE |
| Daz3D | Commercial 3D characters | $50-500 |

### Hybrid Approach (Recommended)
1. Collect 500-1,000 real transformation pairs
2. Generate 10,000-50,000 synthetic variations
3. Fine-tune model on real data
4. Use synthetic to prevent overfitting

### Assessment
**Viability: HIGH (complement to real data)**
- Can generate unlimited training data
- Controlled variation (lighting, pose, body type)
- Legal: No consent issues with synthetic humans
- Limitation: May not capture real-world nuances

---

## 8. Legal Requirements & Compliance

### GDPR (EU)

| Requirement | Details | PhysiqAI Impact |
|-------------|---------|-----------------|
| Explicit Consent | Required for AI training use | Must document consent |
| Right to Erasure | Users can request data deletion | Need data management system |
| Data Minimization | Collect only necessary data | Don't over-collect metadata |
| Special Categories | Body images may be biometric | Higher protection needed |

### US Privacy Laws

#### California (CCPA/CPRA)
- Explicit consent for AI training required
- Right to deletion applies
- Sensitive data (body images) has extra requirements

#### Other States (Virginia, Colorado, etc.)
- Similar consent requirements
- Opt-out rights for data sales

### Model Release Requirements

For any collected photos:
```
Required Release Elements:
1. Full name and signature
2. Specific grant for AI/ML training
3. Commercial use permission
4. Duration (perpetual recommended)
5. Territory (worldwide)
6. Description of use
```

### AI Training Specific Considerations

| Scenario | Legal Requirement |
|----------|------------------|
| Public Reddit photos | Still requires consent for AI training |
| Stock photos | Check if license covers AI training |
| User-submitted with consent | Document and verify consent |
| Synthetic data | No consent needed |
| Academic datasets | Check specific license terms |

### Recommended Legal Framework

1. **Privacy Policy:** Explicitly state AI training use
2. **Consent Form:** Separate opt-in for AI training
3. **Model Release:** Professional photography standard
4. **Data Processing Agreement:** With any data providers
5. **Legal Counsel:** Review before large-scale collection

---

## 9. Implementation Strategy

### Phase 1: Foundation (Months 1-3)
**Budget: $15,000-25,000**

1. **Acquire existing datasets**
   - UniqueData body measurements: ~$5,000-10,000
   - Stock photos (limited): ~$2,000
   
2. **Set up synthetic pipeline**
   - MakeHuman + Blender: FREE
   - Generate 10,000 synthetic pairs
   - Estimated effort: 2-4 weeks dev time

3. **Legal preparation**
   - Draft model release forms
   - Privacy policy updates
   - Legal review: ~$3,000-5,000

### Phase 2: Partnership Development (Months 2-6)
**Budget: $50,000-150,000**

1. **Gym/Trainer Partnerships**
   - Target: 10-20 fitness facilities
   - Offer: Free professional photos for members
   - Exchange: Consent for AI training use
   - Expected yield: 500-2,000 transformation pairs
   
2. **Fitness App Outreach**
   - Contact MyFitnessPal, Trainerize, JEFIT
   - Propose data licensing pilot
   - Budget for licensing: $20,000-100,000

3. **Crowdsourced Collection**
   - Platform: Custom app or Appen/Scale
   - Compensation: $10-50 per transformation pair
   - Target: 1,000 pairs
   - Budget: $15,000-50,000

### Phase 3: Scale (Months 6-12)
**Budget: $100,000-500,000**

1. **Expand partnerships**
   - National gym chains (24 Hour, Planet Fitness)
   - Online fitness platforms (Beachbody, Peloton)
   
2. **Professional data collection**
   - Scale AI or Appen custom project
   - Target: 10,000+ high-quality pairs
   
3. **Model training and iteration**
   - Use collected data for LoRA fine-tuning
   - Iterate based on results

### Recommended Data Mix

| Source | Percentage | Volume Target |
|--------|------------|---------------|
| Synthetic data | 50% | 25,000 pairs |
| Gym partnerships | 25% | 5,000 pairs |
| Licensed/purchased | 15% | 3,000 pairs |
| Crowdsourced | 10% | 2,000 pairs |
| **Total** | **100%** | **35,000 pairs** |

---

## 10. Cost Summary

### Low Budget Path (~$25,000)
- Synthetic data generation: $5,000 (dev time)
- Small purchased dataset: $10,000
- Legal setup: $5,000
- Small crowdsource pilot: $5,000
- **Result:** Proof of concept, limited quality

### Medium Budget Path (~$100,000)
- Everything above: $25,000
- Appen/Scale collection (2,000 pairs): $40,000
- Gym partnership program: $20,000
- Extended synthetic data: $10,000
- Legal/compliance: $5,000
- **Result:** Production-quality dataset

### Enterprise Path (~$500,000+)
- Full Scale AI custom project: $200,000+
- Major app partnership: $100,000+
- National gym chain deals: $100,000+
- Professional data management: $50,000
- Legal/compliance: $50,000
- **Result:** Industry-leading dataset

---

## Appendix A: Contact List

### Data Providers
| Company | Contact | Purpose |
|---------|---------|---------|
| UniqueData | https://unidata.pro | Body measurements dataset |
| Scale AI | sales@scale.com | Custom collection |
| Appen | sales@appen.com | Crowdsourced collection |

### Fitness Platforms
| Company | Contact | Opportunity |
|---------|---------|-------------|
| MyFitnessPal | business@myfitnesspal.com | Data licensing |
| Trainerize | partners@trainerize.com | Trainer platform data |
| JEFIT | business@jefit.com | Progress photos |

### Research Institutions
| Institution | Department | Contact |
|-------------|------------|---------|
| Cambridge University | AI Research | Research office |
| Max Planck Institute | Computer Vision | AGORA team |

---

## Appendix B: Model Release Template

```
RELEASE AND CONSENT FOR AI TRAINING

I, ________________________, grant [PhysiqAI/Company Name] permission to:

1. Photograph my body before and after fitness transformation
2. Use these photographs to train artificial intelligence models
3. Use resulting AI models for commercial purposes
4. Retain photographs indefinitely for ongoing training

I understand that:
- My likeness may influence AI-generated images
- My actual photographs will not be publicly shared
- I can request data deletion at any time
- No individual photos will be identifiable in the final model

I am over 18 years of age and sign voluntarily.

Signature: ___________________ Date: ___________
Print Name: __________________
Email: ______________________
```

---

## Appendix C: Technical Requirements for Training Data

### Image Specifications

| Attribute | Minimum | Recommended |
|-----------|---------|-------------|
| Resolution | 512x512 | 1024x1024+ |
| Format | JPEG | PNG (lossless) |
| Lighting | Even | Studio quality |
| Background | Clean | Consistent/removable |
| Pose | Front/side | Multiple angles |

### Metadata Requirements
- Subject ID (anonymized)
- Before/after label
- Time between photos
- Body metrics (if available)
- Age, gender (for stratification)

### Quality Control Checklist
- [ ] Full body visible
- [ ] Face visible or consistently obscured
- [ ] No watermarks or text
- [ ] Similar pose in before/after
- [ ] Adequate lighting
- [ ] Sharp focus
- [ ] No clothing obscuring body shape significantly

---

*Report compiled February 2026. Data sources and pricing subject to change.*
