"""
scenarios/us_pharma.py — United States × Pharmaceutical (Smart Insulin Pen) scenario.

Glycon Therapeutics — a Boston-based biotech startup commercializing a biosimilar
insulin with a connected smart pen delivery platform.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.us_pharma_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


US_PHARMA = ScenarioDefinition(
    scenario_id="us_pharma",
    scenario_label="United States — Pharmaceutical",

    locale=LocaleConfig(
        country_code="US", country_name="United States",
        currency_symbol="$", currency_code="USD",
        currency_prefix=True,
        large_number_suffix="M", large_number_divisor=1_000_000,
    ),

    company=CompanyConfig(
        name="Glycon Therapeutics",
        product_name="Glycon NovaPen Smart Insulin System",
        tagline="Connected insulin delivery for better outcomes",
        location="Boston, Massachusetts",
        role_title="VP of Finance & Strategy",
        founding_year="2021",
        industry_label="Pharmaceutical — Insulin Delivery",
        unit_price=4_200.0,         # $4,200 per patient enrolled (pen + year 1 cartridges)
        unit_price_label="Annual Therapy Cost",
        unit_cost=1_400.0,          # $1,400 COGS per patient
        year1_capacity=8_000,       # 8,000 new patient enrollments year 1
        capacity_unit="patients",
    ),

    financials=FinancialConfig(
        total_budget=25_000_000,        # $25M — well-funded Series B biotech
        fixed_costs=38_000_000,         # $38M — lab, GMP facility, regulatory, overhead
        base_revenue=15_000_000,        # $15M — existing small patient base
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
        # Placeholder bounds — will be calibrated by Monte Carlo
        vpi_ras_floor=-4_179_460,
        vpi_ras_ceiling=19_347_550,
        vpi_share_floor=21.62,
        vpi_share_ceiling=26.94,
        competitor_presence_baseline=180_000_000,
    ),

    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    # Departments
    # Pharma-tuned: R&D has strong synergy with Sales (clinical data → formulary wins)
    # Operations bottleneck tighter (0.75 cap in bottleneck_cap_fraction below)
    # Marketing has higher K (expensive to gain traction in pharma)
    departments=[
        DepartmentParams(
            name="R&D", S_max=35_000_000, K=7_500_000, alpha=1.3,
            decay=0.55, min_spend=1_500_000, max_spend=12_500_000,
            state_sensitivity=0.12, catch_up_rate=0.25, sweet_spot_frac=0.70,
        ),
        DepartmentParams(
            name="Sales", S_max=25_000_000, K=6_000_000, alpha=0.9,
            decay=0.20, min_spend=2_000_000, max_spend=12_500_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Operations", S_max=30_000_000, K=4_500_000, alpha=0.85,
            decay=0.55, min_spend=1_500_000, max_spend=10_000_000,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Marketing", S_max=28_000_000, K=5_500_000, alpha=1.05,
            decay=0.40, min_spend=1_200_000, max_spend=10_000_000,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.65,
        ),
    ],

    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd",
            description=(
                "R&D drives clinical evidence, device innovation, and regulatory filings. "
                "Returns are DELAYED by one year — clinical trials and FDA submissions take time. "
                "Strong R&D creates powerful synergy with Sales: published clinical data is what gets "
                "your product onto hospital formularies and insurance approved lists."
            ),
            background_description="R&D runs clinical trials at US medical centres, develops smart pen hardware and firmware, manages FDA regulatory submissions, and builds the connected health software platform.",
        ),DepartmentMeta(
            name="Sales", color_key="dept_sales",
            description=(
                "Sales covers physician relationships, hospital formulary access, and insurance "
                "negotiations. Returns are immediate but CAPPED by Operations — you cannot enroll "
                "patients faster than you can manufacture and distribute pens. Losing a formulary "
                "listing is extremely hard to reverse."
            ),
            background_description="Sales manages physician relationships, hospital formulary access, insurance company negotiations, and patient enrollment programs across the US healthcare system.",
        ),DepartmentMeta(
            name="Operations", color_key="dept_ops",
            description=(
                "Operations is the BOTTLENECK — it determines how many patients you can serve. "
                "Pharmaceutical manufacturing requires GMP compliance, cold-chain logistics, and "
                "quality systems. The cap on Sales is tighter than in other industries because "
                "pharma supply chains are less forgiving."
            ),
            background_description="Operations runs the GMP manufacturing facility, manages cold-chain insulin logistics, ensures FDA compliance, and handles nationwide pharmaceutical distribution.",
        ),DepartmentMeta(
            name="Marketing", color_key="dept_mktg",
            description=(
                "Marketing builds physician awareness and patient demand through medical education, "
                "conferences, patient support programs, and (in the US) direct-to-consumer advertising. "
                "Pharma marketing is expensive — the sweet spot is high, and under-spending means "
                "invisibility in a crowded market. Returns follow an S-curve — below a threshold your message is lost in noise, above it you build compounding brand equity among physicians and patients."
            ),
        
            background_description="Marketing builds physician and patient awareness through direct-to-consumer advertising, medical conference sponsorships, patient education programmes, and health economics research. The US is one of the few markets where prescription drug advertising to consumers is permitted.",
        ),
    ],department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    # Consumer Segments (pharma = market access channels)
    segments=[
        ConsumerSegment(
            key="insurance",
            label="Insurance-Covered Patients",
            description=(
                "Patients covered by employer health plans and pharmacy benefit managers. "
                "The largest channel — driven by formulary placement and copay affordability. "
                "Represent ~35% of the addressable market."
            ),
            market_weight=0.35,
        ),
        ConsumerSegment(
            key="hospital",
            label="Hospital Systems",
            description=(
                "Health system purchasing through group purchasing organizations. Hospitals "
                "standardize on one insulin pen for inpatient use. Winning a hospital means "
                "capturing all its diabetic patients. Represent ~25% of the market."
            ),
            market_weight=0.25,
        ),
        ConsumerSegment(
            key="cashpay",
            label="Out-of-Pocket Patients",
            description=(
                "Uninsured or underinsured patients paying full price at the pharmacy. "
                "Extremely price-sensitive — total cost of therapy is the primary driver. "
                "Patient assistance programs matter here. Represent ~20% of the market."
            ),
            market_weight=0.20,
        ),
        ConsumerSegment(
            key="specialist",
            label="Specialist-Prescribed Patients",
            description=(
                "Patients managed by endocrinologists who prescribe based on clinical data "
                "and device features. Least price-sensitive, most quality-driven. Clinical "
                "evidence and device usability matter most. Represent ~20% of the market."
            ),
            market_weight=0.20,
        ),
    ],

    segment_colors={"insurance": "#3D6B50", "hospital": "#4A7B9D", "cashpay": "#C27D3A", "specialist": "#8B6BAE"},

    # Sub-Decisions
    sub_decisions={
        "R&D": DepartmentSubDecisions(
            dept_name="R&D",
            label="R&D Focus",
            tooltip="Choose your clinical and device development priority this year.",
            options={
                "clinical": SubDecisionOption(
                    key="clinical",
                    label="Clinical Outcomes Studies",
                    description="Run real-world evidence trials to prove superior patient outcomes (HbA1c, time-in-range).",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Sales": 0.12, "Marketing": 0.03},
                    segment_multipliers={"insurance": 1.25, "hospital": 1.30, "cashpay": 0.85, "specialist": 1.40},
                ),
                "device": SubDecisionOption(
                    key="device",
                    label="Smart Pen Device Innovation",
                    description="Improve pen hardware — smaller form factor, painless injection, CGM integration.",
                    smax_mult=1.25, k_mult=1.30,
                    synergy={"Marketing": 0.10},
                    segment_multipliers={"insurance": 1.00, "hospital": 0.90, "cashpay": 0.80, "specialist": 1.45},
                ),
                "costreduce": SubDecisionOption(
                    key="costreduce",
                    label="Manufacturing Cost Reduction",
                    description="Optimize insulin formulation and pen production to lower per-patient costs.",
                    smax_mult=0.90, k_mult=0.75,
                    synergy={"Operations": 0.15, "Sales": 0.05},
                    segment_multipliers={"insurance": 1.30, "hospital": 1.15, "cashpay": 1.50, "specialist": 0.70},
                ),
                "software": SubDecisionOption(
                    key="software",
                    label="Digital Health Platform",
                    description="Build out the connected app — dose tracking, AI recommendations, telehealth integration.",
                    smax_mult=1.20, k_mult=1.25,
                    synergy={"Marketing": 0.08},
                    segment_multipliers={"insurance": 1.10, "hospital": 1.05, "cashpay": 0.75, "specialist": 1.35},
                ),
            },
            default="clinical",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales",
            label="Sales Channel Strategy",
            tooltip="Choose your primary go-to-market channel. Sales is CAPPED by Operations capacity.",
            options={
                "formulary": SubDecisionOption(
                    key="formulary",
                    label="Insurance Formulary Push",
                    description="Dedicate sales team to PBM negotiations and employer health plan listings.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Operations": 0.05},
                    segment_multipliers={"insurance": 1.50, "hospital": 0.85, "cashpay": 0.80, "specialist": 0.90},
                ),
                "hospital": SubDecisionOption(
                    key="hospital",
                    label="Hospital & Health System Sales",
                    description="Target hospital formulary committees and group purchasing organizations.",
                    smax_mult=1.10, k_mult=1.05,
                    synergy={"Operations": 0.10},
                    segment_multipliers={"insurance": 0.85, "hospital": 1.55, "cashpay": 0.75, "specialist": 1.10},
                ),
                "patient": SubDecisionOption(
                    key="patient",
                    label="Patient Access Programs",
                    description="Build copay assistance, free trial, and patient hub programs to drive adoption.",
                    smax_mult=1.10, k_mult=1.15,
                    synergy={"Marketing": 0.10},
                    segment_multipliers={"insurance": 1.10, "hospital": 0.80, "cashpay": 1.50, "specialist": 0.95},
                ),
                "specialist": SubDecisionOption(
                    key="specialist",
                    label="Specialist Physician Focus",
                    description="Deploy field medical liaisons to endocrinology practices with clinical evidence.",
                    smax_mult=1.05, k_mult=0.90,
                    synergy={"R&D": 0.08},
                    segment_multipliers={"insurance": 0.90, "hospital": 1.10, "cashpay": 0.85, "specialist": 1.50},
                ),
            },
            default="formulary",
        ),
        "Operations": DepartmentSubDecisions(
            dept_name="Operations",
            label="Operations Priority",
            tooltip="Choose your supply chain focus. Operations CAPS Sales — you cannot enroll patients you cannot supply.",
            options={
                "capacity": SubDecisionOption(
                    key="capacity",
                    label="Manufacturing Scale-Up",
                    description="Expand GMP production capacity for insulin cartridges and pen assembly.",
                    smax_mult=1.20, k_mult=1.05,
                    synergy={"Sales": 0.10},
                    segment_multipliers={"insurance": 1.20, "hospital": 1.25, "cashpay": 1.00, "specialist": 0.90},
                ),
                "coldchain": SubDecisionOption(
                    key="coldchain",
                    label="Cold Chain & Distribution",
                    description="Invest in temperature-controlled logistics and nationwide distribution reach.",
                    smax_mult=1.10, k_mult=1.15,
                    synergy={"Sales": 0.05, "Marketing": 0.05},
                    segment_multipliers={"insurance": 1.10, "hospital": 1.05, "cashpay": 1.15, "specialist": 1.10},
                ),
                "quality": SubDecisionOption(
                    key="quality",
                    label="Quality Systems & Compliance",
                    description="Strengthen GMP systems, prepare for FDA inspections, reduce defect rates.",
                    smax_mult=1.05, k_mult=0.85,
                    synergy={"R&D": 0.05},
                    segment_multipliers={"insurance": 1.10, "hospital": 1.20, "cashpay": 0.95, "specialist": 1.15},
                ),
                "redundancy": SubDecisionOption(
                    key="redundancy",
                    label="Supply Chain Redundancy",
                    description="Dual-source API, build safety stock, establish backup manufacturing site.",
                    smax_mult=1.10, k_mult=1.00,
                    synergy={"Sales": 0.08},
                    segment_multipliers={"insurance": 1.15, "hospital": 1.10, "cashpay": 1.05, "specialist": 1.05},
                ),
            },
            default="capacity",
        ),
        "Marketing": DepartmentSubDecisions(
            dept_name="Marketing",
            label="Marketing Strategy",
            tooltip="Choose your awareness and demand strategy. In the US, direct-to-patient advertising is legal for prescription products.",
            options={
                "dtc": SubDecisionOption(
                    key="dtc",
                    label="Direct-to-Patient Advertising",
                    description="TV, digital, and social media campaigns targeting diabetic patients directly.",
                    smax_mult=1.20, k_mult=1.15,
                    synergy={"Sales": 0.10},
                    segment_multipliers={"insurance": 1.30, "hospital": 0.75, "cashpay": 1.40, "specialist": 0.80},
                ),
                "medical": SubDecisionOption(
                    key="medical",
                    label="Medical Education & Conferences",
                    description="Sponsor medical conferences, publish clinical evidence, build KOL relationships.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"R&D": 0.08},
                    segment_multipliers={"insurance": 0.90, "hospital": 1.25, "cashpay": 0.70, "specialist": 1.50},
                ),
                "patientprog": SubDecisionOption(
                    key="patientprog",
                    label="Patient Support & Education",
                    description="Diabetes management programs, nurse educator hotlines, peer support communities.",
                    smax_mult=1.10, k_mult=1.00,
                    synergy={"Sales": 0.06, "R&D": 0.04},
                    segment_multipliers={"insurance": 1.15, "hospital": 1.05, "cashpay": 1.35, "specialist": 1.10},
                ),
                "value": SubDecisionOption(
                    key="value",
                    label="Health Economics & Outcomes",
                    description="Commission cost-effectiveness studies and real-world evidence for payer presentations.",
                    smax_mult=1.05, k_mult=0.90,
                    synergy={"Sales": 0.12},
                    segment_multipliers={"insurance": 1.45, "hospital": 1.20, "cashpay": 0.80, "specialist": 1.00},
                ),
            },
            default="dtc",
        ),
    },

    # Competitors
    competitors=[
        CompetitorDef(
            name="NordicBio Pharmaceuticals",
            industry="Global insulin leader",
            location="Copenhagen, Denmark",
            founded="1923",
            description=(
                "The world's dominant insulin manufacturer with 45% global market share. "
                "Massive physician relationships, deep payer contracts, and decades of brand trust. "
                "Slow to innovate on connected delivery but unmatched in volume and distribution."
            ),
            display_label="Global Insulin Market Leader",
            base_revenue=120_000_000, growth_rate=0.04, margin=0.24,
            base_specs={"efficacy": 82, "usability": 55, "cost": 4800},
            spec_growth_rates={"efficacy": 1.5, "usability": 3.0, "cost": 100},
            base_reach=1.4,  # Dominant HCP relationships, massive sales force,
        ),
        CompetitorDef(
            name="AmeriPharma Life Sciences",
            industry="US pharmaceutical major",
            location="Indianapolis, Indiana",
            founded="1876",
            description=(
                "American pharma giant with the second-largest insulin portfolio. Strong DTC "
                "advertising capability and physician relationships. Recently launched a basic "
                "connected pen to compete with smart pen startups."
            ),
            display_label="US Pharma Major",
            base_revenue=95_000_000, growth_rate=0.06, margin=0.2,
            base_specs={"efficacy": 80, "usability": 62, "cost": 4200},
            spec_growth_rates={"efficacy": 2.0, "usability": 4.0, "cost": 80},
            base_reach=1.3,  # Strong US payer and prescriber reach,
        ),
        CompetitorDef(
            name="GenevaPharm AG",
            industry="European biosimilar specialist",
            location="Basel, Switzerland",
            founded="2008",
            description=(
                "European biosimilar company aggressively entering the US market with low-cost "
                "insulin. No connected pen capability but undercutting on price. Strong in hospital "
                "and managed care channels."
            ),
            display_label="European Biosimilar Challenger",
            base_revenue=65_000_000, growth_rate=0.12, margin=0.12,
            base_specs={"efficacy": 78, "usability": 45, "cost": 2800},
            spec_growth_rates={"efficacy": 1.0, "usability": 2.0, "cost": -100},
            base_reach=0.9,  # Limited US commercial infrastructure,
        ),
        CompetitorDef(
            name="Dextral Health",
            industry="Digital health insulin startup",
            location="San Francisco, California",
            founded="2019",
            description=(
                "Venture-backed digital health startup with a software-first approach to insulin "
                "delivery. Beautiful app, strong tech talent, but limited clinical evidence "
                "and no pharma sales experience. Your closest direct competitor."
            ),
            display_label="Digital Health Startup Rival",
            base_revenue=30_000_000, growth_rate=0.18, margin=0.06,
            base_specs={"efficacy": 75, "usability": 85, "cost": 3600},
            spec_growth_rates={"efficacy": 2.5, "usability": 6.0, "cost": 50},
            base_reach=0.7,  # Nascent commercial reach, DTC focused,
        ),
    ],

    competitor_labels={
        "NordicBio Pharmaceuticals": "Global Insulin Market Leader",
        "AmeriPharma Life Sciences": "US Pharma Major",
        "GenevaPharm AG": "European Biosimilar Challenger",
        "Dextral Health": "Digital Health Startup Rival",
    },

    # Product Specs
    product_specs=[
        ProductSpec(key="efficacy", label="Clinical Efficacy", unit="score", base_value=78, higher_is_better=True),
        ProductSpec(key="usability", label="Device Usability", unit="score", base_value=72, higher_is_better=True),
        ProductSpec(key="cost", label="Therapy Cost", unit="$/yr", base_value=4200, higher_is_better=False, display_format=",.0f"),
    ],

    spec_evolution_rules=[
        SpecEvolutionRule(
            spec_key="efficacy", dept_name="R&D",
            base_growth=1.0,
            spend_sensitivity=5.0,
            dept_budget_ref=6_000_000,
            sub_decision_bonuses={"clinical": 4.0, "device": 1.0, "costreduce": -1.0, "software": 2.0},
            min_value=65, max_value=98,
        ),
        SpecEvolutionRule(
            spec_key="usability", dept_name="R&D",
            base_growth=1.5,
            spend_sensitivity=6.0,
            dept_budget_ref=6_000_000,
            sub_decision_bonuses={"device": 5.0, "software": 4.0, "clinical": 1.0, "costreduce": -2.0},
            min_value=50, max_value=98,
        ),
        SpecEvolutionRule(
            spec_key="cost", dept_name="R&D",
            base_growth=50,
            spend_sensitivity=-200,
            dept_budget_ref=6_000_000,
            sub_decision_bonuses={"costreduce": -400, "clinical": 100, "device": 150, "software": 100},
            min_value=1500, max_value=6000,
        ),
    ],

    segment_spec_preferences={
        "insurance": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.35, ideal_value=88, tolerance=15),
            SegmentSpecPreference(spec_key="usability", weight=0.20, ideal_value=75, tolerance=20),
            SegmentSpecPreference(spec_key="cost", weight=0.45, ideal_value=3000, tolerance=1500),
        ],
        "hospital": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.45, ideal_value=90, tolerance=12),
            SegmentSpecPreference(spec_key="usability", weight=0.25, ideal_value=80, tolerance=18),
            SegmentSpecPreference(spec_key="cost", weight=0.30, ideal_value=3500, tolerance=1500),
        ],
        "cashpay": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.20, ideal_value=80, tolerance=18),
            SegmentSpecPreference(spec_key="usability", weight=0.15, ideal_value=70, tolerance=20),
            SegmentSpecPreference(spec_key="cost", weight=0.65, ideal_value=2000, tolerance=1200),
        ],
        "specialist": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.45, ideal_value=92, tolerance=10),
            SegmentSpecPreference(spec_key="usability", weight=0.40, ideal_value=90, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.15, ideal_value=4500, tolerance=2000),
        ],
    },

    performance_index_name="GPI",
    performance_index_full="Glycon Performance Index",
    market_label="insulin delivery market",

    # Pharma-tuned mechanics
    bottleneck_cap_dept_idx=2,       # Operations
    bottleneck_capped_dept_idx=1,    # Sales
    bottleneck_cap_fraction=0.75,    # Tighter than EV (0.85) — pharma supply chains less forgiving
    delayed_return_dept_idx=0,       # R&D
    brand_equity_depts=[(3, 0.6), (0, 1.0)],  # R&D reputation IS the brand in pharma

    general_news_pool=GENERAL_NEWS_POOL,
    dept_news_pool=DEPT_NEWS_POOL,
    competitor_news_pool=COMPETITOR_NEWS_POOL,

    storyboard=StoryboardContent(
        world_headline="The year is 2025. The insulin market is being disrupted — and patients are caught in the crossfire.",
        world_body=(
            "Insulin prices have become a political lightning rod. The Inflation Reduction Act has "
            "capped copays, biosimilars are flooding the market, and connected health technology is "
            "transforming how patients manage diabetes. Meanwhile, GLP-1 drugs like Ozempic are "
            "reducing the number of patients who progress to insulin therapy. The companies that "
            "combine clinical excellence with smart technology and accessible pricing will define "
            "the next generation of diabetes care."
        ),
        market_body=(
            "The US insulin delivery market is valued at $12B annually, with smart connected "
            "devices representing the fastest-growing segment at 25% CAGR. Four distinct market "
            "access channels determine where patients get their insulin."
        ),
        market_kpis=[
            ("Market Size", "$12B annually", "dept_rd"),
            ("Smart Pen Growth", "25% CAGR", "accent"),
            ("Channels", "4 access pathways", "dept_mktg"),
        ],
        segments_intro="Each channel has different decision-makers, different price sensitivities, and different evidence requirements.",
        company_subtitle="Founded 2021  ·  Boston, MA  ·  280 employees  ·  Series B funded",
        company_body=(
            "Glycon Therapeutics is a clinical-stage biotech that has successfully developed a "
            "biosimilar rapid-acting insulin paired with the NovaPen — a connected smart pen with "
            "dose tracking, CGM integration, and AI-powered dosing suggestions. The company received "
            "FDA approval 8 months ago and has been commercializing through a small sales team. "
            "The previous CFO left to join a competitor. You are stepping in to lead the critical "
            "5-year commercial scale-up that will determine whether Glycon becomes a major player "
            "in diabetes care."
        ),
        product_subtitle="Smart Insulin Pen System — Where pharma meets digital health",
        product_body=(
            "The Glycon NovaPen is a reusable smart insulin pen paired with biosimilar rapid-acting "
            "insulin cartridges. The pen connects via Bluetooth to a patient app that tracks doses, "
            "integrates with continuous glucose monitors, and provides AI-powered insights. "
            "Annual therapy cost per patient is approximately $4,200 (device + cartridges). "
            "Year 1 enrollment capacity is 8,000 new patients."
        ),
        product_kpis=[
            ("Therapy Cost", "$4,200/yr", "dept_rd"),
            ("Efficacy Score", "78/100", "accent"),
            ("Usability Score", "72/100", "dept_sales"),
            ("Yr 1 Capacity", "8,000 patients", "dept_ops"),
        ],
        role_body=(
            "You are responsible for allocating Glycon's annual operating budget across four "
            "departments — R&D, Sales, Operations, and Marketing — over a 5-year commercial window. "
            "Each year you set budgets AND choose a strategic direction for each department. "
            "Your decisions are final: once a year is locked, you cannot revisit it."
        ),
        objective_body=(
            "Your GPI score (0–1000+) is based on two equally weighted components: "
            "risk-adjusted profitability (50%) and insulin delivery market share (50%). "
            "Consistent earnings beat volatile ones. Broad market access beats narrow niches."
        ),
        departments_intro="Each department has distinct mechanics. In pharma, R&D evidence drives Sales access — the synergy is critical.",
        competitors_intro="You are not the only one trying to modernize insulin delivery. These competitors want the same patients.",
        ready_headline="Your journey starts now — patients are waiting.",
        ready_body=(
            "You have been briefed on the market, the company, the product, your role, "
            "and the competition. The background and objective tabs will remain available as "
            "reference during the simulation. Trust your strategy — allocate wisely."
        ),
    ),

    briefing=BriefingContent(
        world_body=(
            "The year is 2025. Insulin pricing is under political scrutiny, biosimilars are "
            "proliferating, and connected health technology is transforming diabetes management. "
            "GLP-1 drugs are reducing the insulin-dependent population. The companies that combine "
            "clinical evidence with smart technology and fair pricing will win."
        ),
        market_body=(
            "The US insulin delivery market is $12B annually with smart connected devices growing "
            "at 25% CAGR. Four market access channels — insurance formularies, hospitals, "
            "out-of-pocket patients, and specialist-prescribed patients — each require different "
            "strategies to win."
        ),
        company_body=(
            "Glycon Therapeutics has FDA-approved biosimilar insulin and a connected smart pen "
            "platform. 280 employees, Series B funded, 8 months post-approval. The previous CFO "
            "left. You are leading the 5-year commercial scale-up."
        ),
        product_body=(
            "The NovaPen is a reusable connected insulin pen with dose tracking, CGM integration, "
            "and AI dosing insights. Annual cost per patient ~$4,200. Competes against legacy "
            "insulin pens, cheap biosimilars, and one other smart pen startup. "
            "Year 1 capacity: 8,000 patients."
        ),
        product_kpis=[
            ("Therapy Cost", "$4,200/yr", "dept_rd"),
            ("Efficacy Score", "78/100", "accent"),
            ("Usability Score", "72/100", "dept_sales"),
            ("Yr 1 Capacity", "8,000 patients", "dept_ops"),
        ],
        role_body=(
            "Allocate budget across R&D, Sales, Operations, and Marketing over 5 years. "
            "Choose strategic directions for each department. In pharma, R&D evidence directly "
            "enables Sales access — the synergy between clinical data and formulary wins is "
            "the most important relationship in the game."
        ),
        objective_body=(
            "Your GPI score (0–1000+) is based on risk-adjusted profitability (50%) and "
            "market share (50%). Consistent earnings beat volatile ones. Broad market access "
            "beats narrow niches. The best scores come from balancing both."
        ),
    ),
    objective_text={},
)


register_scenario("us", "pharma", US_PHARMA)
