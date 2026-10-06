"""United States x Electric Vehicles scenario.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    CompetitorPersonality,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)


from scenarios.us_ev_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL



US_EV = ScenarioDefinition(
    scenario_id="us_ev",
    scenario_label="United States — Electric Vehicles",

    # Locale
    locale=LocaleConfig(
        country_code="US",
        country_name="United States",
        currency_symbol="$",
        currency_code="USD",
        currency_prefix=True,
        large_number_suffix="M",
        large_number_divisor=1_000_000,
    ),

    # Company
    company=CompanyConfig(
        name="Voltex Motors",
        product_name="Voltex Xeno EV Coupe",
        tagline="Growth-stage American EV manufacturer",
        location="Austin, Texas",
        role_title="VP of Finance & Strategy",
        founding_year="2022",
        industry_label="Electric Vehicles",
        unit_price=42_000.0,
        unit_price_label="MSRP",
        unit_cost=28_000.0,
        year1_capacity=18_000,
        capacity_unit="units",
    ),

    # Financials
    financials=FinancialConfig(
        total_budget=60_000_000,
        fixed_costs=95_000_000,
        base_revenue=40_000_000,
        profit_reinvestment_rate=0.03,
        inflation_min=0.06,
        inflation_max=0.15,
        underuse_threshold=0.15,
        underuse_penalty_rate=3.0,
        max_change_rate=0.30,
        demand_noise_std=0.08,
        scenario_drift_std=0.03,
        risk_penalty_lambda=1.5,
        num_periods=5,
        num_eval_scenarios=30,
        state_decay=0.5,
 
        vpi_ras_floor=-65_000_000,
        vpi_ras_ceiling=200_000_000,
        vpi_share_floor=1.0,
        vpi_share_ceiling=35.0,
        competitor_presence_baseline=400_000_000,
    ),

    # Timer
    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    # Departments
    departments=[
        DepartmentParams(
            name="R&D", S_max=80_000_000, K=16_000_000, alpha=1.3,
            decay=0.6, min_spend=3_000_000, max_spend=30_000_000,
            state_sensitivity=0.12, catch_up_rate=0.25, sweet_spot_frac=0.70,
        ),
        DepartmentParams(
            name="Sales", S_max=60_000_000, K=14_000_000, alpha=0.9,
            decay=0.15, min_spend=5_000_000, max_spend=30_000_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Operations", S_max=80_000_000, K=9_000_000, alpha=0.85,
            decay=0.55, min_spend=4_000_000, max_spend=25_000_000,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Marketing", S_max=80_000_000, K=10_000_000, alpha=1.05,
            decay=0.40, min_spend=3_000_000, max_spend=25_000_000,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.65,
        ),
    ],

    # Department display metadata
    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd",
            description=(
                "Research & Development drives long-term innovation such as battery technology, "
                "powertrain engineering, software, and safety testing. Returns are DELAYED by one year. "
                "R&D sub-decisions unlock synergy bonuses for other departments. "
                "Sustained investment compounds, making future spending more effective."
            ),
            background_description="R&D covers battery technology development, powertrain engineering, software platform improvements, and vehicle safety testing. The team includes materials scientists, firmware engineers, and test drivers.",
        ),
        DepartmentMeta(
            name="Sales", color_key="dept_sales",
            description=(
                "Sales converts demand into orders through methods liks dealer networks, direct-to-consumer channels, "
                "fleet partnerships, and corporate sales. Returns are immediate but CAPPED by Operations "
                "capacity (you cannot sell more than you can produce). "
                "Cutting sales budget causes a fast drop in bookings."
            ),
            background_description="Sales manages dealer network relationships, direct-to-consumer ordering, fleet partnerships, and corporate sales. This team converts consumer interest into signed purchase orders.",
        ),
        DepartmentMeta(
            name="Operations", color_key="dept_ops",
            description=(
                "Operations runs the factory  with vehicle assembly, battery production, quality control, "
                "supplier management, and logistics. Operations is the BOTTLENECK. It determines "
                "production capacity that caps Sales. Under-investing in Operations while Sales is high means lost orders. "
                "Steady investment compounds via carry-over."
            ),
            background_description="Operations is responsible for end-to-end production including assembling vehicles, manufacturing battery packs to ensuring quality, coordinating suppliers, and managing logistics. This is where every delivered car is brought to life.",
        ),
        DepartmentMeta(
            name="Marketing", color_key="dept_mktg",
            description=(
                "Marketing builds brand awareness and demand through value messaging, performance "
                "positioning, technology campaigns, and sustainability branding. Returns follow an "
                "S-curve with minimal at low spend, strong above threshold, but over-spending past the "
                "sweet spot wastes budget. Brand equity persists but fades without reinforcement."
            ),
            background_description="Marketing connects the product to the customer. It shapes the brand, launches vehicles, and creates campaigns that highlight design, performance, and EV technology to drive sales.",
        ),
    ],

    # Department colors
    department_colors={
        "R&D": "#4A7B9D",
        "Sales": "#C27D3A",
        "Operations": "#3D7A5A",
        "Marketing": "#8B6BAE",
    },

    # Consumer Segments
    segments=[
        ConsumerSegment(
            key="budget",
            label="Budget-Conscious Families",
            description=(
                "Middle-income households seeking affordable EVs as a practical alternative "
                "to gas cars. Highly sensitive to sticker price and total cost of ownership. "
                "Represent ~35% of the addressable EV market."
            ),
            market_weight=0.35,
        ),
        ConsumerSegment(
            key="tech",
            label="Tech-Savvy Early Adopters",
            description=(
                "Affluent, urban professionals who prioritize cutting-edge features such as, OTA software "
                "updates, autonomous driving aids, connected apps, and digital UX. "
                "Represent ~25% of the addressable EV market."
            ),
            market_weight=0.25,
        ),
        ConsumerSegment(
            key="performance",
            label="Performance Enthusiasts",
            description=(
                "Drivers who demand best-in-class range, acceleration, and driving dynamics. "
                "Willing to pay a premium for a superior product. "
                "Represent ~20% of the addressable EV market."
            ),
            market_weight=0.20,
        ),
        ConsumerSegment(
            key="fleet",
            label="Fleet & Commercial Buyers",
            description=(
                "Corporations, rideshare operators, and government agencies purchasing in volume. "
                "Prioritise reliability, serviceability, and total cost of ownership at scale. "
                "Represent ~20% of the addressable EV market."
            ),
            market_weight=0.20,
        ),
    ],

    # Segment colors
    segment_colors={
        "budget": "#3D6B50",
        "tech": "#4A7B9D",
        "performance": "#C27D3A",
        "fleet": "#8B6BAE",
    },

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
                "range": SubDecisionOption(
                    key="range",
                    label="Extended Range & Battery Life",
                    description="Push energy density by targeting 400+ mile range.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Sales": 0.08, "Marketing": 0.05},
                    segment_multipliers={"budget": 1.20, "tech": 1.10, "performance": 1.30, "fleet": 1.25},
                ),
                "software": SubDecisionOption(
                    key="software",
                    label="Autonomous Driving & Software",
                    description="Invest in ADAS (Advanced Driver Assistance Systems), OTA(Over-the-Air) updates, and an industry-leading digital cockpit.",
                    smax_mult=1.25, k_mult=1.30,
                    synergy={"Marketing": 0.12},
                    segment_multipliers={"budget": 0.70, "tech": 1.50, "performance": 1.00, "fleet": 1.05},
                ),
                "cost": SubDecisionOption(
                    key="cost",
                    label="Cost Reduction & Manufacturing",
                    description="Optimise cell chemistry and production to lower the sticker price.",
                    smax_mult=0.90, k_mult=0.75,
                    synergy={"Operations": 0.15, "Sales": 0.05},
                    segment_multipliers={"budget": 1.45, "tech": 0.70, "performance": 0.65, "fleet": 1.30},
                ),
                "performance": SubDecisionOption(
                    key="performance",
                    label="Performance & Powertrain",
                    description="Develop a high-output dual-motor platform with class-leading acceleration.",
                    smax_mult=1.20, k_mult=1.25,
                    synergy={"Marketing": 0.10},
                    segment_multipliers={"budget": 0.65, "tech": 1.15, "performance": 1.55, "fleet": 0.70},
                ),
            },
            default="range",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales",
            label="Sales Channel Strategy",
            tooltip=(
                "Choose your go-to-market channel. Sales revenue is CAPPED by Operations "
                "capacity."
            ),
            options={
                "direct": SubDecisionOption(
                    key="direct",
                    label="Direct-to-Consumer",
                    description="Company-owned showrooms, online ordering, and home delivery.",
                    smax_mult=1.10, k_mult=1.05,
                    synergy={"Marketing": 0.08},
                    segment_multipliers={"budget": 0.90, "tech": 1.40, "performance": 1.15, "fleet": 0.75},
                ),
                "fleet": SubDecisionOption(
                    key="fleet",
                    label="Fleet & B2B Enterprise",
                    description="Dedicated enterprise sales team targeting corporate and government fleets.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Operations": 0.10},
                    segment_multipliers={"budget": 0.80, "tech": 0.85, "performance": 0.70, "fleet": 1.60},
                ),
                "dealer": SubDecisionOption(
                    key="dealer",
                    label="Franchise Dealer Network",
                    description="Partner with established dealerships for wide geographic coverage.",
                    smax_mult=0.95, k_mult=0.80,
                    synergy={"Operations": 0.05},
                    segment_multipliers={"budget": 1.30, "tech": 0.75, "performance": 0.85, "fleet": 1.15},
                ),
                "partnerships": SubDecisionOption(
                    key="partnerships",
                    label="Strategic Brand Partnerships",
                    description="Co-brand with complementary companies for cross-selling and bundled offers.",
                    smax_mult=1.10, k_mult=1.15,
                    synergy={"Marketing": 0.12, "R&D": 0.05},
                    segment_multipliers={"budget": 1.10, "tech": 1.20, "performance": 1.00, "fleet": 0.90},
                ),
            },
            default="direct",
        ),
        "Operations": DepartmentSubDecisions(
            dept_name="Operations",
            label="Operations Priority",
            tooltip=(
                "Choose your operational focus. Operations capacity CAPS Sales delivery"
            ),
            options={
                "throughput": SubDecisionOption(
                    key="throughput",
                    label="Factory Throughput & Automation",
                    description="Maximise units-per-hour through robotics and lean manufacturing.",
                    smax_mult=1.20, k_mult=1.05,
                    synergy={"Sales": 0.10},
                    segment_multipliers={"budget": 1.25, "tech": 1.00, "performance": 0.90, "fleet": 1.30},
                ),
                "charging": SubDecisionOption(
                    key="charging",
                    label="Charging Network Expansion",
                    description="Build proprietary fast-charging stations along major corridors.",
                    smax_mult=1.10, k_mult=1.15,
                    synergy={"Marketing": 0.08, "Sales": 0.05},
                    segment_multipliers={"budget": 1.15, "tech": 1.20, "performance": 1.10, "fleet": 1.00},
                ),
                "supply_chain": SubDecisionOption(
                    key="supply_chain",
                    label="Supply Chain Resilience",
                    description="Dual-source critical components and build strategic inventory buffers.",
                    smax_mult=1.05, k_mult=0.85,
                    synergy={"R&D": 0.05},
                    segment_multipliers={"budget": 1.10, "tech": 0.90, "performance": 0.95, "fleet": 1.20},
                ),
                "service": SubDecisionOption(
                    key="service",
                    label="After-Sales Service & Warranty",
                    description="Expand service centres and extend warranty coverage to build loyalty.",
                    smax_mult=1.10, k_mult=1.00,
                    synergy={"Sales": 0.08, "Marketing": 0.06},
                    segment_multipliers={"budget": 1.20, "tech": 1.05, "performance": 1.10, "fleet": 1.15},
                ),
            },
            default="throughput",
        ),
        "Marketing": DepartmentSubDecisions(
            dept_name="Marketing",
            label="Marketing Message",
            tooltip=(
                "Choose your brand positioning. Marketing builds long-term brand equity but "
                "over-spending wastes budget fastest here."
            ),
            options={
                "value": SubDecisionOption(
                    key="value",
                    label="Affordability & TCO (Total Cost of Ownership)",
                    description="Position on total cost of ownership (investing means cheaper to buy, own, and run).",
                    smax_mult=1.05, k_mult=0.90,
                    synergy={"Sales": 0.10},
                    segment_multipliers={"budget": 1.50, "tech": 0.75, "performance": 0.65, "fleet": 1.25},
                ),
                "tech": SubDecisionOption(
                    key="tech",
                    label="Technology & Innovation Leadership",
                    description="Lead with software, autonomy, and cutting-edge features.",
                    smax_mult=1.20, k_mult=1.15,
                    synergy={"R&D": 0.08},
                    segment_multipliers={"budget": 0.70, "tech": 1.55, "performance": 1.10, "fleet": 0.90},
                ),
                "performance": SubDecisionOption(
                    key="performance",
                    label="Performance & Driving Excitement",
                    description="Emphasise acceleration, handling, and the thrill of electric driving.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"R&D": 0.05, "Sales": 0.05},
                    segment_multipliers={"budget": 0.65, "tech": 1.10, "performance": 1.55, "fleet": 0.75},
                ),
                "green": SubDecisionOption(
                    key="green",
                    label="Sustainability & Green Mission",
                    description="Net-zero supply chain, ethical sourcing, green credentials.",
                    smax_mult=1.10, k_mult=1.00,
                    synergy={"Sales": 0.04, "Operations": 0.04},
                    segment_multipliers={"budget": 1.05, "tech": 1.20, "performance": 0.80, "fleet": 1.30},
                ),
            },
            default="tech",
        ),
    },

    # Competitors
    competitors=[
        CompetitorDef(
            name="Solara Automotive",
            industry="Electric Vehicles",
            location="Palo Alto, USA",
            founded="2014",
            description=(
                "Silicon Valley EV disruptor known for its software-first philosophy and "
                "over-the-air update ecosystem. Strong brand among tech adopters; "
                "challenged on manufacturing scale and service network."
            ),
            display_label="Silicon Valley EV Disruptor",
            base_revenue=280_000_000, growth_rate=0.10, margin=0.14,
            starting_specs={"range": 305, "battery": 92, "accel": 3.4},
            personality=CompetitorPersonality(
                total_budget=60_000_000,
                base_allocation_weights={"R&D": 0.40, "Sales": 0.15, "Operations": 0.15, "Marketing": 0.30},
                sub_decision_prefs={
                    "R&D":        [("software", 0.65), ("range", 0.15), ("performance", 0.15), ("cost", 0.05)],
                    "Sales":      [("direct", 0.70), ("partnerships", 0.20), ("dealer", 0.05), ("fleet", 0.05)],
                    "Operations": [("charging", 0.45), ("throughput", 0.25), ("supply_chain", 0.20), ("service", 0.10)],
                    "Marketing":  [("tech", 0.70), ("performance", 0.15), ("green", 0.10), ("value", 0.05)],
                },
                strategic_iq=0.60,
                noise_factor=0.20,
                starting_brand_equity=80_000_000,
                spending_tendency="R&D and Marketing heavy: Bets on software innovation and brand",
            ),
            # Legacy fallback fields (used if personality system is bypassed)
            base_specs={"range": 305, "battery": 92, "accel": 3.4},
            spec_growth_rates={"range": 7.0, "battery": 7.0, "accel": -0.08},
            base_reach=1.35,
        ),
        CompetitorDef(
            name="Halo Electric",
            industry="Electric Vehicles",
            location="Munich, Germany",
            founded="2010",
            description=(
                "Premium European EV brand with a heritage of engineering excellence. "
                "Targets performance and luxury segments. High margins but limited volume; "
                "expanding into the mass-market with a new mid-size coupe."
            ),
            display_label="Premium European EV Brand",
            base_revenue=450_000_000, growth_rate=0.08, margin=0.18,
            starting_specs={"range": 310, "battery": 78, "accel": 2.5},
            personality=CompetitorPersonality(
                total_budget=65_000_000,
                base_allocation_weights={"R&D": 0.35, "Sales": 0.20, "Operations": 0.20, "Marketing": 0.25},
                sub_decision_prefs={
                    "R&D":        [("performance", 0.75), ("range", 0.15), ("software", 0.05), ("cost", 0.05)],
                    "Sales":      [("direct", 0.60), ("partnerships", 0.25), ("dealer", 0.10), ("fleet", 0.05)],
                    "Operations": [("throughput", 0.30), ("charging", 0.30), ("service", 0.30), ("supply_chain", 0.10)],
                    "Marketing":  [("performance", 0.65), ("tech", 0.20), ("green", 0.10), ("value", 0.05)],
                },
                strategic_iq=0.50,
                noise_factor=0.20,
                starting_brand_equity=150_000_000,
                spending_tendency="Performance-obsessed: Pours R&D into powertrain and acceleration",
            ),
            base_specs={"range": 310, "battery": 78, "accel": 2.5},
            spec_growth_rates={"range": 8.0, "battery": 3.0, "accel": -0.25},
            base_reach=1.25,
        ),
        CompetitorDef(
            name="BrightDrive Motors",
            industry="Electric Vehicles",
            location="Shenzhen, China",
            founded="2017",
            description=(
                "Aggressive Chinese EV manufacturer with ultra-low-cost battery technology "
                "and rapid global expansion. Dominant in budget segments; accelerating "
                "into Western markets with competitive pricing."
            ),
            display_label="Low-Cost Chinese EV Challenger",
            base_revenue=350_000_000, growth_rate=0.12, margin=0.1,
            starting_specs={"range": 270, "battery": 68, "accel": 5.5},
            personality=CompetitorPersonality(
                total_budget=40_000_000,
                base_allocation_weights={"R&D": 0.20, "Sales": 0.25, "Operations": 0.35, "Marketing": 0.20},
                sub_decision_prefs={
                    "R&D":        [("cost", 0.70), ("range", 0.20), ("software", 0.05), ("performance", 0.05)],
                    "Sales":      [("dealer", 0.50), ("fleet", 0.30), ("direct", 0.10), ("partnerships", 0.10)],
                    "Operations": [("throughput", 0.55), ("supply_chain", 0.30), ("service", 0.10), ("charging", 0.05)],
                    "Marketing":  [("value", 0.70), ("green", 0.20), ("tech", 0.05), ("performance", 0.05)],
                },
                strategic_iq=0.20,
                noise_factor=0.25,
                starting_brand_equity=20_000_000,
                spending_tendency="Cost-focused with heavy Operations spend: Competing on price",
            ),
            base_specs={"range": 270, "battery": 68, "accel": 5.5},
            spec_growth_rates={"range": 6.0, "battery": 3.0, "accel": -0.05},
            base_reach=0.50,
        ),
        CompetitorDef(
            name="Apex Legacy Auto (EV Division)",
            industry="Electric Vehicles",
            location="Detroit, USA",
            founded="1962",
            description=(
                "Legacy automaker undergoing a forced EV transition. Large dealer network "
                "and brand recognition are assets; legacy costs and slow software culture "
                "create structural disadvantages against pure-play rivals."
            ),
            display_label="Legacy OEM in Transition",
            base_revenue=320_000_000, growth_rate=0.04, margin=0.08,
            starting_specs={"range": 350, "battery": 92, "accel": 4.8},
            personality=CompetitorPersonality(
                total_budget=90_000_000,
                base_allocation_weights={"R&D": 0.25, "Sales": 0.30, "Operations": 0.30, "Marketing": 0.15},
                sub_decision_prefs={
                    "R&D":        [("range", 0.60), ("cost", 0.25), ("software", 0.10), ("performance", 0.05)],
                    "Sales":      [("fleet", 0.50), ("dealer", 0.35), ("direct", 0.10), ("partnerships", 0.05)],
                    "Operations": [("throughput", 0.50), ("supply_chain", 0.30), ("service", 0.15), ("charging", 0.05)],
                    "Marketing":  [("value", 0.55), ("green", 0.25), ("tech", 0.15), ("performance", 0.05)],
                },
                strategic_iq=0.70,
                noise_factor=0.15,
                starting_brand_equity=200_000_000,
                spending_tendency="Heavy Operations and Sales investor with fleet-focused distribution",
            ),
            base_specs={"range": 350, "battery": 92, "accel": 4.8},
            spec_growth_rates={"range": 24.0, "battery": 10.0, "accel": -0.02},
            base_reach=1.75,
        ),
    ],

    # Competitor display labels
    competitor_labels={
        "Solara Automotive": "Silicon Valley EV Disruptor",
        "Halo Electric": "Premium European EV Brand",
        "BrightDrive Motors": "Low-Cost Chinese EV Challenger",
        "Apex Legacy Auto (EV Division)": "Legacy OEM in Transition",
    },

    # Product Specs
    # The visible metrics that evolve each year
    product_specs=[
        ProductSpec(key="range", label="Range (EPA)", unit="mi", base_value=310, higher_is_better=True),
        ProductSpec(key="battery", label="Battery", unit="kWh", base_value=75, higher_is_better=True),
        ProductSpec(key="accel", label="0-60 mph", unit="sec", base_value=4.1, higher_is_better=False, display_format=".1f"),
    ],

    # Spec Evolution Rules
    # How each spec changes based on R&D spend and sub-decisions
    spec_evolution_rules=[
        # Range: driven by R&D, boosted by "Extended Range" sub-decision
        SpecEvolutionRule(
            spec_key="range", dept_name="R&D",
            base_growth=0.0,           # No free improvement — must invest in R&D
            spend_sensitivity=12.0,    # +12 mi/yr at full budget reference spend
            dept_budget_ref=15_000_000,
            sub_decision_bonuses={"range": 10.0, "cost": -3.0, "software": 2.0, "performance": 5.0},
            min_value=250, max_value=550,
        ),
        # Battery: driven by R&D, boosted by "Extended Range"
        SpecEvolutionRule(
            spec_key="battery", dept_name="R&D",
            base_growth=0.0,           # No free improvement — must invest in R&D
            spend_sensitivity=5.0,     # +5 kWh/yr at full spend
            dept_budget_ref=15_000_000,
            sub_decision_bonuses={"range": 4.0, "cost": -1.0, "software": 0.5, "performance": 2.5},
            min_value=60, max_value=150,
        ),
        # Acceleration: driven by R&D, boosted by "Performance" (lower is better)
        SpecEvolutionRule(
            spec_key="accel", dept_name="R&D",
            base_growth=0.0,           # No free improvement — must invest in R&D
            spend_sensitivity=-0.2,    # -0.2s/yr at full spend
            dept_budget_ref=15_000_000,
            sub_decision_bonuses={"performance": -0.25, "range": 0.05, "cost": 0.1, "software": -0.08},
            min_value=2.0, max_value=6.0,
        ),
    ],

    # Segment Spec Preferences
    # How much each segment values each spec (weights sum to ~1.0)
    segment_spec_preferences={
        "budget": [
            SegmentSpecPreference(spec_key="range", weight=0.45, ideal_value=420, tolerance=50),
            SegmentSpecPreference(spec_key="battery", weight=0.40, ideal_value=115, tolerance=18),
            SegmentSpecPreference(spec_key="accel", weight=0.15, ideal_value=5.0, tolerance=1.5),
        ],
        "tech": [
            SegmentSpecPreference(spec_key="range", weight=0.20, ideal_value=380, tolerance=50),
            SegmentSpecPreference(spec_key="battery", weight=0.50, ideal_value=125, tolerance=18),
            SegmentSpecPreference(spec_key="accel", weight=0.30, ideal_value=2.5, tolerance=0.6),
        ],
        "performance": [
            SegmentSpecPreference(spec_key="range", weight=0.15, ideal_value=400, tolerance=60),
            SegmentSpecPreference(spec_key="battery", weight=0.10, ideal_value=110, tolerance=20),
            SegmentSpecPreference(spec_key="accel", weight=0.75, ideal_value=2.2, tolerance=0.4),
        ],
        "fleet": [
            SegmentSpecPreference(spec_key="range", weight=0.40, ideal_value=430, tolerance=50),
            SegmentSpecPreference(spec_key="battery", weight=0.50, ideal_value=120, tolerance=18),
            SegmentSpecPreference(spec_key="accel", weight=0.10, ideal_value=5.0, tolerance=2.0),
        ],
    },

    # Performance index
    performance_index_name="VPI",
    performance_index_full="Voltex Performance Index",
    market_label="US EV Market",

    # Bottleneck / synergy rules
    bottleneck_cap_dept_idx=2,       # Operations
    bottleneck_capped_dept_idx=1,    # Sales
    bottleneck_cap_fraction=0.85,
    delayed_return_dept_idx=0,       # R&D
    brand_equity_depts=[(3, 1.0), (0, 0.5)],  # Marketing + 0.5*R&D

    # News pools (imported from us_ev_news.py)
    general_news_pool=GENERAL_NEWS_POOL,
    dept_news_pool=DEPT_NEWS_POOL,
    competitor_news_pool=COMPETITOR_NEWS_POOL,

    # Storyboard content
    storyboard=StoryboardContent(
        # Step 0: The World
        world_headline=(
            "The year is 2025. The land grab for the American EV market has begun."
        ),
        world_body=(
            "Ten percent penetration crossed. The Inflation Reduction Act rewired consumer economics overnight. "
            "Charging corridors are multiplying, but the heartland is still skeptical.\n\n"
            "Legacy automakers are burning billions on the transition, and some will not survive it. "
            "Chinese manufacturers have arrived with sub-$30K vehicles, and Western governments are scrambling to respond. "
            "Lithium prices swung 40% in twelve months. Battery costs are falling, but supply chains are not stable. "
            "The next five years will be a ruthless filter. The companies that emerge will have built "
            "real businesses, not just market cap stories.\n\n"
            "The winners nail three things simultaneously:\n\n"
            "* A product people actually want to drive\n"
            "* A factory that can build it profitably\n"
            "* A brand that earns trust beyond the coasts.\n\n"
            "You are about to make the calls that determine which side of that line YOU land on."
        ),

        # Step 1: The Market
        market_body=(
            "The US passenger EV market is growing at 32% annually and is expected to reach "
            "$800B by 2030. Four distinct consumer groups exist in the market from price conscious "
            "families to corporate fleet managers. Each with radically different priorities.\n\n"
            "Click on the different consumer segments to learn more about them."
        ),
        market_kpis=[
            ("Market Size", "$800B by 2030", "dept_rd"),
            ("Growth Rate", "32% annually", "accent"),
            ("Segments", "4 consumer groups", "dept_mktg"),
        ],

        # Step 2: Consumer Segments
        segments_intro="Each segment cares about different things. The family buyer wants affordable range and price. The tech enthusiast wants bleeding-edge features. The fleet manager wants cheap total cost of ownership.",

        # Step 3: Your Company
        company_subtitle="Founded 2022  ·  Austin, Texas  ·  1,200 employees  ·  NASDAQ: VLTX",
        company_body=(
            "Voltex Motors started in a converted warehouse on the outskirts of Austin, founded by a "
            "former battery engineer who believed that American EV startups were building the wrong cars, "
            "for the wrong people. Instead of chasing luxury, Voltex focused on the middle of the market, "
            "families who wanted to go electric but could not justify $80,000. Two niche electric pickups "
            "proved the manufacturing competence. A loyal early-adopter fanbase evangelised the brand.\n\n"
            "Now Voltex is about to launch the Xeno, a mass-market electric coupe priced at $42,000 that "
            "could make or break the company. The previous CFO retired last quarter. You are stepping "
            "in ahead of the most consequential product launch in Voltex history. "
            "You will get $60 million every year for five years. "
            "The legacy automakers are watching. So are the short sellers.\n\n"
            "Click on the items to learn more information about the company."
        ),

        # Step 4: The Product
        product_subtitle="All-Electric Coupe: The make-or-break launch",
        product_body=(
            "The Voltex Xeno is the company's entry into the mass-market passenger EV segment. "
            "A 5-seat all-electric coupe targeting a starting MSRP of $42,000 with:\n\n"
            "* 75 kWh battery pack\n"
            "* Dual-motor AWD (All wheel drive)\n"
            "* OTA-capable (Over the air) software stack.\n\n"
            "Year 1 production capacity is 18,000 units."
        ),
        product_kpis=[
            ("MSRP", "$42,000", "dept_rd"),
            ("Range (EPA)", "310 mi", "accent"),
            ("0-60 mph", "4.1 sec", "dept_sales"),
            ("Yr 1 Capacity", "18,000 units", "dept_ops"),
        ],

        # Step 5: Your Role
        role_body=(
            "You are responsible for allocating Voltex's annual operating budget across four "
            "departments over a 5-year launch window. Each year, you set budgets AND choose a "
            "strategic direction for each department. Once a year is locked, you cannot revisit it."
        ),

        # Step 6: The Objective
        objective_body=(
            "Your VPI score (0-1000+) is based on two equally weighted components:\n\n"
            "* Risk-adjusted profitability\n"
            "* EV market share\n\n"
            "Consistent earnings beat volatile ones. Broad market presence beats narrow niches.\n\n"
            "Hover over different zones to understand what the scores represent."
        ),

        # Step 7: Departments
        departments_intro=(
            "You are in charge of four departments, all with completely different return profiles. "
            "Each one has a ceiling, a floor, and a non-linear response curve. Starve one, "
            "and the others underperform. Flood one, and the returns diminish fast. "
            "The allocation that wins Year 1 may be the wrong call for Year 3.\n\n"
            "Each year, you also pick one strategic direction per department. "
            "Strategies are not isolated choices, and some combinations create synergies.\n\n"
            "Click a department to see its strategies and which cross-department effects they trigger."
        ),

        # Step 8: Competitors
        competitors_intro=(
            "You will not be operating in a vacuum. Four rivals are competing for the same customers, "
            "shelf space, and analyst attention. They have their own war chests. Their own strategies. "
            "Their own mistakes.\n\n"
            "Study them by clicking on all competitors. They are not standing still."
        ),

        # Step 9: Ready
        ready_headline="The Xeno launch defines Voltex's next decade.",
        ready_body=(
            "The Xeno is ready for production. The early adopters are waiting. "
            "But so are the legacy automakers with billion dollar war chests, "
            "the Chinese manufacturers with unbeatable pricing, and the Wall Street analysts who "
            "are not sure you will survive. Prove them wrong. Allocate wisely."
        ),

        # Optional slides between Role and Departments (mandate) and between Competitors and Ready (practice).

        # Mandate slide: the annual budget (not a five-year total), repeated five times, and locking is one-way.
        mandate_body=(
            "Each year, you receive a fresh $60 million in operating budget. "
            "You allocate it across four departments and choose a strategic direction for each.\n\n"
            "Once a year is locked, you cannot return to it. But the next year unlocks a fresh $60 million, "
            "along with a small bonus of 3% of last year's profit. "
            "Lose money, and the floor still holds: you'll get at least $30M to work with.\n\n"
            "What carries over from year to year isn't just the bonus. It's the consequences. "
            "A strong R&D year still pays off two years later. For example, Battery technology doesn't materialize overnight. "
            "Additionally, a starved Operations year still chokes Sales the year after; "
            "you cannot sell what you cannot build. "
            "Your job is to play five connected hands, not five independent ones."
        ),

        # The Practice slide: short, low-pressure copy. The interactive sandbox
        # is doing the teaching; the words should get out of its way.
        practice_body=(
            "This is a practice round for one year.\n\n"
            "* Move the four sliders to allocate the budget.\n"
            "* Each department has a floor (minimum spend) and a ceiling (maximum spend); the sliders won't let you go past either.\n"
            "* Pick one strategic direction in each department.\n"
            "* Lock the year.\n\n"
            "Watch the strategy chips: each affects customer segments differently, and some pairings boost "
            "other departments through synergies (as mentioned on slide 7). "
            "This round doesn't count. Get comfortable with the controls. "
            "When the real Year 1 starts, you'll see actual results based on your decisions."
        ),
    ),

    # Briefing content
    briefing=BriefingContent(
        world_body=(
            "The US EV market has crossed 10% penetration and the land grab is on. Federal tax credits "
            "are reshaping economics, charging infrastructure is growing but patchy, and legacy automakers "
            "are pouring billions into EV platforms. Battery costs are falling but lithium prices swung "
            "40% last year. Chinese manufacturers are entering with aggressive pricing. The next five "
            "years will separate real businesses from cash-burning headlines."
        ),
        market_body=(
            "The US passenger EV market is growing at 32% annually toward $800B by 2030. Four consumer "
            "segments — families, tech enthusiasts, performance buyers, and fleet managers. Each with "
            "radically different priorities and purchase triggers."
        ),
        company_body=(
            "Voltex Motors is an Austin-based EV manufacturer with two delivered pickups, 1,200 employees, "
            "and a NASDAQ listing. Founded by a former battery engineer focused on the middle market. "
            "The Xeno is a $42,000 mass-market coupe that is about to launch. This is the make-or-break moment."
        ),
        product_body=(
            "The Voltex Xeno is the company's entry into the mass-market passenger EV segment. "
            "A 5-seat all-electric coupe targeting a starting MSRP of $42,000. The Xeno "
            "competes directly with established rivals from major EV manufacturers. "
            "It is designed on a new platform with a 75 kWh battery pack, "
            "dual-motor all-wheel drive, and an OTA-capable software stack. "
            "Year 1 production capacity is 18,000 units. Success of the Xeno defines "
            "whether Voltex becomes a mainstream EV brand or remains a niche player."
        ),
        product_kpis=[
            ("MSRP", "$42,000", "dept_rd"),
            ("Range (EPA)", "310 mi", "accent"),
            ("0-60 mph", "4.1 sec", "dept_sales"),
            ("Yr 1 Capacity", "18,000 units", "dept_ops"),
        ],
        role_body=(
            "You are responsible for allocating Voltex's annual operating budget across four "
            "departments over a 5-year launch window. "
            "Each year you set budgets AND choose a strategic direction for each department. "
            "These sub-decisions shape which consumer segments the Xeno appeals to and "
            "directly influence revenue. Your decisions are final: once a year is locked, "
            "you cannot revisit it."
        ),
        objective_body=(
            "Your VPI score (0-1000+) is based on two equally weighted components: "
            "risk-adjusted profitability (50%) and EV market share (50%). "
            "Consistent earnings beat volatile ones. Broad market presence beats narrow niches. "
            "The best scores come from balancing both."
        ),
    ),
    objective_text={},
)


# Register with the scenario registry

register_scenario("us", "ev", US_EV)
