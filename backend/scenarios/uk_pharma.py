"""
scenarios/uk_pharma.py — United Kingdom × Pharmaceutical (Smart Insulin Pen) scenario.

Meridian BioSciences — a Cambridge-based biotech commercializing a biosimilar
insulin with a connected smart pen. DTC advertising BANNED. NHS/NICE gatekeepers.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.uk_pharma_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


UK_PHARMA = ScenarioDefinition(
    scenario_id="uk_pharma",
    scenario_label="United Kingdom — Pharmaceutical",

    locale=LocaleConfig(
        country_code="GB", country_name="United Kingdom",
        currency_symbol="£", currency_code="GBP",
        currency_prefix=True,
        large_number_suffix="M", large_number_divisor=1_000_000,
    ),

    company=CompanyConfig(
        name="Meridian BioSciences",
        product_name="Meridian IntelliPen Smart Insulin System",
        tagline="Connected insulin delivery for the NHS and beyond",
        location="Cambridge, United Kingdom",
        role_title="VP of Finance & Strategy",
        founding_year="2020",
        industry_label="Pharmaceutical — Insulin Delivery",
        unit_price=2_800.0,         # £2,800/patient/yr (NHS negotiated price)
        unit_price_label="Annual Therapy Cost",
        unit_cost=950.0,
        year1_capacity=7_000,
        capacity_unit="patients",
    ),

    financials=FinancialConfig(
        total_budget=18_000_000,
        fixed_costs=27_000_000,
        base_revenue=10_000_000,
        profit_reinvestment_rate=0.03,
        inflation_min=0.04,
        inflation_max=0.10,
        underuse_threshold=0.15,
        underuse_penalty_rate=2.5,
        max_change_rate=0.30,
        demand_noise_std=0.08,
        scenario_drift_std=0.03,
        risk_penalty_lambda=1.5,
        num_periods=5,
        num_eval_scenarios=30,
        state_decay=0.5,
        vpi_ras_floor=-2_986_320,
        vpi_ras_ceiling=13_475_600,
        vpi_share_floor=21.24,
        vpi_share_ceiling=26.4,
        competitor_presence_baseline=120_000_000,
    ),

    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    departments=[
        DepartmentParams(
            name="R&D", S_max=25_000_000, K=5_400_000, alpha=1.3,
            decay=0.55, min_spend=1_100_000, max_spend=9_000_000,
            state_sensitivity=0.12, catch_up_rate=0.25, sweet_spot_frac=0.70,
        ),
        DepartmentParams(
            name="Sales", S_max=18_000_000, K=4_300_000, alpha=0.9,
            decay=0.20, min_spend=1_400_000, max_spend=9_000_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Operations", S_max=21_000_000, K=3_200_000, alpha=0.85,
            decay=0.55, min_spend=1_100_000, max_spend=7_200_000,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Marketing", S_max=20_000_000, K=4_000_000, alpha=1.05,
            decay=0.40, min_spend=900_000, max_spend=7_200_000,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.65,
        ),
    ],

    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd", description=(
            "R&D drives clinical evidence, device innovation, and MHRA filings. Returns are "
            "DELAYED by one year. In the UK, NICE technology appraisals require robust clinical "
            "data — R&D synergy with Sales is the most important relationship in the game."
        ),
            background_description="R&D conducts clinical trials at NHS centres, develops the pen platform with NHS App integration, manages MHRA regulatory submissions, and builds digital health features.",
        ),
        DepartmentMeta(
            name="Sales", color_key="dept_sales", description=(
            "Sales covers NHS trust relationships, NICE submissions, and pharmacy partnerships. "
            "Returns are immediate but CAPPED by Operations. Losing an NHS formulary position "
            "is extremely hard to reverse."
        ),
            background_description="Sales manages NHS trust formulary access, NICE submission support, pharmacy chain partnerships, and patient enrollment through the UK healthcare system.",
        ),
        DepartmentMeta(
            name="Operations", color_key="dept_ops", description=(
            "Operations is the BOTTLENECK. MHRA GMP compliance, cold-chain logistics, and "
            "post-Brexit import complications add UK-specific complexity."
        ),
            background_description="Operations runs the Cambridge GMP facility, manages cold-chain distribution across the UK, ensures MHRA compliance, and navigates post-Brexit import logistics.",
        ),
        DepartmentMeta(
            name="Marketing", color_key="dept_mktg", description=(
            "Marketing builds physician awareness through medical education, NHS conferences, "
            "and patient support. Direct-to-consumer prescription advertising is BANNED in the UK. "
            "Your path to patients goes through the NHS and physicians. Returns follow an S-curve — below a threshold your message is lost in noise, above it you build compounding brand equity among physicians and patients."
        ),
            background_description="Marketing builds physician awareness through medical education, Diabetes UK conference sponsorships, NHS patient support programmes, and health economics research for NICE. Direct-to-consumer prescription advertising is not permitted in the UK.",
        ),
    ],

    department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    segments=[
        ConsumerSegment(key="nhsprimary", label="Public Healthcare (GP-Prescribed)",
            description="NHS primary care — the largest channel. GPs prescribe based on CCG/ICS guidelines and NICE recommendations. Volume-driven but price-controlled. Represent ~40% of the market.",
            market_weight=0.40),
        ConsumerSegment(key="nhshospital", label="Hospital Procurement",
            description="NHS hospital trusts purchasing through NHS Supply Chain. Standardise on one pen for inpatient use. Clinical evidence and reliability critical. Represent ~25% of the market.",
            market_weight=0.25),
        ConsumerSegment(key="nice", label="National Treatment Guidelines",
            description="NICE recommended pathway — getting onto the NICE-approved treatment list is the single most impactful commercial milestone. Affects all NHS prescribing. Represent ~20% of the market.",
            market_weight=0.20),
        ConsumerSegment(key="private", label="Private Clinics & Insurance",
            description="Bupa, private clinics, and self-pay patients. Small but higher-margin channel. Less price-sensitive, more feature-driven. Represent ~15% of the market.",
            market_weight=0.15),
    ],

    segment_colors={"nhsprimary": "#3D6B50", "nhshospital": "#4A7B9D", "nice": "#C27D3A", "private": "#8B6BAE"},

    sub_decisions={
        "R&D": DepartmentSubDecisions(
            dept_name="R&D", label="R&D Focus",
            tooltip="Choose your clinical and device priority.",
            options={
                "clinical": SubDecisionOption(key="clinical", label="NHS Clinical Outcomes Studies",
                    description="Run real-world evidence trials at NHS centres for NICE technology appraisal submission.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Sales": 0.12, "Marketing": 0.03},
                    segment_multipliers={"nhsprimary": 1.25, "nhshospital": 1.30, "nice": 1.45, "private": 0.85}),
                "device": SubDecisionOption(key="device", label="Smart Pen Device Innovation",
                    description="Improve hardware — smaller form factor, NHS App integration, CGM connectivity.",
                    smax_mult=1.25, k_mult=1.30, synergy={"Marketing": 0.10},
                    segment_multipliers={"nhsprimary": 0.95, "nhshospital": 0.90, "nice": 1.05, "private": 1.45}),
                "costreduce": SubDecisionOption(key="costreduce", label="Manufacturing Cost Reduction",
                    description="Optimise production to lower NHS drug tariff price — critical for NICE cost-effectiveness.",
                    smax_mult=0.90, k_mult=0.75, synergy={"Operations": 0.15, "Sales": 0.05},
                    segment_multipliers={"nhsprimary": 1.35, "nhshospital": 1.20, "nice": 1.30, "private": 0.70}),
                "software": SubDecisionOption(key="software", label="Digital Health Platform",
                    description="Build NHS App integration, telehealth features, and AI dosing support.",
                    smax_mult=1.20, k_mult=1.25, synergy={"Marketing": 0.08},
                    segment_multipliers={"nhsprimary": 1.10, "nhshospital": 1.00, "nice": 1.10, "private": 1.35}),
            },
            default="clinical",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales", label="Sales Channel Strategy",
            tooltip="Sales is CAPPED by Operations.",
            options={
                "nhsformulary": SubDecisionOption(key="nhsformulary", label="NHS Formulary & NICE Submission",
                    description="Focus on NICE technology appraisals and NHS trust formulary listings.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Operations": 0.05},
                    segment_multipliers={"nhsprimary": 1.40, "nhshospital": 1.10, "nice": 1.50, "private": 0.70}),
                "hospital": SubDecisionOption(key="hospital", label="Hospital & Trust Sales",
                    description="Target NHS trust procurement and NHS Supply Chain contracts.",
                    smax_mult=1.10, k_mult=1.05, synergy={"Operations": 0.10},
                    segment_multipliers={"nhsprimary": 0.85, "nhshospital": 1.55, "nice": 1.00, "private": 0.80}),
                "patient": SubDecisionOption(key="patient", label="Patient Access & Support",
                    description="Build patient assistance and nurse educator programmes within NHS guidelines.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Marketing": 0.10},
                    segment_multipliers={"nhsprimary": 1.15, "nhshospital": 0.80, "nice": 0.95, "private": 1.35}),
                "specialist": SubDecisionOption(key="specialist", label="Specialist Engagement",
                    description="Deploy medical science liaisons to UK endocrinology and diabetes centres.",
                    smax_mult=1.05, k_mult=0.90, synergy={"R&D": 0.08},
                    segment_multipliers={"nhsprimary": 0.90, "nhshospital": 1.20, "nice": 1.15, "private": 1.20}),
            },
            default="nhsformulary",
        ),
        "Operations": DepartmentSubDecisions(
            dept_name="Operations", label="Operations Priority",
            tooltip="Operations CAPS Sales.",
            options={
                "capacity": SubDecisionOption(key="capacity", label="Manufacturing Scale-Up",
                    description="Expand GMP capacity at Cambridge facility.",
                    smax_mult=1.20, k_mult=1.05, synergy={"Sales": 0.10},
                    segment_multipliers={"nhsprimary": 1.20, "nhshospital": 1.25, "nice": 1.00, "private": 0.90}),
                "coldchain": SubDecisionOption(key="coldchain", label="Cold Chain & NHS Distribution",
                    description="Build NHS-compatible distribution including NHS-at-Home delivery.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Sales": 0.05, "Marketing": 0.05},
                    segment_multipliers={"nhsprimary": 1.15, "nhshospital": 1.05, "nice": 1.05, "private": 1.10}),
                "quality": SubDecisionOption(key="quality", label="Quality & MHRA Compliance",
                    description="Strengthen GMP systems for MHRA excellence rating.",
                    smax_mult=1.05, k_mult=0.85, synergy={"R&D": 0.05},
                    segment_multipliers={"nhsprimary": 1.10, "nhshospital": 1.20, "nice": 1.15, "private": 1.05}),
                "redundancy": SubDecisionOption(key="redundancy", label="Post-Brexit Supply Resilience",
                    description="Dual-source API, build UK safety stock against Channel port disruptions.",
                    smax_mult=1.10, k_mult=1.00, synergy={"Sales": 0.08},
                    segment_multipliers={"nhsprimary": 1.15, "nhshospital": 1.10, "nice": 1.05, "private": 1.05}),
            },
            default="capacity",
        ),
        # DTC BANNED in UK — Marketing options are professional/educational only
        "Marketing": DepartmentSubDecisions(
            dept_name="Marketing", label="Marketing Strategy",
            tooltip="DTC prescription advertising is banned in the UK. Marketing works through NHS, medical, and educational channels.",
            options={
                "medical": SubDecisionOption(key="medical", label="Medical Education & Conferences",
                    description="Sponsor Diabetes UK conferences, publish in BMJ/Lancet, build KOL relationships.",
                    smax_mult=1.20, k_mult=1.15, synergy={"R&D": 0.10},
                    segment_multipliers={"nhsprimary": 1.10, "nhshospital": 1.30, "nice": 1.25, "private": 1.10}),
                "patientprog": SubDecisionOption(key="patientprog", label="NHS Patient Support Programmes",
                    description="Diabetes management, nurse educator services, peer support within NHS framework.",
                    smax_mult=1.15, k_mult=1.00, synergy={"Sales": 0.08},
                    segment_multipliers={"nhsprimary": 1.25, "nhshospital": 0.95, "nice": 1.05, "private": 1.15}),
                "value": SubDecisionOption(key="value", label="Health Economics for NICE",
                    description="Commission UK cost-effectiveness studies specifically for NICE technology appraisal.",
                    smax_mult=1.10, k_mult=0.90, synergy={"Sales": 0.12},
                    segment_multipliers={"nhsprimary": 1.30, "nhshospital": 1.15, "nice": 1.50, "private": 0.80}),
                "nhs_digital": SubDecisionOption(key="nhs_digital", label="NHS Digital Integration Campaign",
                    description="Position as NHS App-compatible, NHS-at-Home ready, integrated with NHS Digital infrastructure.",
                    smax_mult=1.10, k_mult=1.10, synergy={"R&D": 0.06, "Sales": 0.06},
                    segment_multipliers={"nhsprimary": 1.20, "nhshospital": 1.15, "nice": 1.15, "private": 0.90}),
            },
            default="value",
        ),
    },

    competitors=[
        CompetitorDef(name="NordicBio UK", industry="Global insulin leader — UK operations",
            location="London (HQ: Copenhagen)", founded="1923",
            description="UK subsidiary of global insulin leader. Deep NHS relationships, decades of trust, massive scale. Slow on connected delivery.",
            display_label="Global Insulin Leader (UK Arm)",
            base_revenue=85_000_000, growth_rate=0.03, margin=0.22,
            base_specs={"efficacy": 82, "usability": 54, "cost": 3200},
            spec_growth_rates={"efficacy": 1.5, "usability": 2.5, "cost": 60},
            base_reach=1.35,  # Strong NHS formulary relationships and HCP reach
        ),
        CompetitorDef(name="GenevaPharm UK", industry="European biosimilar specialist",
            location="London (HQ: Basel)", founded="2008",
            description="Swiss biosimilar company aggressive on NHS pricing. No connected pen but deep understanding of NICE cost-effectiveness requirements.",
            display_label="European Biosimilar Challenger",
            base_revenue=50_000_000, growth_rate=0.10, margin=0.12,
            base_specs={"efficacy": 78, "usability": 44, "cost": 1900},
            spec_growth_rates={"efficacy": 1.0, "usability": 2.0, "cost": -60},
            base_reach=1.0,  # Established biosimilar footprint in UK
        ),
        CompetitorDef(name="AmeriPharma UK", industry="US pharma major — UK subsidiary",
            location="London (HQ: Indianapolis)", founded="1876",
            description="American pharma with strong UK physician relationships. Recently launched a basic connected pen for NHS market.",
            display_label="US Pharma Major (UK Arm)",
            base_revenue=65_000_000, growth_rate=0.05, margin=0.17,
            base_specs={"efficacy": 80, "usability": 60, "cost": 2800},
            spec_growth_rates={"efficacy": 1.8, "usability": 3.5, "cost": 50},
            base_reach=1.2,  # Significant NHS payer presence
        ),
        CompetitorDef(name="Vitality Health Tech", industry="UK digital health startup",
            location="London, United Kingdom", founded="2019",
            description="London-based digital health startup backed by NHS innovation funds. Strong software, limited pharma experience.",
            display_label="UK Digital Health Startup Rival",
            base_revenue=15_000_000, growth_rate=0.22, margin=0.04,
            base_specs={"efficacy": 74, "usability": 84, "cost": 2600},
            spec_growth_rates={"efficacy": 2.5, "usability": 6.0, "cost": 30},
            base_reach=0.65,  # Early-stage, limited NHS pathway
        ),
    ],

    competitor_labels={
        "NordicBio UK": "Global Insulin Leader (UK Arm)",
        "GenevaPharm UK": "European Biosimilar Challenger",
        "AmeriPharma UK": "US Pharma Major (UK Arm)",
        "Vitality Health Tech": "UK Digital Health Startup Rival",
    },

    product_specs=[
        ProductSpec(key="efficacy", label="Clinical Efficacy", unit="score", base_value=77, higher_is_better=True),
        ProductSpec(key="usability", label="Device Usability", unit="score", base_value=70, higher_is_better=True),
        ProductSpec(key="cost", label="Therapy Cost", unit="£/yr", base_value=2800, higher_is_better=False, display_format=",.0f"),
    ],

    spec_evolution_rules=[
        SpecEvolutionRule(spec_key="efficacy", dept_name="R&D",
            base_growth=1.0, spend_sensitivity=5.0, dept_budget_ref=4_500_000,
            sub_decision_bonuses={"clinical": 4.0, "device": 1.0, "costreduce": -1.0, "software": 2.0},
            min_value=65, max_value=98),
        SpecEvolutionRule(spec_key="usability", dept_name="R&D",
            base_growth=1.5, spend_sensitivity=6.0, dept_budget_ref=4_500_000,
            sub_decision_bonuses={"device": 5.0, "software": 4.0, "clinical": 1.0, "costreduce": -2.0},
            min_value=50, max_value=98),
        SpecEvolutionRule(spec_key="cost", dept_name="R&D",
            base_growth=35, spend_sensitivity=-140, dept_budget_ref=4_500_000,
            sub_decision_bonuses={"costreduce": -280, "clinical": 70, "device": 100, "software": 70},
            min_value=900, max_value=4000),
    ],

    segment_spec_preferences={
        "nhsprimary": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.35, ideal_value=86, tolerance=15),
            SegmentSpecPreference(spec_key="usability", weight=0.20, ideal_value=75, tolerance=20),
            SegmentSpecPreference(spec_key="cost", weight=0.45, ideal_value=2000, tolerance=1000),
        ],
        "nhshospital": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.45, ideal_value=90, tolerance=12),
            SegmentSpecPreference(spec_key="usability", weight=0.25, ideal_value=78, tolerance=18),
            SegmentSpecPreference(spec_key="cost", weight=0.30, ideal_value=2400, tolerance=1200),
        ],
        "nice": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.40, ideal_value=88, tolerance=12),
            SegmentSpecPreference(spec_key="usability", weight=0.15, ideal_value=75, tolerance=18),
            SegmentSpecPreference(spec_key="cost", weight=0.45, ideal_value=1800, tolerance=900),
        ],
        "private": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.35, ideal_value=88, tolerance=14),
            SegmentSpecPreference(spec_key="usability", weight=0.45, ideal_value=90, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.20, ideal_value=3500, tolerance=1800),
        ],
    },

    performance_index_name="MPI",
    performance_index_full="Meridian Performance Index",
    market_label="insulin delivery market",

    bottleneck_cap_dept_idx=2,
    bottleneck_capped_dept_idx=1,
    bottleneck_cap_fraction=0.75,
    delayed_return_dept_idx=0,
    brand_equity_depts=[(3, 0.6), (0, 1.0)],

    general_news_pool=GENERAL_NEWS_POOL,
    dept_news_pool=DEPT_NEWS_POOL,
    competitor_news_pool=COMPETITOR_NEWS_POOL,

    storyboard=StoryboardContent(
        world_headline="The year is 2025. The NHS is embracing digital diabetes care — but the gatekeepers are formidable.",
        world_body=(
            "The NHS is the single largest healthcare system Meridian will ever deal with — and it "
            "operates like nothing else in the world. NICE technology appraisals are the gateway to "
            "adoption, demanding rigorous clinical evidence and cost-effectiveness data that can take "
            "years to compile. NHS trust formulary committees make independent decisions, clinical "
            "commissioning groups control prescribing budgets, and post-Brexit supply chain friction "
            "has added weeks to import timelines for pharmaceutical ingredients. Biosimilars are "
            "transforming insulin pricing, GLP-1 drugs are reducing the patient pipeline, and direct-to-"
            "consumer advertising is banned entirely. Your path to patients goes exclusively through "
            "the NHS, physicians, and published evidence. There are no shortcuts."
        ),
        market_body=(
            "The UK insulin delivery market is valued at 2.8 billion pounds annually. Connected smart "
            "pens are the fastest-growing segment, but NHS adoption requires NICE approval."
        ),
        market_kpis=[
            ("Market Size", "£2.8B annually", "dept_rd"),
            ("Smart Pen Growth", "20% CAGR", "accent"),
            ("Channels", "4 access pathways", "dept_mktg"),
        ],
        segments_intro="Each channel has different NHS gatekeepers, different evidence thresholds, and different timelines to win.",
        company_subtitle="Founded 2020  ·  Cambridge  ·  220 employees  ·  LSE: MRDN",
        company_body=(
            "Meridian BioSciences was founded by a Cambridge University pharmacologist who believed that "
            "connected insulin delivery could transform NHS diabetes outcomes. The IntelliPen platform was "
            "developed in collaboration with Addenbrooke's Hospital, tested through a multi-centre NHS "
            "trial that caught the attention of NICE evaluators, and manufactured at an MHRA-inspected "
            "facility in the Cambridge science park. The company has early traction with three NHS trusts "
            "in the East of England and a growing body of real-world evidence. But winning a positive NICE "
            "technology appraisal, building formulary access across 200+ NHS trusts, and scaling a "
            "post-Brexit supply chain is the challenge that separates promising biotech from national "
            "healthcare partner."
        ),
        product_subtitle="Smart Insulin Pen — Built for the NHS, designed for patients",
        product_body=(
            "The IntelliPen is a connected insulin pen with NHS App integration, CGM compatibility, "
            "and AI-powered dosing support. Developed at Cambridge, tested at Addenbrooke's. Annual "
            "therapy cost 2,800 pounds per patient. Year 1 enrollment capacity: 7,000 patients."
        ),
        product_kpis=[
            ("Therapy Cost", "£2,800/yr", "dept_rd"),
            ("Efficacy Score", "77/100", "accent"),
            ("Usability Score", "70/100", "dept_sales"),
            ("Yr 1 Capacity", "7,000 patients", "dept_ops"),
        ],
        role_body=(
            "Allocate Meridian's budget across four departments over 5 years. DTC advertising is "
            "banned — your Marketing must work through medical education, conferences, and NHS "
            "channels. Clinical evidence is your most powerful weapon."
        ),
        objective_body="MPI based on profitability (50%) and UK market share (50%). Consistency beats volatility.",
        departments_intro="In UK pharma, NICE appraisals require robust clinical evidence — the R&D to Sales synergy is the most important relationship in the game.",
        competitors_intro="These competitors are already on NHS formularies with decades of trust. You need to displace them with better evidence.",
        ready_headline="Your journey starts now — 4.9 million British diabetics are waiting for better care.",
        ready_body=(
            "No DTC advertising. No shortcuts past NICE. Your path to patients goes through "
            "published evidence, NHS trust relationships, and physician trust. The science is your "
            "weapon. The NHS is your battlefield. Five years. Allocate wisely."
        ),
    ),

    briefing=BriefingContent(
        world_body=(
            "The NHS gates access through NICE technology appraisals demanding rigorous evidence. "
            "NHS trust formularies make independent decisions. DTC is banned. Post-Brexit friction "
            "complicates supply chains. Biosimilars are disrupting pricing. Your path to patients "
            "goes through physicians and published clinical evidence, not marketing spend."
        ),
        market_body="UK insulin delivery: 2.8 billion pounds, smart pens growing at 20%. Four NHS-gated channels.",
        company_body=(
            "Meridian BioSciences is a Cambridge biotech with MHRA approval, early NHS trust traction, "
            "and growing real-world evidence from Addenbrooke's Hospital. 220 employees, LSE-listed. "
            "Founded by a Cambridge pharmacologist. The challenge: win NICE and scale across 200+ trusts."
        ),
        product_body="IntelliPen: connected pen with NHS App integration and AI dosing. 2,800 pounds per patient per year. Year 1: 7,000 patients.",
        product_kpis=[
            ("Therapy Cost", "£2,800/yr", "dept_rd"),
            ("Efficacy Score", "77/100", "accent"),
            ("Usability Score", "70/100", "dept_sales"),
            ("Yr 1 Capacity", "7,000 patients", "dept_ops"),
        ],
        role_body="Allocate across 4 departments over 5 years. DTC banned — work through NHS channels.",
        objective_body="MPI based on profitability (50%) and market share (50%).",
    ),
    objective_text={},
)


register_scenario("uk", "pharma", UK_PHARMA)
