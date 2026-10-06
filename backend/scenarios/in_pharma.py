"""
scenarios/in_pharma.py — India × Pharmaceutical (Smart Insulin Pen) scenario.

PranaCare Life Sciences — a Hyderabad-based biotech commercializing a biosimilar
insulin with a connected smart pen. NPPA price ceilings, CDSCO regulatory,
DTC advertising BANNED. Premium positioning justified by connected features.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.in_pharma_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


IN_PHARMA = ScenarioDefinition(
    scenario_id="in_pharma",
    scenario_label="India — Pharmaceutical",

    locale=LocaleConfig(
        country_code="IN", country_name="India",
        currency_symbol="₹", currency_code="INR",
        currency_prefix=True,
        large_number_suffix="Cr", large_number_divisor=10_000_000,
        small_number_suffix="L", small_number_divisor=100_000,
        slider_step=100_000,
    ),

    company=CompanyConfig(
        name="PranaCare Life Sciences",
        product_name="PranaCare VitalPen Smart Insulin System",
        tagline="Connected insulin delivery for India's 80 million diabetics",
        location="Hyderabad, Telangana",
        role_title="VP of Finance & Strategy",
        founding_year="2021",
        industry_label="Pharmaceutical — Insulin Delivery",
        # Premium smart pen: ₹30,000/patient/yr (~$360). Higher than generic insulin
        # (₹8,000-12,000) but justified by connected features and device value.
        unit_price=30_000.0,
        unit_price_label="Annual Therapy Cost",
        unit_cost=10_000.0,
        year1_capacity=25_000,      # India: high volume, lower price
        capacity_unit="patients",
    ),

    financials=FinancialConfig(
        total_budget=3_000_000_000,         # ₹300 Cr
        fixed_costs=4_500_000_000,          # ₹450 Cr
        base_revenue=2_000_000_000,         # ₹200 Cr
        profit_reinvestment_rate=0.03,
        inflation_min=0.06,
        inflation_max=0.14,
        underuse_threshold=0.15,
        underuse_penalty_rate=2.5,
        max_change_rate=0.30,
        demand_noise_std=0.10,
        scenario_drift_std=0.04,
        risk_penalty_lambda=1.5,
        num_periods=5,
        num_eval_scenarios=30,
        state_decay=0.5,
        # Placeholder — Monte Carlo calibrated later
        vpi_ras_floor=-637_660_000,
        vpi_ras_ceiling=2_284_550_000,
        vpi_share_floor=22.5,
        vpi_share_ceiling=28.01,
        competitor_presence_baseline=18_000_000_000,    # ₹1,800 Cr
    ),

    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    departments=[
        DepartmentParams(
            name="R&D", S_max=4_200_000_000, K=900_000_000, alpha=1.3,
            decay=0.55, min_spend=180_000_000, max_spend=1_500_000_000,
            state_sensitivity=0.12, catch_up_rate=0.25, sweet_spot_frac=0.70,
        ),
        DepartmentParams(
            name="Sales", S_max=3_000_000_000, K=720_000_000, alpha=0.9,
            decay=0.20, min_spend=240_000_000, max_spend=1_500_000_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Operations", S_max=3_600_000_000, K=540_000_000, alpha=0.85,
            decay=0.55, min_spend=180_000_000, max_spend=1_200_000_000,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Marketing", S_max=3_400_000_000, K=660_000_000, alpha=1.05,
            decay=0.40, min_spend=150_000_000, max_spend=1_200_000_000,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.65,
        ),
    ],

    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd", description=(
            "R&D drives clinical evidence, heat-tolerant device engineering, and CDSCO filings. "
            "Returns are DELAYED by one year. In India, published data from institutions like AIIMS "
            "is essential for government formulary access and physician trust."
        ),
            background_description="R&D conducts clinical studies at AIIMS and Indian medical colleges, develops heat-tolerant pen technology, manages CDSCO submissions, and builds multilingual software supporting 12+ Indian languages.",
        ),
        DepartmentMeta(
            name="Sales", color_key="dept_sales", description=(
            "Sales covers physician relationships, government formulary access, and state-level "
            "negotiations. Returns are immediate but CAPPED by Operations. India's vast geography "
            "and fragmented healthcare system make coverage expensive."
        ),
            background_description="Sales manages government hospital formulary access, private hospital chain relationships, retail pharmacy distribution, and institutional procurement tenders.",
        ),
        DepartmentMeta(
            name="Operations", color_key="dept_ops", description=(
            "Operations is the BOTTLENECK. CDSCO GMP compliance, heat-proof cold-chain logistics, "
            "and monsoon-resilient distribution are India-specific challenges. "
            "PLI scheme rewards domestic manufacturing scale."
        ),
            background_description="Operations runs the Hyderabad GMP facility, manages heat-proof cold-chain logistics, handles NPPA pricing compliance, and coordinates distribution across India's diverse geography.",
        ),
        DepartmentMeta(
            name="Marketing", color_key="dept_mktg", description=(
            "Marketing builds physician awareness through medical education, conferences, and "
            "patient programmes. Direct-to-consumer drug advertising is BANNED in India. "
            "Multilingual outreach across India's 22 official languages is critical. Returns follow an S-curve — below a threshold your message is lost in noise, above it you build compounding brand equity among physicians and patients."
        ),
            background_description="Marketing builds physician awareness through medical education, RSSDI conference sponsorships, multilingual patient programmes, and community health outreach. Direct-to-consumer prescription advertising is not permitted in India.",
        ),
    ],

    department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    segments=[
        ConsumerSegment(key="government", label="Government Hospitals & Public Clinics",
            description="Central and state government procurement through CGHS, ESI, and district hospitals. Massive volume but NPPA-controlled pricing with razor-thin margins. Represent ~38% of the market.",
            market_weight=0.38),
        ConsumerSegment(key="private_hosp", label="Private Hospital Networks",
            description="Apollo, Fortis, Max, Narayana — India's private hospital chains. Quality and reliability matter. Premium pricing accepted. Represent ~22% of the market.",
            market_weight=0.22),
        ConsumerSegment(key="pharmacy", label="Pharmacy Walk-In Patients",
            description="Patients buying directly at retail pharmacies (Apollo, MedPlus, local chemists). Out-of-pocket spending. Price-sensitive but brand-aware. Represent ~25% of the market.",
            market_weight=0.25),
        ConsumerSegment(key="institutional", label="Institutional Buyers (Military, Railways)",
            description="Indian Armed Forces, Indian Railways, PSU health services. Bulk tender procurement with strict compliance requirements. Represent ~15% of the market.",
            market_weight=0.15),
    ],

    segment_colors={"government": "#3D6B50", "private_hosp": "#4A7B9D", "pharmacy": "#C27D3A", "institutional": "#8B6BAE"},

    sub_decisions={
        "R&D": DepartmentSubDecisions(
            dept_name="R&D", label="R&D Focus",
            tooltip="Choose your clinical and device priority.",
            options={
                "clinical": SubDecisionOption(key="clinical", label="AIIMS Clinical Outcomes Studies",
                    description="Run real-world trials at AIIMS and top Indian medical colleges for government formulary evidence.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Sales": 0.12, "Marketing": 0.03},
                    segment_multipliers={"government": 1.40, "private_hosp": 1.25, "pharmacy": 0.85, "institutional": 1.30}),
                "device": SubDecisionOption(key="device", label="Heat-Tolerant Device Engineering",
                    description="Optimise pen for India's 45°C+ summers — heat-stable insulin, dust-resistant mechanics, extended battery.",
                    smax_mult=1.25, k_mult=1.30, synergy={"Marketing": 0.10},
                    segment_multipliers={"government": 1.10, "private_hosp": 1.00, "pharmacy": 1.15, "institutional": 1.20}),
                "costreduce": SubDecisionOption(key="costreduce", label="Cost Reduction for NPPA Compliance",
                    description="Radical cost engineering to achieve NPPA price ceiling viability. Local sourcing, simplified design.",
                    smax_mult=0.90, k_mult=0.75, synergy={"Operations": 0.15, "Sales": 0.05},
                    segment_multipliers={"government": 1.50, "private_hosp": 0.90, "pharmacy": 1.40, "institutional": 1.35}),
                "software": SubDecisionOption(key="software", label="Multilingual Digital Platform",
                    description="Build connected app with support for 12+ Indian languages, WhatsApp integration, and offline mode.",
                    smax_mult=1.20, k_mult=1.25, synergy={"Marketing": 0.08},
                    segment_multipliers={"government": 0.90, "private_hosp": 1.15, "pharmacy": 1.20, "institutional": 0.85}),
            },
            default="clinical",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales", label="Sales Channel Strategy",
            tooltip="Sales is CAPPED by Operations.",
            options={
                "government": SubDecisionOption(key="government", label="Government Tender & Formulary Push",
                    description="Target CGHS, ESI, state formularies, and Jan Aushadhi network listings.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Operations": 0.05},
                    segment_multipliers={"government": 1.50, "private_hosp": 0.80, "pharmacy": 0.85, "institutional": 1.25}),
                "hospital": SubDecisionOption(key="hospital", label="Private Hospital Chain Sales",
                    description="Target Apollo, Fortis, Max, Narayana hospital formulary committees.",
                    smax_mult=1.10, k_mult=1.05, synergy={"Operations": 0.10},
                    segment_multipliers={"government": 0.80, "private_hosp": 1.55, "pharmacy": 0.90, "institutional": 0.85}),
                "patient": SubDecisionOption(key="patient", label="Patient Access Programmes",
                    description="Build copay assistance, free trials, and patient education for out-of-pocket buyers.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Marketing": 0.10},
                    segment_multipliers={"government": 0.85, "private_hosp": 0.90, "pharmacy": 1.50, "institutional": 0.80}),
                "specialist": SubDecisionOption(key="specialist", label="Endocrinologist Engagement",
                    description="Deploy medical liaisons to diabetes centres with Indian clinical evidence.",
                    smax_mult=1.05, k_mult=0.90, synergy={"R&D": 0.08},
                    segment_multipliers={"government": 1.05, "private_hosp": 1.20, "pharmacy": 1.00, "institutional": 1.10}),
            },
            default="government",
        ),
        "Operations": DepartmentSubDecisions(
            dept_name="Operations", label="Operations Priority",
            tooltip="Operations CAPS Sales.",
            options={
                "capacity": SubDecisionOption(key="capacity", label="Manufacturing Scale-Up with PLI",
                    description="Expand GMP capacity at Hyderabad. Qualify for PLI scheme disbursements.",
                    smax_mult=1.20, k_mult=1.05, synergy={"Sales": 0.10},
                    segment_multipliers={"government": 1.25, "private_hosp": 1.10, "pharmacy": 1.05, "institutional": 1.20}),
                "heatchain": SubDecisionOption(key="heatchain", label="Heat-Proof Supply Chain",
                    description="Build monsoon-resilient, temperature-controlled distribution for India's extreme climate.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Sales": 0.05, "Marketing": 0.05},
                    segment_multipliers={"government": 1.10, "private_hosp": 1.05, "pharmacy": 1.20, "institutional": 1.10}),
                "quality": SubDecisionOption(key="quality", label="Quality & WHO Prequalification",
                    description="Achieve WHO prequalification and CDSCO excellence for government procurement eligibility.",
                    smax_mult=1.05, k_mult=0.85, synergy={"R&D": 0.05},
                    segment_multipliers={"government": 1.25, "private_hosp": 1.15, "pharmacy": 0.95, "institutional": 1.20}),
                "localisation": SubDecisionOption(key="localisation", label="Domestic Component Localisation",
                    description="Source pen components domestically to reduce import dependency and qualify for Make in India incentives.",
                    smax_mult=1.10, k_mult=1.00, synergy={"Sales": 0.08},
                    segment_multipliers={"government": 1.20, "private_hosp": 1.00, "pharmacy": 1.10, "institutional": 1.15}),
            },
            default="capacity",
        ),
        # DTC BANNED in India
        "Marketing": DepartmentSubDecisions(
            dept_name="Marketing", label="Marketing Strategy",
            tooltip="DTC drug advertising is banned in India. Marketing works through medical and patient education channels.",
            options={
                "medical": SubDecisionOption(key="medical", label="Medical Education & Conferences",
                    description="Sponsor RSSDI/API conferences, publish in IJMR, build relationships with Indian diabetes leaders.",
                    smax_mult=1.20, k_mult=1.15, synergy={"R&D": 0.10},
                    segment_multipliers={"government": 1.15, "private_hosp": 1.30, "pharmacy": 0.85, "institutional": 1.10}),
                "patientprog": SubDecisionOption(key="patientprog", label="Multilingual Patient Programmes",
                    description="Diabetes management in 12+ Indian languages. WhatsApp-based education. Community health worker training.",
                    smax_mult=1.15, k_mult=1.00, synergy={"Sales": 0.08},
                    segment_multipliers={"government": 1.10, "private_hosp": 0.95, "pharmacy": 1.35, "institutional": 1.00}),
                "value": SubDecisionOption(key="value", label="Health Economics for Government Buyers",
                    description="Commission Indian cost-effectiveness studies for NPPA, state formularies, and CGHS submissions.",
                    smax_mult=1.10, k_mult=0.90, synergy={"Sales": 0.12},
                    segment_multipliers={"government": 1.50, "private_hosp": 1.10, "pharmacy": 0.80, "institutional": 1.30}),
                "community": SubDecisionOption(key="community", label="Community Health & Rural Outreach",
                    description="Partner with ASHA workers, PHCs, and rural diabetes screening programmes.",
                    smax_mult=1.05, k_mult=1.05, synergy={"Sales": 0.06, "R&D": 0.04},
                    segment_multipliers={"government": 1.25, "private_hosp": 0.75, "pharmacy": 1.15, "institutional": 1.10}),
            },
            default="medical",
        ),
    },

    competitors=[
        CompetitorDef(name="BharatInsulin Ltd",
            industry="Indian pharmaceutical conglomerate",
            location="Mumbai, India", founded="1995",
            description="India's largest domestic insulin manufacturer backed by a major pharma group. Dominant government tender presence, massive distribution, NPPA-compliant pricing. No connected pen capability.",
            display_label="Dominant Indian Insulin Manufacturer",
            base_revenue=12_000_000_000, growth_rate=0.08, margin=0.11,
            base_specs={"efficacy": 80, "usability": 45, "cost": 12000},
            spec_growth_rates={"efficacy": 1.0, "usability": 2.0, "cost": -500},
            base_reach=1.45,  # Unmatched distribution across India including rural
        ),
        CompetitorDef(name="NordicBio India",
            industry="Global insulin leader — Indian operations",
            location="Bangalore (HQ: Copenhagen)", founded="1923",
            description="Indian subsidiary of global leader. Premium pricing, strong private hospital relationships, trusted brand. Recently launched basic connected pen for Indian market.",
            display_label="Global Leader (Indian Arm)",
            base_revenue=8_000_000_000, growth_rate=0.05, margin=0.2,
            base_specs={"efficacy": 83, "usability": 58, "cost": 35000},
            spec_growth_rates={"efficacy": 1.5, "usability": 3.0, "cost": 800},
            base_reach=1.1,  # Premium reach in metros, limited tier-2/3
        ),
        CompetitorDef(name="HanBio India",
            industry="Chinese pharma — Indian subsidiary",
            location="Chennai (HQ: Shanghai)", founded="2015",
            description="Chinese pharma aggressively entering India with ultra-low-cost biosimilar insulin. Undercutting on price. Strong in government tenders but faces periodic anti-China sentiment.",
            display_label="Chinese Low-Cost Challenger",
            base_revenue=5_000_000_000, growth_rate=0.15, margin=0.07,
            base_specs={"efficacy": 76, "usability": 40, "cost": 8000},
            spec_growth_rates={"efficacy": 1.0, "usability": 1.5, "cost": -400},
            base_reach=0.8,  # Growing but trust and regulatory constraints
        ),
        CompetitorDef(name="MedTech Innovations Pvt Ltd",
            industry="Indian digital health startup",
            location="Bangalore, India", founded="2020",
            description="Bangalore-based startup with software-first approach. Strong tech talent from India's IT ecosystem, limited pharma experience. Your closest competitor.",
            display_label="Indian Digital Health Rival",
            base_revenue=2_500_000_000, growth_rate=0.22, margin=0.04,
            base_specs={"efficacy": 74, "usability": 80, "cost": 25000},
            spec_growth_rates={"efficacy": 2.5, "usability": 5.5, "cost": 400},
            base_reach=0.7,  # Urban-focused, limited traditional channel reach
        ),
    ],

    competitor_labels={
        "BharatInsulin Ltd": "Dominant Indian Insulin Manufacturer",
        "NordicBio India": "Global Leader (Indian Arm)",
        "HanBio India": "Chinese Low-Cost Challenger",
        "MedTech Innovations Pvt Ltd": "Indian Digital Health Rival",
    },

    product_specs=[
        ProductSpec(key="efficacy", label="Clinical Efficacy", unit="score", base_value=76, higher_is_better=True),
        ProductSpec(key="usability", label="Device Usability", unit="score", base_value=68, higher_is_better=True),
        ProductSpec(key="cost", label="Therapy Cost", unit="₹/yr", base_value=30000, higher_is_better=False, display_format=",.0f"),
    ],

    spec_evolution_rules=[
        SpecEvolutionRule(spec_key="efficacy", dept_name="R&D",
            base_growth=1.0, spend_sensitivity=5.0, dept_budget_ref=700_000_000,
            sub_decision_bonuses={"clinical": 4.0, "device": 1.0, "costreduce": -1.0, "software": 2.0},
            min_value=65, max_value=98),
        SpecEvolutionRule(spec_key="usability", dept_name="R&D",
            base_growth=1.5, spend_sensitivity=6.0, dept_budget_ref=700_000_000,
            sub_decision_bonuses={"device": 5.0, "software": 4.0, "clinical": 1.0, "costreduce": -2.0},
            min_value=50, max_value=98),
        SpecEvolutionRule(spec_key="cost", dept_name="R&D",
            base_growth=500, spend_sensitivity=-2000, dept_budget_ref=700_000_000,
            sub_decision_bonuses={"costreduce": -4000, "clinical": 1000, "device": 1500, "software": 1000},
            min_value=8000, max_value=50000),
    ],

    segment_spec_preferences={
        "government": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.30, ideal_value=85, tolerance=18),
            SegmentSpecPreference(spec_key="usability", weight=0.15, ideal_value=70, tolerance=22),
            SegmentSpecPreference(spec_key="cost", weight=0.55, ideal_value=12000, tolerance=8000),
        ],
        "private_hosp": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.45, ideal_value=90, tolerance=12),
            SegmentSpecPreference(spec_key="usability", weight=0.30, ideal_value=82, tolerance=18),
            SegmentSpecPreference(spec_key="cost", weight=0.25, ideal_value=35000, tolerance=15000),
        ],
        "pharmacy": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.25, ideal_value=80, tolerance=18),
            SegmentSpecPreference(spec_key="usability", weight=0.25, ideal_value=75, tolerance=20),
            SegmentSpecPreference(spec_key="cost", weight=0.50, ideal_value=18000, tolerance=10000),
        ],
        "institutional": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.35, ideal_value=85, tolerance=15),
            SegmentSpecPreference(spec_key="usability", weight=0.20, ideal_value=72, tolerance=20),
            SegmentSpecPreference(spec_key="cost", weight=0.45, ideal_value=15000, tolerance=10000),
        ],
    },

    performance_index_name="PPI",
    performance_index_full="PranaCare Performance Index",
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
        world_headline="The year is 2025. India has 80 million diabetics — and most can't afford modern insulin delivery.",
        world_body=(
            "India is the world's diabetes capital and the numbers are staggering — 80 million diagnosed, "
            "an estimated 40 million more undiagnosed, and the count rising at 4% per year. Yet most "
            "Indian diabetics use disposable syringes because pen devices are too expensive. NPPA price "
            "ceilings keep medications affordable but margins razor-thin, Chinese biosimilars are flooding "
            "the market on price alone, and India's extreme climate — 48-degree summers, monsoon flooding "
            "— makes cold chain logistics a daily battle. Connected health technology offers a premium path: "
            "a smart pen that tracks doses and syncs to a phone could transform adherence. But can a "
            "premium device survive in a market where doctors still write prescriptions on paper and "
            "the average patient pays out of pocket?"
        ),
        market_body=(
            "The Indian insulin delivery market is valued at ₹18,000 Cr annually, growing at 15% "
            "CAGR driven by rising diabetes prevalence. Four access channels gate patient reach."
        ),
        market_kpis=[
            ("Market Size", "₹18,000 Cr", "dept_rd"),
            ("Growth Rate", "15% CAGR", "accent"),
            ("Channels", "4 access pathways", "dept_mktg"),
        ],
        segments_intro="Each channel has different gatekeepers, pricing constraints, and evidence requirements.",
        company_subtitle="Founded 2021  ·  Hyderabad  ·  350 employees  ·  NSE: PRANACARE",
        company_body=(
            "PranaCare Life Sciences was born when its founder — a former AIIMS endocrinologist who had "
            "spent a decade watching patients mismanage insulin because they could not afford proper pen "
            "devices — partnered with an IIT Hyderabad engineer to build a smart pen designed specifically "
            "for India. The VitalPen works in 45-degree heat without cold chain, supports 12 Indian "
            "languages, syncs via WhatsApp (because that is what Indian patients actually use), and costs "
            "a fraction of imported alternatives. Early clinical data from AIIMS showed a 28% reduction in "
            "hypoglycaemic events. Apollo Hospitals took notice. The challenge: can a Hyderabad startup "
            "compete with global pharma giants who have decades of government tender relationships?"
        ),
        product_subtitle="Smart Insulin Pen — Designed for India, engineered for outcomes",
        product_body=(
            "The VitalPen is a heat-tolerant connected pen with multilingual app, WhatsApp integration, "
            "and offline mode for rural areas. Annual cost ₹30,000/patient — premium versus generic "
            "insulin (₹8,000-12,000) but justified by connected features and clinical outcomes. "
            "Year 1 capacity: 25,000 patients."
        ),
        product_kpis=[
            ("Therapy Cost", "₹30,000/yr", "dept_rd"),
            ("Efficacy Score", "76/100", "accent"),
            ("Usability Score", "68/100", "dept_sales"),
            ("Yr 1 Capacity", "25,000 patients", "dept_ops"),
        ],
        role_body=(
            "Allocate PranaCare's budget across R&D, Sales, Operations, and Marketing over 5 years. "
            "DTC advertising is banned. NPPA price ceilings constrain pricing. Your path to patients "
            "goes through government formularies, hospital chains, and physician trust."
        ),
        objective_body=(
            "Your PPI score (0–1000+) is based on risk-adjusted profitability (50%) and "
            "Indian insulin market share (50%)."
        ),
        departments_intro="In Indian pharma, R&D evidence from AIIMS-level institutions drives government formulary access.",
        competitors_intro="These competitors dominate Indian hospitals and pharmacies today.",
        ready_headline="Your journey starts now — 80 million patients need better care.",
        ready_body=(
            "No DTC advertising. NPPA controls your price ceiling. Monsoons will flood your warehouses. "
            "But 80 million Indians need better diabetes care, and that number grows by 3 million every "
            "year. The science works. The technology is ready. Now you need the strategy. Five years."
        ),
    ),

    briefing=BriefingContent(
        world_body=(
            "India has 80 million diabetics and most use disposable syringes. NPPA price ceilings keep "
            "margins thin, Chinese biosimilars undercut on price, and 48-degree heat makes cold chain a "
            "daily battle. Connected health offers a premium path but must survive in a market where "
            "patients pay out of pocket and doctors write prescriptions on paper."
        ),
        market_body=(
            "The Indian insulin market is valued at 18,000 crore rupees, growing at 15% CAGR. Four channels: "
            "government hospitals, private chains, pharmacy retail, and institutional buyers."
        ),
        company_body=(
            "PranaCare is a Hyderabad biotech building India's first affordable smart insulin pen. VitalPen "
            "works in extreme heat, supports 12 Indian languages, syncs via WhatsApp. 350 employees, "
            "NSE-listed. Founded by a former AIIMS endocrinologist. Early Apollo Hospitals traction."
        ),
        product_body=(
            "VitalPen: heat-tolerant connected pen, WhatsApp integration, offline mode. "
            "₹30,000/patient/yr. Year 1 capacity: 25,000 patients."
        ),
        product_kpis=[
            ("Therapy Cost", "₹30,000/yr", "dept_rd"),
            ("Efficacy Score", "76/100", "accent"),
            ("Usability Score", "68/100", "dept_sales"),
            ("Yr 1 Capacity", "25,000 patients", "dept_ops"),
        ],
        role_body="Allocate across 4 departments. DTC banned, NPPA controls pricing. R&D evidence drives government access.",
        objective_body="PPI based on profitability (50%) and market share (50%).",
    ),
    objective_text={},
)


register_scenario("in", "pharma", IN_PHARMA)
