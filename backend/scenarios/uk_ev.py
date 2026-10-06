"""
scenarios/uk_ev.py — United Kingdom × Electric Vehicles scenario.

Albion Motors — a growth-stage British EV manufacturer based in Coventry,
launching the Meridian Electric Saloon into the UK's competitive EV market.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.uk_ev_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


UK_EV = ScenarioDefinition(
    scenario_id="uk_ev",
    scenario_label="United Kingdom — Electric Vehicles",

    # Locale
    locale=LocaleConfig(
        country_code="GB",
        country_name="United Kingdom",
        currency_symbol="£",
        currency_code="GBP",
        currency_prefix=True,
        large_number_suffix="M",
        large_number_divisor=1_000_000,
    ),

    # Company
    company=CompanyConfig(
        name="Albion Motors",
        product_name="Albion Meridian Electric Saloon",
        tagline="British EV engineering, reimagined",
        location="Coventry, West Midlands",
        role_title="VP of Finance & Strategy",
        founding_year="2021",
        industry_label="Electric Vehicles",
        unit_price=36_000.0,
        unit_price_label="MSRP",
        unit_cost=24_000.0,
        year1_capacity=14_000,
        capacity_unit="units",
    ),

    # Financials
    financials=FinancialConfig(
        total_budget=48_000_000,
        fixed_costs=78_000_000,
        base_revenue=32_000_000,
        profit_reinvestment_rate=0.03,
        inflation_min=0.05,
        inflation_max=0.14,
        underuse_threshold=0.15,
        underuse_penalty_rate=2.5,
        max_change_rate=0.30,
        demand_noise_std=0.08,
        scenario_drift_std=0.03,
        risk_penalty_lambda=1.5,
        num_periods=5,
        num_eval_scenarios=30,
        state_decay=0.5,
        vpi_ras_floor=5_004_160,
        vpi_ras_ceiling=55_614_700,
        vpi_share_floor=10.44,
        vpi_share_ceiling=13.31,
        competitor_presence_baseline=260_000_000,
    ),

    # Timer
    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    # Departments
    departments=[
        DepartmentParams(
            name="R&D", S_max=64_000_000, K=12_800_000, alpha=1.3,
            decay=0.6, min_spend=2_400_000, max_spend=24_000_000,
            state_sensitivity=0.12, catch_up_rate=0.25, sweet_spot_frac=0.70,
        ),
        DepartmentParams(
            name="Sales", S_max=48_000_000, K=11_200_000, alpha=0.9,
            decay=0.15, min_spend=4_000_000, max_spend=24_000_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Operations", S_max=64_000_000, K=7_200_000, alpha=0.85,
            decay=0.55, min_spend=3_200_000, max_spend=20_000_000,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Marketing", S_max=64_000_000, K=8_000_000, alpha=1.05,
            decay=0.40, min_spend=2_400_000, max_spend=20_000_000,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.65,
        ),
    ],

    # Department display metadata
    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd",
            description=(
                "Research & Development drives long-term innovation — critical for compact urban "
                "platforms and connected car technology. Returns are DELAYED by one year. "
                "R&D sub-decisions unlock synergy bonuses for other departments. "
                "Sustained investment compounds, making future spending more effective."
            ),
            background_description="R&D covers compact vehicle engineering, right-hand-drive platform development, software systems, and performance tuning for European driving conditions.",
        ),DepartmentMeta(
            name="Sales", color_key="dept_sales",
            description=(
                "Sales converts demand into orders across the UK — from London showrooms to Scottish "
                "dealerships. The company car and BIK channel is critical. Returns are immediate "
                "but CAPPED by Operations capacity. Cutting sales budget causes a fast drop in bookings."
            ),
            background_description="Sales manages dealer relationships, company car fleet partnerships, direct ordering, and negotiations with leasing companies across the UK.",
        ),DepartmentMeta(
            name="Operations", color_key="dept_ops",
            description=(
                "Operations is the BOTTLENECK. It determines production capacity that caps Sales. "
                "Post-Brexit customs and rules-of-origin compliance add complexity to UK manufacturing. "
                "Under-investing in Operations while Sales is high means lost orders."
            ),
            background_description="Operations runs the Coventry production facility, manages post-Brexit supply chains, handles UK-wide distribution, and maintains quality standards.",
        ),DepartmentMeta(
            name="Marketing", color_key="dept_mktg",
            description=(
                "Marketing builds brand awareness across the UK and positions the brand for company "
                "car buyers, retail customers, and fleet operators. Returns follow an S-curve — "
                "over-spending past the sweet spot wastes budget. Brand equity fades without reinforcement."
            ),
        
            background_description="Marketing builds brand awareness through value messaging, technology leadership campaigns, performance positioning, and sustainability branding. The team manages campaigns across the UK's diverse media landscape.",
        ),
    ],department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    # Consumer Segments
    segments=[
        ConsumerSegment(
            key="costconscious",
            label="Cost-Conscious Urban Commuters",
            description=(
                "Middle-income households seeking affordable EVs for daily commuting in congested "
                "British cities. Highly sensitive to purchase price, running costs, and congestion "
                "charge exemptions. Represent ~38% of the addressable market."
            ),
            market_weight=0.38,
        ),
        ConsumerSegment(
            key="tech",
            label="Connected Tech Professionals",
            description=(
                "Affluent professionals in London, Manchester, and Edinburgh who prioritise "
                "connected features, OTA updates, ADAS, and digital UX. Many are company car "
                "choosers influenced by BIK tax rates. Represent ~23% of the addressable market."
            ),
            market_weight=0.23,
        ),
        ConsumerSegment(
            key="enthusiast",
            label="Motoring Enthusiasts",
            description=(
                "Drivers who demand best-in-class acceleration, handling dynamics, and driving "
                "pleasure. Britain's rich motoring heritage means this segment values performance "
                "and brand prestige. Represent ~17% of the addressable market."
            ),
            market_weight=0.17,
        ),
        ConsumerSegment(
            key="fleet",
            label="Fleet & Company Car Buyers",
            description=(
                "Corporate fleets, leasing companies, and government bodies. The UK's BIK tax "
                "advantage for EVs is a powerful driver. Prioritise reliability, residual values, "
                "and total cost of ownership. Represent ~22% of the addressable market."
            ),
            market_weight=0.22,
        ),
    ],

    segment_colors={"costconscious": "#3D6B50", "tech": "#4A7B9D", "enthusiast": "#C27D3A", "fleet": "#8B6BAE"},

    # Sub-Decisions
    sub_decisions={
        "R&D": DepartmentSubDecisions(
            dept_name="R&D",
            label="R&D Focus",
            tooltip=(
                "Choose where your engineering team directs its energy this year. "
                "Each focus modifies R&D's return curve and can boost other departments."
            ),
            options={
                "compact": SubDecisionOption(
                    key="compact",
                    label="Compact Urban Platform",
                    description="Optimise the platform for narrow British streets, urban parking, and efficiency.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Sales": 0.08, "Marketing": 0.05},
                    segment_multipliers={"costconscious": 1.40, "tech": 1.05, "enthusiast": 0.75, "fleet": 1.25},
                ),
                "software": SubDecisionOption(
                    key="software",
                    label="Connected Car & OTA Software",
                    description="Invest in ADAS, over-the-air updates, and an industry-leading digital cockpit.",
                    smax_mult=1.25, k_mult=1.30,
                    synergy={"Marketing": 0.12},
                    segment_multipliers={"costconscious": 0.75, "tech": 1.50, "enthusiast": 1.00, "fleet": 1.05},
                ),
                "cost": SubDecisionOption(
                    key="cost",
                    label="Cost Reduction Engineering",
                    description="Optimise cell chemistry and production to lower the sticker price below £35,000.",
                    smax_mult=0.90, k_mult=0.75,
                    synergy={"Operations": 0.15, "Sales": 0.05},
                    segment_multipliers={"costconscious": 1.45, "tech": 0.70, "enthusiast": 0.65, "fleet": 1.35},
                ),
                "performance": SubDecisionOption(
                    key="performance",
                    label="Performance Powertrain",
                    description="Develop a high-output dual-motor platform with class-leading acceleration and handling.",
                    smax_mult=1.20, k_mult=1.25,
                    synergy={"Marketing": 0.10},
                    segment_multipliers={"costconscious": 0.65, "tech": 1.15, "enthusiast": 1.55, "fleet": 0.70},
                ),
            },
            default="compact",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales",
            label="Sales Channel Strategy",
            tooltip=(
                "Choose your go-to-market channel. Sales revenue is CAPPED by Operations "
                "capacity — you cannot sell more vehicles than you can produce."
            ),
            options={
                "direct": SubDecisionOption(
                    key="direct",
                    label="Direct-to-Consumer Online",
                    description="Company-owned experience centres in London, Manchester, and Edinburgh with online ordering.",
                    smax_mult=1.10, k_mult=1.05,
                    synergy={"Marketing": 0.08},
                    segment_multipliers={"costconscious": 0.85, "tech": 1.40, "enthusiast": 1.15, "fleet": 0.75},
                ),
                "companycar": SubDecisionOption(
                    key="companycar",
                    label="Company Car & BIK Channel",
                    description="Dedicated team targeting fleet managers and salary sacrifice scheme operators leveraging 2% BIK rate.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Operations": 0.10},
                    segment_multipliers={"costconscious": 0.80, "tech": 1.10, "enthusiast": 0.70, "fleet": 1.55},
                ),
                "dealer": SubDecisionOption(
                    key="dealer",
                    label="Franchise Dealer Network",
                    description="Partner with established British dealership groups for nationwide coverage.",
                    smax_mult=0.95, k_mult=0.80,
                    synergy={"Operations": 0.05},
                    segment_multipliers={"costconscious": 1.30, "tech": 0.75, "enthusiast": 0.90, "fleet": 1.15},
                ),
                "partnerships": SubDecisionOption(
                    key="partnerships",
                    label="Premium Brand Partnerships",
                    description="Co-brand with complementary British brands for cross-selling and experiential marketing.",
                    smax_mult=1.10, k_mult=1.15,
                    synergy={"Marketing": 0.12, "R&D": 0.05},
                    segment_multipliers={"costconscious": 0.90, "tech": 1.20, "enthusiast": 1.35, "fleet": 0.85},
                ),
            },
            default="companycar",
        ),
        "Operations": DepartmentSubDecisions(
            dept_name="Operations",
            label="Operations Priority",
            tooltip=(
                "Choose your operational focus. Operations capacity CAPS Sales delivery — "
                "invest here to unlock the Sales ceiling."
            ),
            options={
                "throughput": SubDecisionOption(
                    key="throughput",
                    label="Factory Throughput & Automation",
                    description="Maximise units-per-hour at the Coventry plant through robotics and lean manufacturing.",
                    smax_mult=1.20, k_mult=1.05,
                    synergy={"Sales": 0.10},
                    segment_multipliers={"costconscious": 1.25, "tech": 1.00, "enthusiast": 0.90, "fleet": 1.30},
                ),
                "localcontent": SubDecisionOption(
                    key="localcontent",
                    label="UK Local Content & Rules of Origin",
                    description="Increase UK-sourced content to meet post-Brexit rules-of-origin for tariff-free EU export.",
                    smax_mult=1.10, k_mult=1.15,
                    synergy={"Marketing": 0.08, "Sales": 0.05},
                    segment_multipliers={"costconscious": 1.10, "tech": 0.95, "enthusiast": 1.05, "fleet": 1.20},
                ),
                "supply_chain": SubDecisionOption(
                    key="supply_chain",
                    label="Supply Chain Resilience",
                    description="Dual-source critical components and build strategic inventory against Channel port disruptions.",
                    smax_mult=1.05, k_mult=0.85,
                    synergy={"R&D": 0.05},
                    segment_multipliers={"costconscious": 1.10, "tech": 0.90, "enthusiast": 0.95, "fleet": 1.20},
                ),
                "service": SubDecisionOption(
                    key="service",
                    label="After-Sales Service & Warranty",
                    description="Expand service centres across UK regions and extend warranty to build loyalty and residual values.",
                    smax_mult=1.10, k_mult=1.00,
                    synergy={"Sales": 0.08, "Marketing": 0.06},
                    segment_multipliers={"costconscious": 1.20, "tech": 1.05, "enthusiast": 1.10, "fleet": 1.15},
                ),
            },
            default="throughput",
        ),
        "Marketing": DepartmentSubDecisions(
            dept_name="Marketing",
            label="Marketing Message",
            tooltip=(
                "Choose your brand positioning. Marketing builds long-term brand equity but "
                "has the lowest sweet spot — over-spending wastes budget fastest here."
            ),
            options={
                "value": SubDecisionOption(
                    key="value",
                    label="Affordability & BIK Tax Savings",
                    description="Position on total cost of ownership and the 2% BIK tax advantage for company car drivers.",
                    smax_mult=1.05, k_mult=0.90,
                    synergy={"Sales": 0.10},
                    segment_multipliers={"costconscious": 1.45, "tech": 0.80, "enthusiast": 0.65, "fleet": 1.35},
                ),
                "tech": SubDecisionOption(
                    key="tech",
                    label="Technology & Innovation Leadership",
                    description="Lead with software, ADAS, and cutting-edge connected features.",
                    smax_mult=1.20, k_mult=1.15,
                    synergy={"R&D": 0.08},
                    segment_multipliers={"costconscious": 0.70, "tech": 1.55, "enthusiast": 1.10, "fleet": 0.90},
                ),
                "performance": SubDecisionOption(
                    key="performance",
                    label="British Performance Heritage",
                    description="Emphasise driving dynamics, acceleration, and the thrill of electric motoring in the British tradition.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"R&D": 0.05, "Sales": 0.05},
                    segment_multipliers={"costconscious": 0.65, "tech": 1.10, "enthusiast": 1.55, "fleet": 0.75},
                ),
                "green": SubDecisionOption(
                    key="green",
                    label="Green Credentials & Sustainability",
                    description="Net-zero supply chain, UK-sourced renewable energy, ethical mineral sourcing.",
                    smax_mult=1.10, k_mult=1.00,
                    synergy={"Sales": 0.04, "Operations": 0.04},
                    segment_multipliers={"costconscious": 1.10, "tech": 1.20, "enthusiast": 0.80, "fleet": 1.25},
                ),
            },
            default="value",
        ),
    },

    # Competitors
    competitors=[
        CompetitorDef(
            name="Zenith Electric",
            industry="British EV startup",
            location="Oxford, United Kingdom",
            founded="2018",
            description=(
                "Oxford-based EV startup with strong ties to the university research ecosystem. "
                "Known for lightweight engineering and efficient powertrains. Growing rapidly "
                "among tech-forward urban buyers but limited production scale."
            ),
            display_label="British EV Innovator",
            base_revenue=190_000_000, growth_rate=0.10, margin=0.13,
            base_specs={"range": 280, "battery": 68, "accel": 3.9},
            spec_growth_rates={"range": 14.0, "battery": 4.0, "accel": -0.14},
            base_reach=1.1,  # Patriotic brand appeal, growing UK recognition,
        ),
        CompetitorDef(
            name="Volta UK",
            industry="European premium EV",
            location="Stuttgart, Germany",
            founded="2012",
            description=(
                "Premium European EV brand with deep engineering heritage. Strong in the "
                "performance and company car segments. High margins but challenged by "
                "post-Brexit tariff rules on UK-bound imports."
            ),
            display_label="Premium European EV Brand",
            base_revenue=380_000_000, growth_rate=0.07, margin=0.18,
            base_specs={"range": 320, "battery": 82, "accel": 3.2},
            spec_growth_rates={"range": 12.0, "battery": 3.5, "accel": -0.10},
            base_reach=1.2,  # Strong premium positioning across UK,
        ),
        CompetitorDef(
            name="Lingwei Motors UK",
            industry="Chinese EV entrant",
            location="Shenzhen, China",
            founded="2017",
            description=(
                "Aggressive Chinese manufacturer entering the UK market with ultra-competitive "
                "pricing and rapid model refresh cycles. Strong battery cost advantage but "
                "faces brand trust and after-sales network challenges with British buyers."
            ),
            display_label="Low-Cost Chinese Challenger",
            base_revenue=280_000_000, growth_rate=0.12, margin=0.09,
            base_specs={"range": 260, "battery": 64, "accel": 5.3},
            spec_growth_rates={"range": 20.0, "battery": 6.0, "accel": -0.20},
            base_reach=0.75,  # Limited UK brand trust, regulatory uncertainty,
        ),
        CompetitorDef(
            name="Sterling Heritage EV",
            industry="Legacy British OEM",
            location="Birmingham, United Kingdom",
            founded="1948",
            description=(
                "Venerable British automaker undergoing an EV transition. Nationwide dealer "
                "network and deep brand recognition are assets; legacy costs, union complexity, "
                "and slow software culture are structural disadvantages."
            ),
            display_label="Legacy British OEM in Transition",
            base_revenue=260_000_000, growth_rate=0.04, margin=0.07,
            base_specs={"range": 270, "battery": 68, "accel": 4.9},
            spec_growth_rates={"range": 10.0, "battery": 2.5, "accel": -0.05},
            base_reach=1.15,  # Deep UK dealer network and heritage brand,
        ),
    ],

    competitor_labels={
        "Zenith Electric": "British EV Innovator",
        "Volta UK": "Premium European EV Brand",
        "Lingwei Motors UK": "Low-Cost Chinese Challenger",
        "Sterling Heritage EV": "Legacy British OEM in Transition",
    },

    # Product Specs
    product_specs=[
        ProductSpec(key="range", label="Range (WLTP)", unit="mi", base_value=290, higher_is_better=True),
        ProductSpec(key="battery", label="Battery", unit="kWh", base_value=72, higher_is_better=True),
        ProductSpec(key="accel", label="0–60 mph", unit="sec", base_value=4.2, higher_is_better=False, display_format=".1f"),
    ],

    # Spec Evolution Rules
    spec_evolution_rules=[
        SpecEvolutionRule(
            spec_key="range", dept_name="R&D",
            base_growth=5.0,
            spend_sensitivity=18.0,
            dept_budget_ref=12_000_000,
            sub_decision_bonuses={"compact": 12.0, "cost": -5.0, "software": 3.0, "performance": 8.0},
            min_value=230, max_value=500,
        ),
        SpecEvolutionRule(
            spec_key="battery", dept_name="R&D",
            base_growth=2.0,
            spend_sensitivity=7.0,
            dept_budget_ref=12_000_000,
            sub_decision_bonuses={"compact": 5.0, "cost": -2.0, "software": 1.0, "performance": 4.0},
            min_value=58, max_value=140,
        ),
        SpecEvolutionRule(
            spec_key="accel", dept_name="R&D",
            base_growth=-0.05,
            spend_sensitivity=-0.28,
            dept_budget_ref=12_000_000,
            sub_decision_bonuses={"performance": -0.4, "compact": 0.1, "cost": 0.2, "software": -0.1},
            min_value=2.0, max_value=6.0,
        ),
    ],

    # Segment Spec Preferences
    segment_spec_preferences={
        "costconscious": [
            SegmentSpecPreference(spec_key="range", weight=0.55, ideal_value=330, tolerance=90),
            SegmentSpecPreference(spec_key="battery", weight=0.28, ideal_value=80, tolerance=25),
            SegmentSpecPreference(spec_key="accel", weight=0.17, ideal_value=5.0, tolerance=2.0),
        ],
        "tech": [
            SegmentSpecPreference(spec_key="range", weight=0.35, ideal_value=350, tolerance=80),
            SegmentSpecPreference(spec_key="battery", weight=0.25, ideal_value=95, tolerance=30),
            SegmentSpecPreference(spec_key="accel", weight=0.40, ideal_value=3.5, tolerance=1.5),
        ],
        "enthusiast": [
            SegmentSpecPreference(spec_key="range", weight=0.25, ideal_value=370, tolerance=80),
            SegmentSpecPreference(spec_key="battery", weight=0.15, ideal_value=100, tolerance=30),
            SegmentSpecPreference(spec_key="accel", weight=0.60, ideal_value=2.8, tolerance=1.2),
        ],
        "fleet": [
            SegmentSpecPreference(spec_key="range", weight=0.58, ideal_value=350, tolerance=80),
            SegmentSpecPreference(spec_key="battery", weight=0.33, ideal_value=85, tolerance=25),
            SegmentSpecPreference(spec_key="accel", weight=0.09, ideal_value=5.0, tolerance=3.0),
        ],
    },

    # Performance index
    performance_index_name="API",
    performance_index_full="Albion Performance Index",
    market_label="EV market",

    # Bottleneck / synergy rules
    bottleneck_cap_dept_idx=2,
    bottleneck_capped_dept_idx=1,
    bottleneck_cap_fraction=0.85,
    delayed_return_dept_idx=0,
    brand_equity_depts=[(3, 1.0), (0, 0.5)],

    # News pools
    general_news_pool=GENERAL_NEWS_POOL,
    dept_news_pool=DEPT_NEWS_POOL,
    competitor_news_pool=COMPETITOR_NEWS_POOL,

    # Storyboard
    storyboard=StoryboardContent(
        world_headline="The year is 2025. Britain's EV transition is accelerating — but the road is contested.",
        world_body=(
            "The UK government's 2030 ICE sales ban is approaching, Benefit-in-Kind tax advantages "
            "are driving corporate EV adoption, and post-Brexit trade rules are reshaping automotive "
            "supply chains. Meanwhile, Chinese manufacturers are flooding British showrooms with "
            "budget-priced EVs, and European rivals face new rules-of-origin tariffs. Battery costs "
            "are falling but energy prices remain volatile. The companies that allocate capital wisely "
            "will define the next decade of British motoring."
        ),
        market_body=(
            "The UK passenger EV market is growing at 30% annually and is projected to reach "
            "£38B by 2030. Four distinct consumer groups contest the market — each shaped by "
            "Britain's urban density, company car culture, and motoring heritage."
        ),
        market_kpis=[
            ("Market Size", "£38B by 2030", "dept_rd"),
            ("Growth Rate", "30% annually", "accent"),
            ("Segments", "4 consumer groups", "dept_mktg"),
        ],
        segments_intro="Winning in the UK requires matching product features to Britain's unique buyer needs.",
        company_subtitle="Founded 2021  ·  Coventry, West Midlands  ·  800 employees  ·  LSE: ALBN",
        company_body=(
            "Albion Motors is a growth-stage British EV manufacturer that has successfully delivered "
            "two niche electric sports cars to market. The company has strong engineering talent — "
            "many recruited from Jaguar Land Rover and Aston Martin — a loyal early-adopter fanbase, "
            "and a lean but scalable manufacturing facility in Coventry's historic automotive heartland. "
            "The previous CFO departed last quarter to join a European rival. "
            "You are stepping in ahead of the company's most ambitious product launch yet."
        ),
        product_subtitle="All-Electric Saloon — British engineering meets electric innovation",
        product_body=(
            "The Albion Meridian is the company's entry into the mass-market UK EV segment — "
            "a 5-seat all-electric saloon targeting a starting MSRP of £36,000. "
            "It is engineered on a new skateboard platform with a 72 kWh battery pack, "
            "rear-wheel drive with optional AWD, and an OTA-capable software stack. "
            "The Meridian is designed for British roads — compact dimensions, sharp handling, "
            "and class-leading efficiency. Year 1 production capacity is 14,000 units."
        ),
        product_kpis=[
            ("MSRP", "£36,000", "dept_rd"),
            ("Range (WLTP)", "290 mi", "accent"),
            ("0–60 mph", "4.2 sec", "dept_sales"),
            ("Yr 1 Capacity", "14,000 units", "dept_ops"),
        ],
        role_body=(
            "You are responsible for allocating Albion Motors' annual operating budget across four "
            "departments — R&D, Sales, Operations, and Marketing — over a 5-year launch window. "
            "Each year you set budgets AND choose a strategic direction for each department. "
            "Your decisions are final: once a year is locked, you cannot revisit it."
        ),
        objective_body=(
            "Your API score (0–1000+) is based on two equally weighted components: "
            "risk-adjusted profitability (50%) and UK EV market share (50%). "
            "Consistent earnings beat volatile ones. Broad market presence beats narrow niches."
        ),
        departments_intro="Each department has distinct mechanics that affect your bottom line.",
        competitors_intro="You won't be operating in a vacuum. These rivals want the same British customers.",
        ready_headline="Your journey starts now — the Meridian awaits.",
        ready_body=(
            "You have been briefed on the UK market, the company, the product, your role, "
            "and the competition. The background and objective tabs will remain available as "
            "reference during the simulation. Trust your strategy — allocate wisely."
        ),
    ),

    # Briefing
    briefing=BriefingContent(
        world_body=(
            "The year is 2025. Britain's EV transition is accelerating — but the road is contested. "
            "The 2030 ICE ban looms, BIK tax advantages are driving corporate adoption, and post-Brexit "
            "trade rules reshape supply chains. Chinese manufacturers offer budget EVs while European "
            "rivals navigate tariffs. Battery costs fall but energy prices remain volatile. "
            "The companies that allocate wisely will define the next decade of British motoring."
        ),
        market_body=(
            "The UK passenger EV market is growing at 30% annually and is projected to reach "
            "£38B by 2030. Four distinct consumer groups contest the market, each shaped by "
            "Britain's urban density, company car culture, and motoring heritage. Winning requires "
            "spend directed at the right features for British buyers."
        ),
        company_body=(
            "Albion Motors is a growth-stage British EV manufacturer that has successfully delivered "
            "two niche electric sports cars to market. The company has strong engineering talent, "
            "a loyal early-adopter fanbase, and a lean but scalable manufacturing facility in "
            "Coventry. The previous CFO departed last quarter. You are stepping in ahead of "
            "the company's most ambitious product launch yet."
        ),
        product_body=(
            "The Albion Meridian is the company's entry into the mass-market UK EV segment — "
            "a 5-seat all-electric saloon targeting a starting MSRP of £36,000. The Meridian "
            "competes directly with European imports and Chinese challengers in the UK's "
            "highly competitive market. Designed for British roads with a 72 kWh battery, "
            "sharp handling, and OTA software. Year 1 capacity is 14,000 units. "
            "The Meridian's success determines whether Albion becomes a mainstream British EV "
            "brand — or remains a niche player."
        ),
        product_kpis=[
            ("MSRP", "£36,000", "dept_rd"),
            ("Range (WLTP)", "290 mi", "accent"),
            ("0–60 mph", "4.2 sec", "dept_sales"),
            ("Yr 1 Capacity", "14,000 units", "dept_ops"),
        ],
        role_body=(
            "You are responsible for allocating Albion Motors' annual operating budget across four "
            "departments — R&D, Sales, Operations, and Marketing — over a 5-year launch window. "
            "Each year you set budgets AND choose a strategic direction for each department. "
            "These sub-decisions shape which consumer segments the Meridian appeals to and "
            "directly influence revenue. Your decisions are final."
        ),
        objective_body=(
            "Your API score (0–1000+) is based on two equally weighted components: "
            "risk-adjusted profitability (50%) and UK EV market share (50%). "
            "Consistent earnings beat volatile ones. Broad market presence beats narrow niches. "
            "The best scores come from balancing both."
        ),
    ),
    objective_text={},
)


register_scenario("uk", "ev", UK_EV)
