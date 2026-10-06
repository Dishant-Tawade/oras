"""
scenarios/in_ev.py — India × Electric Vehicles scenario.

Vayuha Motors — a growth-stage Indian EV manufacturer based in Pune,
launching the Shakti Electric Sedan into India's booming EV market.

Option C scaling: ₹800 Cr budget, mid-range competitors (₹1,200-6,000 Cr),
22,000 unit capacity. Numbers displayed in Lakhs (L) for department-level
and Crores (Cr) for company-level figures.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.in_ev_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


IN_EV = ScenarioDefinition(
    scenario_id="in_ev",
    scenario_label="India — Electric Vehicles",

    # Locale
    locale=LocaleConfig(
        country_code="IN",
        country_name="India",
        currency_symbol="₹",
        currency_code="INR",
        currency_prefix=True,
        large_number_suffix="Cr",
        large_number_divisor=10_000_000,       # 1 Cr = 10,000,000
        small_number_suffix="L",
        small_number_divisor=100_000,           # 1 Lakh = 100,000
        slider_step=100_000,                    # ₹1L increments on sliders
    ),

    # Company
    company=CompanyConfig(
        name="Vayuha Motors",
        product_name="Vayuha Shakti Electric Sedan",
        tagline="Electric mobility for a billion Indians",
        location="Pune, Maharashtra",
        role_title="VP of Finance & Strategy",
        founding_year="2021",
        industry_label="Electric Vehicles",
        unit_price=2_500_000.0,        # ₹25 lakh MSRP
        unit_price_label="MSRP",
        unit_cost=1_600_000.0,         # ₹16 lakh cost
        year1_capacity=22_000,
        capacity_unit="units",
    ),

    financials=FinancialConfig(
        total_budget=8_000_000_000,        # ₹800 Cr
        fixed_costs=12_000_000_000,        # ₹1,200 Cr
        base_revenue=5_200_000_000,        # ₹520 Cr
        profit_reinvestment_rate=0.03,
        inflation_min=0.08,
        inflation_max=0.18,
        underuse_threshold=0.15,
        underuse_penalty_rate=2.5,
        max_change_rate=0.30,
        demand_noise_std=0.10,
        scenario_drift_std=0.04,
        risk_penalty_lambda=1.5,
        num_periods=5,
        num_eval_scenarios=30,
        state_decay=0.5,
        vpi_ras_floor=1_203_980_000,  # ₹-552 Cr (calibrated from 1000 Monte Carlo runs)
        vpi_ras_ceiling=10_041_850_000,  # ₹736 Cr
        vpi_share_floor=16.38,
        vpi_share_ceiling=20.65,
        competitor_presence_baseline=50_000_000_000,   # ₹5,000 Cr
    ),

    # Timer
    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    # Departments
    # Scaled to ₹800 Cr budget — same ratios as US scenario
    departments=[
        DepartmentParams(
            name="R&D", S_max=10_666_666_666, K=2_133_333_333, alpha=1.3,
            decay=0.6, min_spend=400_000_000, max_spend=4_000_000_000,
            state_sensitivity=0.12, catch_up_rate=0.25, sweet_spot_frac=0.70,
        ),
        DepartmentParams(
            name="Sales", S_max=8_000_000_000, K=1_866_666_666, alpha=0.9,
            decay=0.15, min_spend=666_666_666, max_spend=4_000_000_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Operations", S_max=10_666_666_666, K=1_200_000_000, alpha=0.85,
            decay=0.55, min_spend=533_333_333, max_spend=3_333_333_333,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Marketing", S_max=10_666_666_666, K=1_333_333_333, alpha=1.05,
            decay=0.40, min_spend=400_000_000, max_spend=3_333_333_333,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.65,
        ),
    ],

    # Department display metadata
    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd",
            description=(
                "Research & Development drives long-term innovation — critical for heat-tolerant "
                "battery technology and cost-optimised platforms for the Indian market. Returns are "
                "DELAYED by one year. R&D sub-decisions unlock synergy bonuses for other departments."
            ),
            background_description="R&D covers heat-tolerant battery engineering, cost-optimized platforms for the Indian market, connected vehicle software, and multilingual interface development.",
        ),DepartmentMeta(
            name="Sales", color_key="dept_sales",
            description=(
                "Sales converts demand into orders across India's vast and diverse geography — from "
                "metro showrooms to Tier-2 city dealers. Returns are immediate but CAPPED by "
                "Operations capacity. Cutting sales budget causes a fast drop in bookings."
            ),
            background_description="Sales manages showroom networks, fleet partnerships with ride-hailing and government buyers, Tier-2 city dealer expansion, and digital sales channels.",
        ),DepartmentMeta(
            name="Operations", color_key="dept_ops",
            description=(
                "Operations is the BOTTLENECK. It determines production capacity that caps Sales. "
                "India's PLI scheme rewards domestic manufacturing scale, and monsoon season creates "
                "supply chain challenges. Under-investing means lost orders."
            ),
            background_description="Operations runs the Chakan manufacturing facility, manages monsoon-resilient logistics, handles PLI scheme compliance, and coordinates pan-India distribution.",
        ),DepartmentMeta(
            name="Marketing", color_key="dept_mktg",
            description=(
                "Marketing builds brand awareness across India's multilingual, mobile-first consumer "
                "base. Returns follow an S-curve — minimal at low spend, strong above threshold. "
                "Cricket sponsorships and digital campaigns drive reach. Over-spending wastes budget."
            ),
        
            background_description="Marketing builds brand awareness through value and savings messaging, all-season reliability campaigns, technology positioning, and clean energy branding. The team manages multilingual campaigns across India's diverse media and digital landscape.",
        ),
    ],department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    # Consumer Segments
    segments=[
        ConsumerSegment(
            key="value",
            label="Value-Driven Urban Families",
            description=(
                "Middle-class Indian families seeking affordable electric mobility as a practical "
                "alternative to petrol cars. Extremely sensitive to purchase price, EMI affordability, "
                "and per-km running cost savings. Represent ~42% of the addressable market."
            ),
            market_weight=0.42,
        ),
        ConsumerSegment(
            key="tech",
            label="Tech-Savvy Metro Professionals",
            description=(
                "Affluent IT professionals in Bengaluru, Hyderabad, and Pune who prioritise "
                "connected features, OTA updates, and digital UX. Early adopters who influence "
                "peer networks. Represent ~20% of the addressable market."
            ),
            market_weight=0.20,
        ),
        ConsumerSegment(
            key="premium",
            label="Premium Aspiration Buyers",
            description=(
                "High-income urban Indians who view EVs as a status symbol and aspiration product. "
                "Demand premium build quality, performance, and brand prestige. Willing to pay "
                "for the best. Represent ~15% of the addressable market."
            ),
            market_weight=0.15,
        ),
        ConsumerSegment(
            key="fleet",
            label="Commercial & Fleet Operators",
            description=(
                "Ride-hailing operators, corporate fleets, and government bodies. India's FAME "
                "subsidies and fleet electrification mandates drive volume procurement. Prioritise "
                "total cost of ownership and durability. Represent ~23% of the addressable market."
            ),
            market_weight=0.23,
        ),
    ],

    segment_colors={"value": "#3D6B50", "tech": "#4A7B9D", "premium": "#C27D3A", "fleet": "#8B6BAE"},

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
                "heattolerant": SubDecisionOption(
                    key="heattolerant",
                    label="Heat-Tolerant Battery Technology",
                    description="Optimise thermal management and cycle life for India's extreme 45°C+ summer temperatures.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Sales": 0.08, "Marketing": 0.05},
                    segment_multipliers={"value": 1.25, "tech": 1.10, "premium": 1.15, "fleet": 1.30},
                ),
                "cost": SubDecisionOption(
                    key="cost",
                    label="Cost Reduction Engineering",
                    description="Radical cost engineering — LFP cells, simplified wiring, and local component sourcing to hit sub-₹20L MSRP.",
                    smax_mult=0.90, k_mult=0.75,
                    synergy={"Operations": 0.15, "Sales": 0.05},
                    segment_multipliers={"value": 1.50, "tech": 0.70, "premium": 0.55, "fleet": 1.40},
                ),
                "software": SubDecisionOption(
                    key="software",
                    label="Software & Connectivity",
                    description="Invest in connected car features, multilingual voice AI, and over-the-air updates for India's 5G networks.",
                    smax_mult=1.25, k_mult=1.30,
                    synergy={"Marketing": 0.12},
                    segment_multipliers={"value": 0.80, "tech": 1.50, "premium": 1.10, "fleet": 0.95},
                ),
                "performance": SubDecisionOption(
                    key="performance",
                    label="Performance & Premium Powertrain",
                    description="Develop a high-output platform with class-leading acceleration for India's growing premium EV segment.",
                    smax_mult=1.20, k_mult=1.25,
                    synergy={"Marketing": 0.10},
                    segment_multipliers={"value": 0.60, "tech": 1.15, "premium": 1.55, "fleet": 0.70},
                ),
            },
            default="heattolerant",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales",
            label="Sales Channel Strategy",
            tooltip=(
                "Choose your go-to-market channel. Sales revenue is CAPPED by Operations "
                "capacity — you cannot sell more vehicles than you can produce."
            ),
            options={
                "digital": SubDecisionOption(
                    key="digital",
                    label="Digital-First Online Sales",
                    description="Online ordering with experience centres in Bengaluru, Mumbai, and Delhi. Powered by India's mobile-first consumer base.",
                    smax_mult=1.10, k_mult=1.05,
                    synergy={"Marketing": 0.08},
                    segment_multipliers={"value": 0.85, "tech": 1.45, "premium": 1.10, "fleet": 0.75},
                ),
                "fleet": SubDecisionOption(
                    key="fleet",
                    label="Fleet & Government Sales",
                    description="Dedicated team targeting EESL, state transport corporations, and ride-hailing platforms like BluSmart.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"Operations": 0.10},
                    segment_multipliers={"value": 0.80, "tech": 0.80, "premium": 0.65, "fleet": 1.60},
                ),
                "tier2": SubDecisionOption(
                    key="tier2",
                    label="Tier-2 City Dealer Expansion",
                    description="Aggressive dealer network expansion into Tier-2 and Tier-3 cities across India's heartland.",
                    smax_mult=0.95, k_mult=0.80,
                    synergy={"Operations": 0.05},
                    segment_multipliers={"value": 1.40, "tech": 0.70, "premium": 0.75, "fleet": 1.10},
                ),
                "partnerships": SubDecisionOption(
                    key="partnerships",
                    label="Tech & Lifestyle Partnerships",
                    description="Co-brand with Flipkart, Jio, and lifestyle brands for cross-selling and bundled digital experiences.",
                    smax_mult=1.10, k_mult=1.15,
                    synergy={"Marketing": 0.12, "R&D": 0.05},
                    segment_multipliers={"value": 1.05, "tech": 1.30, "premium": 1.20, "fleet": 0.85},
                ),
            },
            default="digital",
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
                    description="Maximise units-per-hour at the Pune plant through automation and lean manufacturing.",
                    smax_mult=1.20, k_mult=1.05,
                    synergy={"Sales": 0.10},
                    segment_multipliers={"value": 1.25, "tech": 1.00, "premium": 0.85, "fleet": 1.30},
                ),
                "localisation": SubDecisionOption(
                    key="localisation",
                    label="PLI Scheme Localisation",
                    description="Maximise domestic content to qualify for Production-Linked Incentive scheme disbursements.",
                    smax_mult=1.10, k_mult=1.15,
                    synergy={"Marketing": 0.08, "Sales": 0.05},
                    segment_multipliers={"value": 1.20, "tech": 0.95, "premium": 0.90, "fleet": 1.25},
                ),
                "supply_chain": SubDecisionOption(
                    key="supply_chain",
                    label="Supply Chain Resilience",
                    description="Dual-source critical components and build monsoon-proof logistics against seasonal disruptions.",
                    smax_mult=1.05, k_mult=0.85,
                    synergy={"R&D": 0.05},
                    segment_multipliers={"value": 1.10, "tech": 0.90, "premium": 0.95, "fleet": 1.20},
                ),
                "service": SubDecisionOption(
                    key="service",
                    label="After-Sales & Service Network",
                    description="Expand service centres across Indian states and build a mobile service fleet for Tier-2 cities.",
                    smax_mult=1.10, k_mult=1.00,
                    synergy={"Sales": 0.08, "Marketing": 0.06},
                    segment_multipliers={"value": 1.25, "tech": 1.05, "premium": 1.10, "fleet": 1.15},
                ),
            },
            default="localisation",
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
                    label="Petrol Savings & TCO",
                    description="Position on per-km savings versus petrol — 'Switch to electric, save ₹1 lakh per year on fuel.'",
                    smax_mult=1.05, k_mult=0.90,
                    synergy={"Sales": 0.10},
                    segment_multipliers={"value": 1.50, "tech": 0.75, "premium": 0.60, "fleet": 1.30},
                ),
                "tech": SubDecisionOption(
                    key="tech",
                    label="Technology & Innovation",
                    description="Lead with connected features, OTA updates, and India's most advanced EV software platform.",
                    smax_mult=1.20, k_mult=1.15,
                    synergy={"R&D": 0.08},
                    segment_multipliers={"value": 0.75, "tech": 1.55, "premium": 1.15, "fleet": 0.85},
                ),
                "premium": SubDecisionOption(
                    key="premium",
                    label="Premium & Aspiration",
                    description="Position as a premium Indian brand — luxury build quality, performance, and status for the new India.",
                    smax_mult=1.15, k_mult=1.10,
                    synergy={"R&D": 0.05, "Sales": 0.05},
                    segment_multipliers={"value": 0.60, "tech": 1.10, "premium": 1.55, "fleet": 0.75},
                ),
                "green": SubDecisionOption(
                    key="green",
                    label="Clean India & Sustainability",
                    description="Align with Swachh Bharat and clean air missions. Solar-powered manufacturing, ethical sourcing.",
                    smax_mult=1.10, k_mult=1.00,
                    synergy={"Sales": 0.04, "Operations": 0.04},
                    segment_multipliers={"value": 1.15, "tech": 1.15, "premium": 0.85, "fleet": 1.25},
                ),
            },
            default="value",
        ),
    },

    # Competitors
    # Option C: mid-range scaling — Dharma at ₹6,000 Cr (sedan/SUV EV sub-segment)
    competitors=[
        CompetitorDef(
            name="Dharma Motors EV",
            industry="Indian conglomerate EV",
            location="Mumbai, India",
            founded="1945",
            description=(
                "India's largest domestic EV player backed by the Dharma Group's deep pockets. "
                "Dominant market share through the Nexon EV and Tiago EV. Strong brand trust, "
                "massive dealer network, and aggressive pricing. The benchmark competitor."
            ),
            display_label="Dominant Indian EV Leader",
            base_revenue=60_000_000_000, growth_rate=0.10, margin=0.12,   # ₹6,000 Cr
            base_specs={"range": 420, "battery": 60, "accel": 5.0},
            spec_growth_rates={"range": 22.0, "battery": 5.0, "accel": -0.12},
            base_reach=1.4,  # Dominant distribution, massive brand equity in India,
        ),
        CompetitorDef(
            name="Surya EV Tech",
            industry="Indian EV startup",
            location="Bengaluru, India",
            founded="2013",
            description=(
                "Bengaluru-based EV innovator expanding from two-wheelers into four-wheelers. "
                "Known for software-first philosophy and premium build quality. Strong among "
                "tech-savvy urban professionals but limited manufacturing scale."
            ),
            display_label="Tech-Forward EV Startup",
            base_revenue=12_000_000_000, growth_rate=0.15, margin=0.07,   # ₹1,200 Cr
            base_specs={"range": 380, "battery": 55, "accel": 4.5},
            spec_growth_rates={"range": 25.0, "battery": 6.0, "accel": -0.18},
            base_reach=1.0,  # Strong urban tech reach, limited rural penetration,
        ),
        CompetitorDef(
            name="Longway Motors India",
            industry="Chinese-owned EV brand",
            location="Shenzhen, China",
            founded="2017",
            description=(
                "SAIC-backed brand leveraging Chinese manufacturing scale for aggressive Indian "
                "pricing. Feature-rich vehicles at competitive price points. Growing rapidly "
                "but faces periodic anti-China consumer sentiment."
            ),
            display_label="Chinese-Backed Value Challenger",
            base_revenue=22_000_000_000, growth_rate=0.12, margin=0.1,   # ₹2,200 Cr
            base_specs={"range": 400, "battery": 58, "accel": 5.2},
            spec_growth_rates={"range": 20.0, "battery": 5.5, "accel": -0.15},
            base_reach=0.85,  # Growing but facing trust and political headwinds,
        ),
        CompetitorDef(
            name="Swaraj Electric",
            industry="Indian legacy OEM EV",
            location="Mumbai, India",
            founded="1945",
            description=(
                "Legacy Indian automaker with deep rural and fleet network reach. Strong in "
                "commercial and government fleet segments. Slow to modernise software and "
                "digital experience but has unmatched service network depth."
            ),
            display_label="Legacy Indian OEM in EV Transition",
            base_revenue=15_000_000_000, growth_rate=0.06, margin=0.08,   # ₹1,500 Cr
            base_specs={"range": 360, "battery": 55, "accel": 5.8},
            spec_growth_rates={"range": 15.0, "battery": 3.5, "accel": -0.05},
            base_reach=1.2,  # Legacy dealer network, trusted household name,
        ),
    ],

    competitor_labels={
        "Dharma Motors EV": "Dominant Indian EV Leader",
        "Surya EV Tech": "Tech-Forward EV Startup",
        "Longway Motors India": "Chinese-Backed Value Challenger",
        "Swaraj Electric": "Legacy Indian OEM in EV Transition",
    },

    # Product Specs
    product_specs=[
        ProductSpec(key="range", label="Range (ARAI)", unit="km", base_value=450, higher_is_better=True),
        ProductSpec(key="battery", label="Battery", unit="kWh", base_value=60, higher_is_better=True),
        ProductSpec(key="accel", label="0–100 km/h", unit="sec", base_value=4.8, higher_is_better=False, display_format=".1f"),
    ],

    # Spec Evolution Rules
    spec_evolution_rules=[
        SpecEvolutionRule(
            spec_key="range", dept_name="R&D",
            base_growth=10.0,
            spend_sensitivity=35.0,
            dept_budget_ref=2_000_000_000,     # ₹200 Cr reference
            sub_decision_bonuses={"heattolerant": 20.0, "cost": -8.0, "software": 5.0, "performance": 12.0},
            min_value=350, max_value=800,
        ),
        SpecEvolutionRule(
            spec_key="battery", dept_name="R&D",
            base_growth=2.5,
            spend_sensitivity=8.0,
            dept_budget_ref=2_000_000_000,
            sub_decision_bonuses={"heattolerant": 5.0, "cost": -2.0, "software": 1.0, "performance": 4.0},
            min_value=45, max_value=130,
        ),
        SpecEvolutionRule(
            spec_key="accel", dept_name="R&D",
            base_growth=-0.05,
            spend_sensitivity=-0.25,
            dept_budget_ref=2_000_000_000,
            sub_decision_bonuses={"performance": -0.4, "heattolerant": 0.1, "cost": 0.2, "software": -0.1},
            min_value=2.5, max_value=7.0,
        ),
    ],

    # Segment Spec Preferences
    segment_spec_preferences={
        "value": [
            SegmentSpecPreference(spec_key="range", weight=0.55, ideal_value=500, tolerance=120),
            SegmentSpecPreference(spec_key="battery", weight=0.30, ideal_value=70, tolerance=25),
            SegmentSpecPreference(spec_key="accel", weight=0.15, ideal_value=6.0, tolerance=2.5),
        ],
        "tech": [
            SegmentSpecPreference(spec_key="range", weight=0.35, ideal_value=550, tolerance=100),
            SegmentSpecPreference(spec_key="battery", weight=0.25, ideal_value=80, tolerance=25),
            SegmentSpecPreference(spec_key="accel", weight=0.40, ideal_value=4.0, tolerance=1.5),
        ],
        "premium": [
            SegmentSpecPreference(spec_key="range", weight=0.25, ideal_value=600, tolerance=100),
            SegmentSpecPreference(spec_key="battery", weight=0.15, ideal_value=90, tolerance=25),
            SegmentSpecPreference(spec_key="accel", weight=0.60, ideal_value=3.5, tolerance=1.2),
        ],
        "fleet": [
            SegmentSpecPreference(spec_key="range", weight=0.60, ideal_value=500, tolerance=100),
            SegmentSpecPreference(spec_key="battery", weight=0.30, ideal_value=70, tolerance=20),
            SegmentSpecPreference(spec_key="accel", weight=0.10, ideal_value=6.0, tolerance=3.0),
        ],
    },

    # Performance index
    performance_index_name="VPI",
    performance_index_full="Vayuha Performance Index",
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
        world_headline="The year is 2025. India's electric vehicle revolution is exploding — and so is the competition.",
        world_body=(
            "FAME III subsidies are reshaping affordability, state-level incentives are stacking, "
            "and the PLI scheme is rewarding domestic manufacturing scale. Petrol prices have crossed "
            "₹120 per litre, making the EV value proposition irresistible. But competition is fierce — "
            "Dharma Motors dominates, Chinese brands are undercutting on price, and India's extreme heat "
            "and monsoon seasons demand engineering resilience that many global entrants underestimate. "
            "The companies that allocate capital wisely will define India's mobility future."
        ),
        market_body=(
            "The Indian passenger EV market is growing at 55% annually and is projected to reach "
            "₹3,00,000 Cr by 2030. Four distinct consumer groups contest the market — each shaped by "
            "India's unique economics, climate, and digital-first consumer culture."
        ),
        market_kpis=[
            ("Market Size", "₹3L Cr by 2030", "dept_rd"),
            ("Growth Rate", "55% annually", "accent"),
            ("Segments", "4 consumer groups", "dept_mktg"),
        ],
        segments_intro="Winning in India requires matching product features to the country's unique buyer needs.",
        company_subtitle="Founded 2021  ·  Pune, Maharashtra  ·  1,500 employees  ·  NSE: VAYUHA",
        company_body=(
            "Vayuha Motors is a growth-stage Indian EV manufacturer that has successfully delivered "
            "two niche electric three-wheelers and a compact EV to market. The company has strong "
            "engineering talent — many recruited from Dharma Motors and Infosys — a loyal early-adopter "
            "fanbase in Maharashtra and Karnataka, and a lean but scalable manufacturing facility "
            "at the Chakan industrial area near Pune. The previous CFO departed last quarter to join "
            "a Chinese competitor. You are stepping in ahead of the company's most ambitious launch yet."
        ),
        product_subtitle="All-Electric Sedan — India's answer to the petrol car",
        product_body=(
            "The Vayuha Shakti is the company's entry into the mass-market Indian EV segment — "
            "a 5-seat all-electric sedan targeting a starting MSRP of ₹25,00,000. "
            "It is engineered on a new platform with a 60 kWh battery pack, heat-tolerant "
            "thermal management for Indian summers, and a connected software stack with "
            "multilingual voice interface supporting 12 Indian languages. "
            "Year 1 production capacity is 22,000 units."
        ),
        product_kpis=[
            ("MSRP", "₹25,00,000", "dept_rd"),
            ("Range (ARAI)", "450 km", "accent"),
            ("0–100 km/h", "4.8 sec", "dept_sales"),
            ("Yr 1 Capacity", "22,000 units", "dept_ops"),
        ],
        role_body=(
            "You are responsible for allocating Vayuha Motors' annual operating budget across four "
            "departments — R&D, Sales, Operations, and Marketing — over a 5-year launch window. "
            "Each year you set budgets AND choose a strategic direction for each department. "
            "Your decisions are final: once a year is locked, you cannot revisit it."
        ),
        objective_body=(
            "Your VPI score (0–1000+) is based on two equally weighted components: "
            "risk-adjusted profitability (50%) and Indian EV market share (50%). "
            "Consistent earnings beat volatile ones. Broad market presence beats narrow niches."
        ),
        departments_intro="Each department has distinct mechanics that affect your bottom line.",
        competitors_intro="You won't be operating in a vacuum. These rivals want the same Indian customers.",
        ready_headline="Your journey starts now — the Shakti awaits.",
        ready_body=(
            "You have been briefed on the Indian market, the company, the product, your role, "
            "and the competition. The background and objective tabs will remain available as "
            "reference during the simulation. Trust your strategy — allocate wisely."
        ),
    ),

    # Briefing
    briefing=BriefingContent(
        world_body=(
            "The year is 2025. India's EV revolution is exploding — and so is the competition. "
            "FAME III subsidies are reshaping affordability, PLI rewards domestic manufacturing, "
            "and petrol at ₹120/litre makes EVs irresistible. But Dharma dominates, Chinese brands "
            "undercut on price, and extreme heat and monsoons demand engineering resilience. "
            "The companies that allocate capital wisely will define India's mobility future."
        ),
        market_body=(
            "The Indian passenger EV market is growing at 55% annually and is projected to reach "
            "₹3,00,000 Cr by 2030. Four distinct consumer groups contest the market, each shaped "
            "by India's economics, extreme climate, and digital-first consumer culture. Winning "
            "requires spend directed at the right features for Indian buyers."
        ),
        company_body=(
            "Vayuha Motors is a growth-stage Indian EV manufacturer that has delivered two niche "
            "electric vehicles to market. Strong engineering talent from Dharma and Infosys, a loyal "
            "fanbase in Maharashtra and Karnataka, and a scalable Chakan manufacturing facility. "
            "The previous CFO departed last quarter. You are stepping in ahead of the company's "
            "most ambitious launch yet."
        ),
        product_body=(
            "The Vayuha Shakti is the company's entry into the mass-market Indian EV segment — "
            "a 5-seat all-electric sedan at ₹25,00,000 MSRP. The Shakti competes against Dharma, "
            "Longway, and Swaraj in India's fastest-growing automotive segment. Engineered with a "
            "60 kWh battery, heat-tolerant thermal management, and a 12-language voice interface. "
            "Year 1 capacity is 22,000 units. The Shakti's success determines whether Vayuha "
            "becomes a mainstream Indian EV brand — or remains a niche player."
        ),
        product_kpis=[
            ("MSRP", "₹25,00,000", "dept_rd"),
            ("Range (ARAI)", "450 km", "accent"),
            ("0–100 km/h", "4.8 sec", "dept_sales"),
            ("Yr 1 Capacity", "22,000 units", "dept_ops"),
        ],
        role_body=(
            "You are responsible for allocating Vayuha Motors' annual operating budget across four "
            "departments — R&D, Sales, Operations, and Marketing — over a 5-year launch window. "
            "Each year you set budgets AND choose a strategic direction for each department. "
            "These sub-decisions shape which consumer segments the Shakti appeals to and "
            "directly influence revenue. Your decisions are final."
        ),
        objective_body=(
            "Your VPI score (0–1000+) is based on two equally weighted components: "
            "risk-adjusted profitability (50%) and Indian EV market share (50%). "
            "Consistent earnings beat volatile ones. Broad market presence beats narrow niches. "
            "The best scores come from balancing both."
        ),
    ),
    objective_text={},
)


register_scenario("in", "ev", IN_EV)
