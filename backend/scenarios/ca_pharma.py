"""
scenarios/ca_pharma.py — Canada × Pharmaceutical (Smart Insulin Pen) scenario.

NovaBio Health — a Montreal-based biotech commercializing a biosimilar
insulin with a connected smart pen. DTC advertising is BANNED in Canada,
so Marketing sub-decisions focus on medical education and patient programs.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.ca_pharma_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


CA_PHARMA = ScenarioDefinition(
    scenario_id="ca_pharma",
    scenario_label="Canada — Pharmaceutical",

    locale=LocaleConfig(
        country_code="CA", country_name="Canada",
        currency_symbol="C$", currency_code="CAD",
        currency_prefix=True,
        large_number_suffix="M", large_number_divisor=1_000_000,
    ),

    company=CompanyConfig(
        name="NovaBio Health",
        product_name="NovaBio SmartDose Insulin System",
        tagline="Connected insulin delivery for Canadian patients",
        location="Montreal, Quebec",
        role_title="VP of Finance & Strategy",
        founding_year="2021",
        industry_label="Pharmaceutical — Insulin Delivery",
        unit_price=3_600.0,         # C$3,600/patient/yr (lower than US due to pCPA negotiation)
        unit_price_label="Annual Therapy Cost",
        unit_cost=1_200.0,
        year1_capacity=6_000,
        capacity_unit="patients",
    ),

    financials=FinancialConfig(
        total_budget=20_000_000,
        fixed_costs=30_000_000,
        base_revenue=12_000_000,
        profit_reinvestment_rate=0.03,
        inflation_min=0.03,
        inflation_max=0.09,
        underuse_threshold=0.15,
        underuse_penalty_rate=2.5,
        max_change_rate=0.30,
        demand_noise_std=0.08,
        scenario_drift_std=0.03,
        risk_penalty_lambda=1.5,
        num_periods=5,
        num_eval_scenarios=30,
        state_decay=0.5,
        vpi_ras_floor=-2_469_460,
        vpi_ras_ceiling=15_988_550,
        vpi_share_floor=21.8,
        vpi_share_ceiling=27.09,
        competitor_presence_baseline=140_000_000,
    ),

    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    departments=[
        DepartmentParams(
            name="R&D", S_max=28_000_000, K=6_000_000, alpha=1.3,
            decay=0.55, min_spend=1_200_000, max_spend=10_000_000,
            state_sensitivity=0.12, catch_up_rate=0.25, sweet_spot_frac=0.70,
        ),
        DepartmentParams(
            name="Sales", S_max=20_000_000, K=4_800_000, alpha=0.9,
            decay=0.20, min_spend=1_600_000, max_spend=10_000_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Operations", S_max=24_000_000, K=3_600_000, alpha=0.85,
            decay=0.55, min_spend=1_200_000, max_spend=8_000_000,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Marketing", S_max=22_000_000, K=4_400_000, alpha=1.05,
            decay=0.40, min_spend=1_000_000, max_spend=8_000_000,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.65,
        ),
    ],

    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd",
            description=(
                "R&D drives clinical evidence, device innovation, and Health Canada filings. "
                "Returns are DELAYED by one year. Strong R&D creates powerful synergy with Sales: "
                "published Canadian clinical data is what gets you onto provincial formularies."
            ),
            background_description="R&D conducts clinical studies at Canadian medical centres, develops cold-climate-optimized pen hardware, manages Health Canada submissions, and builds bilingual software features.",
        ),DepartmentMeta(
            name="Sales", color_key="dept_sales",
            description=(
                "Sales covers physician relationships, provincial formulary access, and pCPA "
                "negotiations. Returns are immediate but CAPPED by Operations. Losing a provincial "
                "formulary listing is extremely hard to reverse."
            ),
            background_description="Sales negotiates with provincial drug plans through pCPA, manages hospital formulary access, builds pharmacy partnerships, and runs patient enrollment across Canada.",
        ),DepartmentMeta(
            name="Operations", color_key="dept_ops",
            description=(
                "Operations is the BOTTLENECK. Pharmaceutical manufacturing requires Health Canada "
                "GMP compliance, cold-chain logistics (critical in Canadian winters), and quality "
                "systems. The cap on Sales is tight — pharma supply chains are unforgiving."
            ),
            background_description="Operations runs the Montreal GMP facility, manages cold-chain logistics across Canada's vast geography, ensures Health Canada compliance, and handles bilingual packaging.",
        ),DepartmentMeta(
            name="Marketing", color_key="dept_mktg",
            description=(
                "Marketing builds physician awareness through medical education, conferences, and "
                "patient support programs. Direct-to-consumer prescription advertising is BANNED in "
                "Canada — your marketing must work through professional and educational channels. Returns follow an S-curve — below a threshold your message is lost in noise, above it you build compounding brand equity among physicians and patients."
            ),
        
            background_description="Marketing builds physician awareness through medical education, Diabetes Canada conference sponsorships, patient support programmes, and community outreach. Direct-to-consumer prescription advertising is not permitted in Canada.",
        ),
    ],department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    segments=[
        ConsumerSegment(
            key="provincial",
            label="Provincial Drug Plans",
            description=(
                "Each province maintains its own approved drug list. Getting listed through the "
                "pan-Canadian Pharmaceutical Alliance (pCPA) is essential for volume but requires "
                "price negotiation and strong clinical evidence. Represent ~38% of the market."
            ),
            market_weight=0.38,
        ),
        ConsumerSegment(
            key="private",
            label="Employer Insurance Plans",
            description=(
                "Patients covered by employer-sponsored private insurance through Sun Life, Manulife, "
                "Great-West Life. Faster formulary access than provincial plans but still requires "
                "clinical evidence. Represent ~25% of the market."
            ),
            market_weight=0.25,
        ),
        ConsumerSegment(
            key="hospital",
            label="Hospital Purchasing",
            description=(
                "Health system procurement through group purchasing organizations like HealthPRO. "
                "Hospitals standardize on one insulin pen. Clinical evidence and reliability "
                "matter most. Represent ~22% of the market."
            ),
            market_weight=0.22,
        ),
        ConsumerSegment(
            key="northern",
            label="Northern & Remote Communities",
            description=(
                "Indigenous communities and remote northern populations served through NIHB and "
                "territorial health programs. Cold-chain logistics and device durability are "
                "critical. Price-sensitive but government-funded. Represent ~15% of the market."
            ),
            market_weight=0.15,
        ),
    ],

    segment_colors={"provincial": "#3D6B50", "private": "#4A7B9D", "hospital": "#C27D3A", "northern": "#8B6BAE"},

    sub_decisions={
        "R&D": DepartmentSubDecisions(
            dept_name="R&D", label="R&D Focus",
            tooltip="Choose your clinical and device development priority this year.",
            options={
                "clinical": SubDecisionOption(
                    key="clinical", label="Canadian Clinical Outcomes Studies",
                    description="Run real-world evidence trials at Canadian centres to prove superior outcomes for pCPA submissions.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Sales": 0.12, "Marketing": 0.03},
                    segment_multipliers={"provincial": 1.35, "private": 1.20, "hospital": 1.30, "northern": 0.90},
                ),
                "device": SubDecisionOption(
                    key="device", label="Cold-Climate Device Engineering",
                    description="Optimize pen hardware for Canadian conditions — arctic-rated materials, extended battery life in cold.",
                    smax_mult=1.25, k_mult=1.30,
                    synergy={"Marketing": 0.10},
                    segment_multipliers={"provincial": 1.00, "private": 0.90, "hospital": 0.95, "northern": 1.50},
                ),
                "costreduce": SubDecisionOption(
                    key="costreduce", label="Manufacturing Cost Reduction",
                    description="Optimize formulation and production to lower per-patient cost for pCPA price negotiations.",
                    smax_mult=0.90, k_mult=0.75,
                    synergy={"Operations": 0.15, "Sales": 0.05},
                    segment_multipliers={"provincial": 1.40, "private": 1.20, "hospital": 1.15, "northern": 1.25},
                ),
                "software": SubDecisionOption(
                    key="software", label="Bilingual Digital Health Platform",
                    description="Build out the connected app with full English/French support, telehealth integration, and AI features.",
                    smax_mult=1.20, k_mult=1.25,
                    synergy={"Marketing": 0.08},
                    segment_multipliers={"provincial": 1.10, "private": 1.15, "hospital": 1.00, "northern": 0.85},
                ),
            },
            default="clinical",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales", label="Sales Channel Strategy",
            tooltip="Choose your primary go-to-market channel. Sales is CAPPED by Operations.",
            options={
                "formulary": SubDecisionOption(
                    key="formulary", label="Provincial Formulary Push",
                    description="Dedicate team to pCPA negotiations and individual provincial drug plan listings.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Operations": 0.05},
                    segment_multipliers={"provincial": 1.50, "private": 0.85, "hospital": 0.80, "northern": 1.10},
                ),
                "hospital": SubDecisionOption(
                    key="hospital", label="Hospital & Health System Sales",
                    description="Target hospital formulary committees and group purchasing organizations.",
                    smax_mult=1.10, k_mult=1.05, synergy={"Operations": 0.10},
                    segment_multipliers={"provincial": 0.85, "private": 0.90, "hospital": 1.55, "northern": 0.95},
                ),
                "patient": SubDecisionOption(
                    key="patient", label="Patient Access Programs",
                    description="Build patient assistance, free trial, and support programs for uninsured Canadians.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Marketing": 0.10},
                    segment_multipliers={"provincial": 1.10, "private": 1.15, "hospital": 0.80, "northern": 1.35},
                ),
                "specialist": SubDecisionOption(
                    key="specialist", label="Endocrinologist Engagement",
                    description="Deploy field medical liaisons to endocrinology practices with Canadian clinical evidence.",
                    smax_mult=1.05, k_mult=0.90, synergy={"R&D": 0.08},
                    segment_multipliers={"provincial": 1.05, "private": 1.10, "hospital": 1.20, "northern": 0.85},
                ),
            },
            default="formulary",
        ),
        "Operations": DepartmentSubDecisions(
            dept_name="Operations", label="Operations Priority",
            tooltip="Choose your supply chain focus. Operations CAPS Sales.",
            options={
                "capacity": SubDecisionOption(
                    key="capacity", label="Manufacturing Scale-Up",
                    description="Expand GMP production capacity at Montreal facility.",
                    smax_mult=1.20, k_mult=1.05, synergy={"Sales": 0.10},
                    segment_multipliers={"provincial": 1.20, "private": 1.10, "hospital": 1.25, "northern": 0.90},
                ),
                "coldchain": SubDecisionOption(
                    key="coldchain", label="Arctic Cold Chain & Northern Distribution",
                    description="Invest in extreme-temperature logistics for year-round delivery to all Canadian communities.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Sales": 0.05, "Marketing": 0.05},
                    segment_multipliers={"provincial": 1.05, "private": 0.95, "hospital": 1.00, "northern": 1.50},
                ),
                "quality": SubDecisionOption(
                    key="quality", label="Quality Systems & Health Canada Compliance",
                    description="Strengthen GMP systems, prepare for inspections, reduce defect rates.",
                    smax_mult=1.05, k_mult=0.85, synergy={"R&D": 0.05},
                    segment_multipliers={"provincial": 1.10, "private": 1.05, "hospital": 1.20, "northern": 1.10},
                ),
                "redundancy": SubDecisionOption(
                    key="redundancy", label="Supply Chain Redundancy",
                    description="Dual-source API, build safety stock, establish backup site for cross-border resilience.",
                    smax_mult=1.10, k_mult=1.00, synergy={"Sales": 0.08},
                    segment_multipliers={"provincial": 1.15, "private": 1.10, "hospital": 1.10, "northern": 1.05},
                ),
            },
            default="capacity",
        ),
        # NOTE: No DTC option — prescription drug advertising to consumers is BANNED in Canada
        "Marketing": DepartmentSubDecisions(
            dept_name="Marketing", label="Marketing Strategy",
            tooltip="In Canada, direct-to-consumer prescription advertising is banned. Marketing works through professional and educational channels.",
            options={
                "medical": SubDecisionOption(
                    key="medical", label="Medical Education & Conferences",
                    description="Sponsor CDA conferences, publish in CMAJ, build relationships with Canadian endocrinology leaders.",
                    smax_mult=1.20, k_mult=1.15, synergy={"R&D": 0.10},
                    segment_multipliers={"provincial": 1.15, "private": 1.05, "hospital": 1.35, "northern": 0.90},
                ),
                "patientprog": SubDecisionOption(
                    key="patientprog", label="Patient Support & Education Programs",
                    description="Diabetes management programs, bilingual nurse educator hotlines, peer support communities.",
                    smax_mult=1.15, k_mult=1.00, synergy={"Sales": 0.08},
                    segment_multipliers={"provincial": 1.10, "private": 1.20, "hospital": 0.95, "northern": 1.30},
                ),
                "value": SubDecisionOption(
                    key="value", label="Health Economics for Payer Presentations",
                    description="Commission Canadian cost-effectiveness studies for pCPA and provincial drug plan submissions.",
                    smax_mult=1.10, k_mult=0.90, synergy={"Sales": 0.12},
                    segment_multipliers={"provincial": 1.45, "private": 1.15, "hospital": 1.10, "northern": 1.05},
                ),
                "community": SubDecisionOption(
                    key="community", label="Community & Indigenous Outreach",
                    description="Partner with Indigenous health organizations, community diabetes programs, and northern clinics.",
                    smax_mult=1.05, k_mult=1.05, synergy={"Sales": 0.06, "R&D": 0.04},
                    segment_multipliers={"provincial": 0.90, "private": 0.85, "hospital": 0.95, "northern": 1.55},
                ),
            },
            default="medical",
        ),
    },

    competitors=[
        CompetitorDef(
            name="NordicBio Canada",
            industry="Global insulin leader — Canadian operations",
            location="Mississauga, Ontario (HQ: Copenhagen)",
            founded="1923",
            description=(
                "Canadian subsidiary of the world's dominant insulin manufacturer. Deep provincial "
                "formulary relationships, decades of physician trust, and massive scale. "
                "Slow to innovate on connected delivery but unmatched in distribution."
            ),
            display_label="Global Insulin Leader (Canadian Arm)",
            base_revenue=95_000_000, growth_rate=0.04, margin=0.22,
            base_specs={"efficacy": 82, "usability": 55, "cost": 4100},
            spec_growth_rates={"efficacy": 1.5, "usability": 3.0, "cost": 80},
            base_reach=1.35,  # Deep HCP relationships across Canadian provinces,
        ),
        CompetitorDef(
            name="CanPharm Therapeutics",
            industry="Canadian biosimilar manufacturer",
            location="Toronto, Ontario",
            founded="2012",
            description=(
                "Canadian-owned biosimilar company with strong pCPA relationships and competitive "
                "pricing. No connected pen capability but deep understanding of Canadian "
                "regulatory and reimbursement landscape."
            ),
            display_label="Canadian Biosimilar Specialist",
            base_revenue=55_000_000, growth_rate=0.10, margin=0.13,
            base_specs={"efficacy": 78, "usability": 48, "cost": 2600},
            spec_growth_rates={"efficacy": 1.0, "usability": 2.0, "cost": -80},
            base_reach=1.0,  # Established in generics, building brand,
        ),
        CompetitorDef(
            name="AmeriPharma Canada",
            industry="US pharma major — Canadian subsidiary",
            location="Toronto, Ontario (HQ: Indianapolis)",
            founded="1876",
            description=(
                "Canadian operations of American pharma giant. Strong physician relationships "
                "and recently launched a basic connected pen. Larger marketing budget than "
                "most Canadian competitors."
            ),
            display_label="US Pharma Major (Canadian Arm)",
            base_revenue=75_000_000, growth_rate=0.05, margin=0.18,
            base_specs={"efficacy": 80, "usability": 60, "cost": 3600},
            spec_growth_rates={"efficacy": 1.8, "usability": 3.5, "cost": 70},
            base_reach=1.2,  # Strong payer access, provincial formulary presence,
        ),
        CompetitorDef(
            name="MedBridge Digital Health",
            industry="Canadian digital health startup",
            location="Vancouver, British Columbia",
            founded="2020",
            description=(
                "Vancouver-based digital health startup with a software-first approach. "
                "Beautiful app, strong tech talent from BC's startup ecosystem, but limited "
                "clinical evidence and no pharmaceutical sales experience."
            ),
            display_label="Canadian Digital Health Rival",
            base_revenue=18_000_000, growth_rate=0.20, margin=0.05,
            base_specs={"efficacy": 74, "usability": 82, "cost": 3200},
            spec_growth_rates={"efficacy": 2.5, "usability": 6.0, "cost": 40},
            base_reach=0.65,  # Early-stage commercial reach,
        ),
    ],

    competitor_labels={
        "NordicBio Canada": "Global Insulin Leader (Canadian Arm)",
        "CanPharm Therapeutics": "Canadian Biosimilar Specialist",
        "AmeriPharma Canada": "US Pharma Major (Canadian Arm)",
        "MedBridge Digital Health": "Canadian Digital Health Rival",
    },

    product_specs=[
        ProductSpec(key="efficacy", label="Clinical Efficacy", unit="score", base_value=77, higher_is_better=True),
        ProductSpec(key="usability", label="Device Usability", unit="score", base_value=70, higher_is_better=True),
        ProductSpec(key="cost", label="Therapy Cost", unit="C$/yr", base_value=3600, higher_is_better=False, display_format=",.0f"),
    ],

    spec_evolution_rules=[
        SpecEvolutionRule(
            spec_key="efficacy", dept_name="R&D",
            base_growth=1.0, spend_sensitivity=5.0, dept_budget_ref=5_000_000,
            sub_decision_bonuses={"clinical": 4.0, "device": 1.0, "costreduce": -1.0, "software": 2.0},
            min_value=65, max_value=98,
        ),
        SpecEvolutionRule(
            spec_key="usability", dept_name="R&D",
            base_growth=1.5, spend_sensitivity=6.0, dept_budget_ref=5_000_000,
            sub_decision_bonuses={"device": 5.0, "software": 4.0, "clinical": 1.0, "costreduce": -2.0},
            min_value=50, max_value=98,
        ),
        SpecEvolutionRule(
            spec_key="cost", dept_name="R&D",
            base_growth=40, spend_sensitivity=-160, dept_budget_ref=5_000_000,
            sub_decision_bonuses={"costreduce": -320, "clinical": 80, "device": 120, "software": 80},
            min_value=1200, max_value=5000,
        ),
    ],

    segment_spec_preferences={
        "provincial": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.35, ideal_value=88, tolerance=15),
            SegmentSpecPreference(spec_key="usability", weight=0.20, ideal_value=75, tolerance=20),
            SegmentSpecPreference(spec_key="cost", weight=0.45, ideal_value=2500, tolerance=1200),
        ],
        "private": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.40, ideal_value=86, tolerance=14),
            SegmentSpecPreference(spec_key="usability", weight=0.30, ideal_value=80, tolerance=18),
            SegmentSpecPreference(spec_key="cost", weight=0.30, ideal_value=3200, tolerance=1400),
        ],
        "hospital": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.45, ideal_value=90, tolerance=12),
            SegmentSpecPreference(spec_key="usability", weight=0.25, ideal_value=78, tolerance=18),
            SegmentSpecPreference(spec_key="cost", weight=0.30, ideal_value=3000, tolerance=1400),
        ],
        "northern": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.25, ideal_value=82, tolerance=18),
            SegmentSpecPreference(spec_key="usability", weight=0.35, ideal_value=85, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.40, ideal_value=2200, tolerance=1200),
        ],
    },

    performance_index_name="NPI",
    performance_index_full="NovaBio Performance Index",
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
        world_headline="The year is 2025. Canada's insulin market is evolving — and the rules are different here.",
        world_body=(
            "Canada's pharmaceutical market operates under a system unlike anywhere else. Provincial "
            "drug plans control formulary access through the pan-Canadian Pharmaceutical Alliance, Health "
            "Canada's regulatory process is rigorous but slower than the FDA, and bilingual requirements "
            "touch every label, every patient brochure, and every digital interface. The insulin market "
            "is dominated by global giants who have spent decades building provincial formulary relationships. "
            "Biosimilars are gaining acceptance but face physician inertia. Meanwhile, Northern and remote "
            "communities — home to some of Canada's highest diabetes rates — remain chronically underserved. "
            "The companies that navigate pCPA negotiations, build bilingual patient ecosystems, and earn "
            "physician trust from Vancouver to St. John's will reshape Canadian diabetes care."
        ),
        market_body=(
            "The Canadian insulin delivery market is valued at C$3.2B annually, with connected "
            "devices representing the fastest-growing segment. Four distinct access channels "
            "determine how patients receive their insulin."
        ),
        market_kpis=[
            ("Market Size", "C$3.2B annually", "dept_rd"),
            ("Smart Pen Growth", "22% CAGR", "accent"),
            ("Channels", "4 access pathways", "dept_mktg"),
        ],
        segments_intro="Each channel has different gatekeepers and evidence requirements.",
        company_subtitle="Founded 2021  ·  Montreal, QC  ·  200 employees  ·  TSX-V: NVBO",
        company_body=(
            "NovaBio Health launched from a Montreal laboratory where its founder — a former McGill "
            "endocrinologist — spent seven years developing a biosimilar insulin formulation optimized "
            "for Canadian cold-chain distribution. The SmartDose connected pen was designed with bilingual "
            "interfaces from the start, tested through Quebec winters, and validated in a Health Canada "
            "trial that attracted attention from provincial drug plans. The company has secured its first "
            "pCPA agreement and has early traction in Ontario hospital systems. But expanding into every "
            "province, building a bilingual sales force, and earning formulary access from coast to coast "
            "is the challenge that will define whether NovaBio becomes a national player or stays a "
            "regional curiosity."
        ),
        product_subtitle="Smart Insulin Pen — Connected care for all Canadians",
        product_body=(
            "The SmartDose is a reusable connected insulin pen with bilingual English/French "
            "app support, CGM integration, and cold-weather optimized hardware. Annual therapy "
            "cost per patient is approximately C$3,600. Year 1 capacity: 6,000 patients."
        ),
        product_kpis=[
            ("Therapy Cost", "C$3,600/yr", "dept_rd"),
            ("Efficacy Score", "77/100", "accent"),
            ("Usability Score", "70/100", "dept_sales"),
            ("Yr 1 Capacity", "6,000 patients", "dept_ops"),
        ],
        role_body=(
            "You are responsible for allocating NovaBio's annual operating budget across four "
            "departments over a 5-year window. In Canada, prescription drug advertising to "
            "consumers is banned — your Marketing strategy must work through professional "
            "and educational channels."
        ),
        objective_body=(
            "Your NPI score (0–1000+) is based on risk-adjusted profitability (50%) and "
            "Canadian insulin market share (50%)."
        ),
        departments_intro="Each department has distinct mechanics. R&D evidence drives formulary access — the key Canadian synergy.",
        competitors_intro="These competitors are already established in Canadian hospitals and pharmacies.",
        ready_headline="Your journey starts now — Canadian patients need better options.",
        ready_body=(
            "No DTC advertising. Bilingual everything. Provincial drug plans that negotiate as a bloc. "
            "And Northern communities that need care but are a thousand kilometres from the nearest "
            "hospital. You have the science and the technology. Now you need the strategy to reach "
            "35 million Canadians across 10 million square kilometres. Five years."
        ),
    ),

    briefing=BriefingContent(
        world_body=(
            "Canada's insulin market is controlled by provincial drug plans through pCPA, with bilingual "
            "requirements on every touchpoint. Global insulin giants have decades of formulary relationships. "
            "Biosimilars are gaining acceptance but face physician inertia. Northern and remote communities "
            "remain chronically underserved. DTC prescription advertising is banned."
        ),
        market_body=(
            "The Canadian insulin delivery market is C$3.2B annually with connected devices growing at 22%. "
            "Four channels: provincial plans, private insurance, hospitals, and northern communities."
        ),
        company_body=(
            "NovaBio Health is a Montreal biotech with Health Canada approval and early pCPA traction. "
            "Bilingual SmartDose platform, 200 employees. Founded by a former McGill endocrinologist. "
            "The challenge: expand from Ontario success to all 13 provinces and territories."
        ),
        product_body=(
            "The SmartDose pen with bilingual app, CGM integration, and cold-weather design. "
            "C$3,600/patient/year. Year 1 capacity: 6,000 patients."
        ),
        product_kpis=[
            ("Therapy Cost", "C$3,600/yr", "dept_rd"),
            ("Efficacy Score", "77/100", "accent"),
            ("Usability Score", "70/100", "dept_sales"),
            ("Yr 1 Capacity", "6,000 patients", "dept_ops"),
        ],
        role_body=(
            "Allocate budget across R&D, Sales, Operations, and Marketing. No DTC advertising — "
            "Marketing works through medical education and patient programs. R&D evidence "
            "directly enables provincial formulary access."
        ),
        objective_body=(
            "NPI score based on risk-adjusted profitability (50%) and market share (50%)."
        ),
    ),
    objective_text={},
)


register_scenario("ca", "pharma", CA_PHARMA)
