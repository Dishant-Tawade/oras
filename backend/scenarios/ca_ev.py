"""
scenarios/ca_ev.py — Canada × Electric Vehicles scenario.

Pinnacle EV — a growth-stage Canadian EV manufacturer based in Toronto,
launching the Aurora Electric SUV into Canada's rapidly evolving EV market.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.ca_ev_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


CA_EV = ScenarioDefinition(
    scenario_id="ca_ev",
    scenario_label="Canada — Electric Vehicles",

    # Locale
    locale=LocaleConfig(
        country_code="CA",
        country_name="Canada",
        currency_symbol="C$",
        currency_code="CAD",
        currency_prefix=True,
        large_number_suffix="M",
        large_number_divisor=1_000_000,
    ),

    # Company
    company=CompanyConfig(
        name="Pinnacle EV",
        product_name="Pinnacle Aurora Electric SUV",
        tagline="Canadian EV innovator built for all seasons",
        location="Toronto, Ontario",
        role_title="VP of Finance & Strategy",
        founding_year="2022",
        industry_label="Electric Vehicles",
        unit_price=48_000.0,
        unit_price_label="MSRP",
        unit_cost=31_000.0,
        year1_capacity=15_000,
        capacity_unit="units",
    ),

    # Financials
    financials=FinancialConfig(
        total_budget=55_000_000,
        fixed_costs=88_000_000,
        base_revenue=36_850_000,
        profit_reinvestment_rate=0.03,
        inflation_min=0.04,
        inflation_max=0.12,
        underuse_threshold=0.15,
        underuse_penalty_rate=2.5,
        max_change_rate=0.30,
        demand_noise_std=0.08,
        scenario_drift_std=0.03,
        risk_penalty_lambda=1.5,
        num_periods=5,
        num_eval_scenarios=30,
        state_decay=0.5,
        vpi_ras_floor=9_130_560,
        vpi_ras_ceiling=67_180_200,
        vpi_share_floor=11.12,
        vpi_share_ceiling=14.16,
        competitor_presence_baseline=300_000_000,
    ),

    # Timer
    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    # Departments
    departments=[
        DepartmentParams(
            name="R&D", S_max=73_333_333, K=14_666_666, alpha=1.3,
            decay=0.6, min_spend=2_750_000, max_spend=27_500_000,
            state_sensitivity=0.12, catch_up_rate=0.25, sweet_spot_frac=0.70,
        ),
        DepartmentParams(
            name="Sales", S_max=55_000_000, K=12_833_333, alpha=0.9,
            decay=0.15, min_spend=4_583_333, max_spend=27_500_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Operations", S_max=73_333_333, K=8_250_000, alpha=0.85,
            decay=0.55, min_spend=3_666_666, max_spend=22_916_666,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Marketing", S_max=73_333_333, K=9_166_666, alpha=1.05,
            decay=0.40, min_spend=2_750_000, max_spend=22_916_666,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.65,
        ),
    ],

    # Department display metadata
    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd",
            description=(
                "Research & Development drives long-term innovation — critical for cold-weather battery "
                "technology and all-wheel-drive systems. Returns are DELAYED by one year. "
                "R&D sub-decisions unlock synergy bonuses for other departments. "
                "Sustained investment compounds, making future spending more effective."
            ),
            background_description="R&D covers cold-weather battery optimization, all-wheel-drive systems, software development, and vehicle testing in Canadian winter conditions.",
        ),DepartmentMeta(
            name="Sales", color_key="dept_sales",
            description=(
                "Sales converts demand into orders across Canada's vast geography — from Vancouver to "
                "Halifax. Returns are immediate but CAPPED by Operations capacity — you cannot sell "
                "more than you can produce. Cutting sales budget causes a fast drop in bookings."
            ),
            background_description="Sales manages dealer partnerships across provinces, fleet sales to government and commercial buyers, and direct ordering through the company website.",
        ),DepartmentMeta(
            name="Operations", color_key="dept_ops",
            description=(
                "Operations is the BOTTLENECK. It determines production capacity that caps Sales. "
                "Canada's supply chain spans cross-border US-Canada logistics and domestic rail networks. "
                "Under-investing in Operations while Sales is high means lost orders."
            ),
            background_description="Operations manages the assembly plant, cold-weather logistics, cross-Canada distribution, and supplier relationships for Canadian-sourced components.",
        ),DepartmentMeta(
            name="Marketing", color_key="dept_mktg",
            description=(
                "Marketing builds brand awareness across English and French Canadian markets. "
                "Returns follow an S-curve — minimal at low spend, strong above threshold, but "
                "over-spending past the sweet spot wastes budget. Brand equity persists but fades "
                "without reinforcement."
            ),
        
            background_description="Marketing builds brand awareness through value and savings messaging, all-season capability campaigns, technology positioning, and environmental branding. The team manages bilingual campaigns across English and French Canada.",
        ),
    ],department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    # Consumer Segments
    segments=[
        ConsumerSegment(
            key="coldclimate",
            label="Cold-Climate Commuters",
            description=(
                "Canadian families and daily commuters who need reliable year-round EV performance — "
                "especially in harsh winters. Highly sensitive to cold-weather range, cabin heating "
                "efficiency, and total cost of ownership. Represent ~40% of the addressable market."
            ),
            market_weight=0.40,
        ),
        ConsumerSegment(
            key="tech",
            label="Urban Tech Adopters",
            description=(
                "Affluent professionals in Toronto, Vancouver, and Montreal who prioritise connected "
                "features, OTA updates, autonomous driving aids, and digital UX. "
                "Represent ~22% of the addressable market."
            ),
            market_weight=0.22,
        ),
        ConsumerSegment(
            key="outdoor",
            label="Outdoor Adventure Buyers",
            description=(
                "Active Canadians who want an EV that can handle cottage trips, ski weekends, and "
                "backcountry adventures. Demand long range, AWD capability, roof-rack compatibility, "
                "and rugged all-season performance. Represent ~18% of the addressable market."
            ),
            market_weight=0.18,
        ),
        ConsumerSegment(
            key="fleet",
            label="Government & Fleet",
            description=(
                "Federal, provincial, and municipal fleets plus corporate buyers. Canada's ZEV mandates "
                "are accelerating fleet electrification. Prioritise reliability, serviceability, and "
                "total cost of ownership at scale. Represent ~20% of the addressable market."
            ),
            market_weight=0.20,
        ),
    ],

    segment_colors={"coldclimate": "#3D6B50", "tech": "#4A7B9D", "outdoor": "#C27D3A", "fleet": "#8B6BAE"},

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
                "coldweather": SubDecisionOption(
                    key="coldweather",
                    label="Cold-Weather Battery Technology",
                    description="Optimise thermal management and energy density for -30°C Canadian winters.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Sales": 0.08, "Marketing": 0.05},
                    segment_multipliers={"coldclimate": 1.40, "tech": 1.05, "outdoor": 1.25, "fleet": 1.20},
                ),
                "software": SubDecisionOption(
                    key="software",
                    label="Connected Software & ADAS",
                    description="Invest in autonomous driving aids, OTA updates, and a best-in-class digital cockpit.",
                    smax_mult=1.25, k_mult=1.30,
                    synergy={"Marketing": 0.12},
                    segment_multipliers={"coldclimate": 0.75, "tech": 1.50, "outdoor": 0.90, "fleet": 1.05},
                ),
                "cost": SubDecisionOption(
                    key="cost",
                    label="Cost Reduction Engineering",
                    description="Optimise cell chemistry and production processes to lower the sticker price.",
                    smax_mult=0.90, k_mult=0.75,
                    synergy={"Operations": 0.15, "Sales": 0.05},
                    segment_multipliers={"coldclimate": 1.30, "tech": 0.70, "outdoor": 0.75, "fleet": 1.40},
                ),
                "awd": SubDecisionOption(
                    key="awd",
                    label="AWD Powertrain & Performance",
                    description="Develop a high-output dual-motor AWD platform with class-leading traction and acceleration.",
                    smax_mult=1.20, k_mult=1.25,
                    synergy={"Marketing": 0.10},
                    segment_multipliers={"coldclimate": 1.10, "tech": 1.15, "outdoor": 1.50, "fleet": 0.70},
                ),
            },
            default="coldweather",
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
                    description="Company-owned experience centres in Toronto, Vancouver, and Montreal with online ordering and home delivery.",
                    smax_mult=1.10, k_mult=1.05,
                    synergy={"Marketing": 0.08},
                    segment_multipliers={"coldclimate": 0.85, "tech": 1.40, "outdoor": 1.10, "fleet": 0.75},
                ),
                "fleet": SubDecisionOption(
                    key="fleet",
                    label="Government & Fleet Sales",
                    description="Dedicated enterprise team targeting federal, provincial, and municipal fleet procurement.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Operations": 0.10},
                    segment_multipliers={"coldclimate": 0.80, "tech": 0.85, "outdoor": 0.70, "fleet": 1.60},
                ),
                "dealer": SubDecisionOption(
                    key="dealer",
                    label="Franchise Dealer Network",
                    description="Partner with established Canadian dealerships for coast-to-coast geographic coverage.",
                    smax_mult=0.95, k_mult=0.80,
                    synergy={"Operations": 0.05},
                    segment_multipliers={"coldclimate": 1.35, "tech": 0.75, "outdoor": 1.00, "fleet": 1.10},
                ),
                "partnerships": SubDecisionOption(
                    key="partnerships",
                    label="Outdoor & Lifestyle Partnerships",
                    description="Co-brand with MEC, Canadian Tire, and adventure brands for cross-selling and bundled experiences.",
                    smax_mult=1.10, k_mult=1.15,
                    synergy={"Marketing": 0.12, "R&D": 0.05},
                    segment_multipliers={"coldclimate": 1.05, "tech": 1.15, "outdoor": 1.45, "fleet": 0.80},
                ),
            },
            default="direct",
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
                    description="Maximise units-per-hour at the Ontario plant through robotics and lean manufacturing.",
                    smax_mult=1.20, k_mult=1.05,
                    synergy={"Sales": 0.10},
                    segment_multipliers={"coldclimate": 1.20, "tech": 1.00, "outdoor": 0.90, "fleet": 1.30},
                ),
                "winterlogistics": SubDecisionOption(
                    key="winterlogistics",
                    label="Winter Logistics & Charging Network",
                    description="Build proprietary heated charging stations and winterised distribution for all-season delivery.",
                    smax_mult=1.10, k_mult=1.15,
                    synergy={"Marketing": 0.08, "Sales": 0.05},
                    segment_multipliers={"coldclimate": 1.30, "tech": 1.10, "outdoor": 1.20, "fleet": 1.00},
                ),
                "supply_chain": SubDecisionOption(
                    key="supply_chain",
                    label="Cross-Border Supply Resilience",
                    description="Dual-source critical components across US-Canada border and build strategic inventory buffers.",
                    smax_mult=1.05, k_mult=0.85,
                    synergy={"R&D": 0.05},
                    segment_multipliers={"coldclimate": 1.10, "tech": 0.90, "outdoor": 0.95, "fleet": 1.20},
                ),
                "service": SubDecisionOption(
                    key="service",
                    label="After-Sales Service & Warranty",
                    description="Expand service centres across provinces and extend cold-climate battery warranty.",
                    smax_mult=1.10, k_mult=1.00,
                    synergy={"Sales": 0.08, "Marketing": 0.06},
                    segment_multipliers={"coldclimate": 1.25, "tech": 1.05, "outdoor": 1.15, "fleet": 1.10},
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
                    label="Affordability & TCO",
                    description="Position on total cost of ownership — cheaper to buy, own, and run than gas in every province.",
                    smax_mult=1.05, k_mult=0.90,
                    synergy={"Sales": 0.10},
                    segment_multipliers={"coldclimate": 1.45, "tech": 0.75, "outdoor": 0.70, "fleet": 1.30},
                ),
                "allseason": SubDecisionOption(
                    key="allseason",
                    label="All-Season Adventure",
                    description="Lead with rugged all-weather capability — from cottage country to the Rockies, in any season.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"R&D": 0.05, "Sales": 0.05},
                    segment_multipliers={"coldclimate": 1.20, "tech": 0.90, "outdoor": 1.55, "fleet": 0.80},
                ),
                "tech": SubDecisionOption(
                    key="tech",
                    label="Technology & Innovation Leadership",
                    description="Lead with software, autonomy, and cutting-edge connected features.",
                    smax_mult=1.20, k_mult=1.15,
                    synergy={"R&D": 0.08},
                    segment_multipliers={"coldclimate": 0.75, "tech": 1.55, "outdoor": 1.00, "fleet": 0.90},
                ),
                "green": SubDecisionOption(
                    key="green",
                    label="Clean & Green Canadian",
                    description="Net-zero supply chain, Canadian-sourced minerals, hydro-powered manufacturing.",
                    smax_mult=1.10, k_mult=1.00,
                    synergy={"Sales": 0.04, "Operations": 0.04},
                    segment_multipliers={"coldclimate": 1.10, "tech": 1.20, "outdoor": 1.05, "fleet": 1.25},
                ),
            },
            default="allseason",
        ),
    },

    # Competitors
    competitors=[
        CompetitorDef(
            name="Maple Legacy Auto (EV Division)",
            industry="Legacy Canadian OEM",
            location="Oshawa, Canada",
            founded="1955",
            description=(
                "Canada's dominant legacy automaker with coast-to-coast dealer coverage built "
                "over seven decades. Every Canadian province has multiple Maple dealerships; "
                "brand trust among older buyers is unmatched. The EV transition is painful — "
                "slow software culture, union constraints, and high fixed costs mean the "
                "product itself lags, but sheer distribution weight keeps them competitive."
            ),
            display_label="Established Giant",
            # Large revenue base but nearly stagnant — they're milking legacy ICE margins
            base_revenue=1_800_000_000, growth_rate=0.02, margin=0.06,
            # Specs are mediocre — legacy OEM playing catch-up, not leading
            base_specs={"range": 390, "battery": 62, "accel": 6.8},
            spec_growth_rates={"range": 8.0, "battery": 1.5, "accel": -0.04},
            # Massive reach: every town in Canada has a Maple dealer
            base_reach=2.0,
        ),
        CompetitorDef(
            name="Evergreen Motors",
            industry="Canadian EV startup",
            location="Vancouver, Canada",
            founded="2019",
            description=(
                "Five-year-old Vancouver startup riding the eco-conscious wave. Cult following "
                "among urban sustainability buyers but almost no dealer presence outside BC "
                "and Ontario. Engineering team is talented but small; cold-weather performance "
                "remains a known gap. The company is burning cash on rapid hiring."
            ),
            display_label="Scrappy Newcomer",
            # Small revenue, high burn, high growth aspirations
            base_revenue=55_000_000, growth_rate=0.22, margin=-0.05,
            # Good eco credentials but hardware is early-stage
            base_specs={"range": 370, "battery": 58, "accel": 5.8},
            spec_growth_rates={"range": 14.0, "battery": 3.0, "accel": -0.12},
            # Very low reach — genuinely hard to buy outside major cities
            base_reach=0.35,
        ),
        CompetitorDef(
            name="Frost Automotive",
            industry="Premium cold-climate EV",
            location="Montreal, Canada",
            founded="2016",
            description=(
                "Boutique Montreal EV maker that has spent nine years perfecting cold-weather "
                "range retention and heated-battery conditioning. The product is genuinely best-in-class "
                "for Canadian winters — but it costs 40% more than the segment average and "
                "distribution is intentionally curated: 18 flagship showrooms, no mass-market dealers."
            ),
            display_label="Premium Niche Specialist",
            # Healthy revenue for a niche player, premium margins, slow growth by design
            base_revenue=310_000_000, growth_rate=0.05, margin=0.21,
            # Outstanding specs — this is the product benchmark, especially range and battery
            base_specs={"range": 570, "battery": 96, "accel": 3.2},
            spec_growth_rates={"range": 10.0, "battery": 2.5, "accel": -0.06},
            # Low reach by choice — exclusivity is part of the brand
            base_reach=0.55,
        ),
        CompetitorDef(
            name="Pacific Drive",
            industry="Chinese EV entrant",
            location="Shenzhen, China",
            founded="2018",
            description=(
                "Aggressive Chinese manufacturer treating Canada as a strategic beachhead. "
                "Vertical integration gives them a dramatic battery cost advantage; they are "
                "actively losing money per unit to buy market share. Dealer network is expanding "
                "fast but brand trust is low and regulators are watching closely."
            ),
            display_label="Aggressive Price Disruptor",
            # Large global revenue but Canadian operation is loss-leader
            base_revenue=420_000_000, growth_rate=0.18, margin=-0.03,
            # Solid battery specs from vertical integration, weak on performance
            base_specs={"range": 430, "battery": 78, "accel": 6.2},
            spec_growth_rates={"range": 16.0, "battery": 4.5, "accel": -0.10},
            # Moderate and fast-growing reach — they are spending heavily on distribution
            base_reach=0.80,
        ),
    ],

    competitor_labels={
        "Maple Legacy Auto (EV Division)": "Established Giant",
        "Evergreen Motors": "Scrappy Newcomer",
        "Frost Automotive": "Premium Niche Specialist",
        "Pacific Drive": "Aggressive Price Disruptor",
    },

    # Product Specs
    product_specs=[
        ProductSpec(key="range", label="Range (NRCan)", unit="km", base_value=500, higher_is_better=True),
        ProductSpec(key="battery", label="Battery", unit="kWh", base_value=75, higher_is_better=True),
        ProductSpec(key="accel", label="0–100 km/h", unit="sec", base_value=4.3, higher_is_better=False, display_format=".1f"),
    ],

    # Spec Evolution Rules
    # base_growth: free annual improvement with zero R&D spend (technology floor drift)
    # spend_sensitivity: additional delta per 1x dept_budget_ref of R&D spend
    # Tuned so: zero spend -> slow decay toward competitors; sustained 1x spend -> gradual
    # leadership; 2x spend -> clear dominance. Single-year burst has limited lasting effect.
    spec_evolution_rules=[
        SpecEvolutionRule(
            spec_key="range", dept_name="R&D",
            base_growth=3.0,           # was 8.0 — free drift now modest
            spend_sensitivity=15.0,
            dept_budget_ref=13_750_000,
            sub_decision_bonuses={"coldweather": 10.0, "cost": -4.0, "software": 2.5, "awd": 6.0},
            min_value=300, max_value=750,  # wider floor so laggards fall behind; tighter ceil
        ),
        SpecEvolutionRule(
            spec_key="battery", dept_name="R&D",
            base_growth=0.5,           # was 2.0
            spend_sensitivity=5.0,     # was 8.0
            dept_budget_ref=13_750_000,
            sub_decision_bonuses={"coldweather": 3.0, "cost": -1.0, "software": 0.5, "awd": 2.0},
            min_value=50, max_value=140,
        ),
        SpecEvolutionRule(
            spec_key="accel", dept_name="R&D",
            base_growth=-0.02,         # was -0.05 — free improvement nearly zero
            spend_sensitivity=-0.15,   # was -0.3
            dept_budget_ref=13_750_000,
            sub_decision_bonuses={"awd": -0.2, "coldweather": 0.05, "cost": 0.1, "software": -0.05},
            min_value=2.0, max_value=7.0,  # raised ceiling so bad players can get worse
        ),
    ],

    # Segment Spec Preferences
    segment_spec_preferences={
        "coldclimate": [
            SegmentSpecPreference(spec_key="range", weight=0.55, ideal_value=600, tolerance=200),
            SegmentSpecPreference(spec_key="battery", weight=0.30, ideal_value=95, tolerance=40),
            SegmentSpecPreference(spec_key="accel", weight=0.15, ideal_value=5.5, tolerance=2.5),
        ],
        "tech": [
            SegmentSpecPreference(spec_key="range", weight=0.35, ideal_value=620, tolerance=180),
            SegmentSpecPreference(spec_key="battery", weight=0.25, ideal_value=105, tolerance=40),
            SegmentSpecPreference(spec_key="accel", weight=0.40, ideal_value=3.5, tolerance=2.0),
        ],
        "outdoor": [
            SegmentSpecPreference(spec_key="range", weight=0.50, ideal_value=660, tolerance=200),
            SegmentSpecPreference(spec_key="battery", weight=0.20, ideal_value=100, tolerance=40),
            SegmentSpecPreference(spec_key="accel", weight=0.30, ideal_value=4.5, tolerance=2.0),
        ],
        "fleet": [
            SegmentSpecPreference(spec_key="range", weight=0.58, ideal_value=630, tolerance=200),
            SegmentSpecPreference(spec_key="battery", weight=0.33, ideal_value=95, tolerance=40),
            SegmentSpecPreference(spec_key="accel", weight=0.09, ideal_value=6.0, tolerance=3.5),
        ],
    },

    # Performance index
    performance_index_name="PPI",
    performance_index_full="Pinnacle Performance Index",
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
        world_headline="The year is 2025. Canada's EV revolution is accelerating — but the road ahead is icy.",
        world_body=(
            "Federal ZEV mandates are tightening, provincial incentive programmes are expanding, "
            "and cross-border trade dynamics with the United States are shifting. Meanwhile, aggressive "
            "Chinese manufacturers are entering Canadian showrooms with budget-busting prices. "
            "Battery material costs remain volatile, and Canada's extreme winters demand engineering "
            "excellence that tropical-climate competitors struggle to match. The companies that allocate "
            "capital wisely will define the next decade of Canadian mobility."
        ),
        market_body=(
            "The Canadian passenger EV market is growing at 38% annually and is projected to reach "
            "C$45B by 2030. Four distinct consumer groups contest the market — each shaped by Canada's "
            "unique geography, climate, and bilingual culture."
        ),
        market_kpis=[
            ("Market Size", "C$45B by 2030", "dept_rd"),
            ("Growth Rate", "38% annually", "accent"),
            ("Segments", "4 consumer groups", "dept_mktg"),
        ],
        segments_intro="Winning in Canada requires matching product features to the country's unique buyer needs.",
        company_subtitle="Founded 2022  ·  Toronto, Ontario  ·  900 employees  ·  TSX: PNCL",
        company_body=(
            "Pinnacle EV is a growth-stage Canadian EV manufacturer that has successfully delivered "
            "two niche electric crossover vehicles to market. The company has strong engineering "
            "talent — many recruited from Bombardier and Magna International — a loyal early-adopter "
            "fanbase across Ontario and BC, and a lean but scalable manufacturing facility in "
            "Markham, Ontario. The previous CFO departed last quarter to join a US competitor. "
            "You are stepping in ahead of the company's most ambitious product launch yet."
        ),
        product_subtitle="All-Electric SUV — Built for Canadian roads, in every season",
        product_body=(
            "The Pinnacle Aurora is the company's entry into the mass-market Canadian EV segment — "
            "a 5-seat all-electric SUV targeting a starting MSRP of C$48,000. "
            "It is engineered on a new skateboard platform with a 75 kWh battery pack, "
            "dual-motor AWD, heated battery conditioning for -30°C operation, and an OTA-capable "
            "software stack with bilingual (English/French) voice interface. "
            "Year 1 production capacity is 15,000 units."
        ),
        product_kpis=[
            ("MSRP", "C$48,000", "dept_rd"),
            ("Range (NRCan)", "500 km", "accent"),
            ("0–100 km/h", "4.3 sec", "dept_sales"),
            ("Yr 1 Capacity", "15,000 units", "dept_ops"),
        ],
        role_body=(
            "You are responsible for allocating Pinnacle EV's annual operating budget across four "
            "departments — R&D, Sales, Operations, and Marketing — over a 5-year launch window. "
            "Each year you set budgets AND choose a strategic direction for each department. "
            "Your decisions are final: once a year is locked, you cannot revisit it."
        ),
        objective_body=(
            "Your PPI score (0–1000+) is based on two equally weighted components: "
            "risk-adjusted profitability (50%) and Canadian EV market share (50%). "
            "Consistent earnings beat volatile ones. Broad market presence beats narrow niches."
        ),
        departments_intro="Each department has distinct mechanics that affect your bottom line.",
        competitors_intro="You won't be operating in a vacuum. These rivals want the same Canadian customers.",
        ready_headline="Your journey starts now — the Aurora awaits.",
        ready_body=(
            "You have been briefed on the Canadian market, the company, the product, your role, "
            "and the competition. The background and objective tabs will remain available as "
            "reference during the simulation. Trust your strategy — allocate wisely."
        ),
    ),

    # Briefing
    briefing=BriefingContent(
        world_body=(
            "The year is 2025. Canada's EV revolution is accelerating — but the road ahead is icy. "
            "Federal ZEV mandates are tightening, provincial incentive programmes are expanding, "
            "and cross-border trade dynamics with the United States are shifting. Chinese manufacturers "
            "are entering Canadian showrooms with aggressive pricing. Battery costs are volatile, "
            "and extreme winters demand engineering excellence. The companies that allocate capital "
            "wisely — and build the right product for Canadian conditions — will define the next decade."
        ),
        market_body=(
            "The Canadian passenger EV market is growing at 38% annually and is projected to reach "
            "C$45B by 2030. Four distinct consumer groups contest the market, each shaped by Canada's "
            "unique geography, harsh winters, and bilingual culture. Winning requires spend directed "
            "at the right features for Canadian buyers."
        ),
        company_body=(
            "Pinnacle EV is a growth-stage Canadian EV manufacturer that has successfully delivered "
            "two niche electric crossover vehicles to market. The company has strong engineering "
            "talent, a loyal early-adopter fanbase across Ontario and BC, and a lean but scalable "
            "manufacturing facility in Markham, Ontario. The previous CFO departed last quarter. "
            "You are stepping in ahead of the company's most ambitious product launch yet."
        ),
        product_body=(
            "The Pinnacle Aurora is the company's entry into the mass-market Canadian EV segment — "
            "a 5-seat all-electric SUV targeting a starting MSRP of C$48,000. The Aurora "
            "competes directly with established rivals in Canada's unique cold-climate market. "
            "It is engineered on a new skateboard platform with a 75 kWh battery pack, "
            "dual-motor AWD, heated battery conditioning, and bilingual OTA software. "
            "Year 1 production capacity is 15,000 units. The Aurora's success determines "
            "whether Pinnacle becomes a mainstream Canadian EV brand — or remains a niche player."
        ),
        product_kpis=[
            ("MSRP", "C$48,000", "dept_rd"),
            ("Range (NRCan)", "500 km", "accent"),
            ("0–100 km/h", "4.3 sec", "dept_sales"),
            ("Yr 1 Capacity", "15,000 units", "dept_ops"),
        ],
        role_body=(
            "You are responsible for allocating Pinnacle EV's annual operating budget across four "
            "departments — R&D, Sales, Operations, and Marketing — over a 5-year launch window. "
            "Each year you set budgets AND choose a strategic direction for each department. "
            "These sub-decisions shape which consumer segments the Aurora appeals to and "
            "directly influence revenue. Your decisions are final: once a year is locked, "
            "you cannot revisit it."
        ),
        objective_body=(
            "Your PPI score (0–1000+) is based on two equally weighted components: "
            "risk-adjusted profitability (50%) and Canadian EV market share (50%). "
            "Consistent earnings beat volatile ones. Broad market presence beats narrow niches. "
            "The best scores come from balancing both."
        ),
    ),
    objective_text={},
)


register_scenario("ca", "ev", CA_EV)
