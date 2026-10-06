"""
scenarios/uk_hydration.py — United Kingdom × Hydration Drink scenario.

AquaPulse — a London-based isotonic RTD brand. UK-specific: SDIL sugar tax,
Tesco/Sainsbury's shelf wars, Premier League football culture, ASA advertising standards.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.uk_hydration_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


UK_HYDRATION = ScenarioDefinition(
    scenario_id="uk_hydration",
    scenario_label="United Kingdom — Hydration Drink",

    locale=LocaleConfig(
        country_code="GB", country_name="United Kingdom",
        currency_symbol="£", currency_code="GBP", currency_prefix=True,
        large_number_suffix="M", large_number_divisor=1_000_000,
    ),

    company=CompanyConfig(
        name="AquaPulse",
        product_name="AquaPulse Isotonic Electrolyte Drink",
        tagline="Everyday hydration, brilliantly British",
        location="London, United Kingdom",
        role_title="VP of Finance & Strategy",
        founding_year="2022",
        industry_label="Food & Beverage — Hydration",
        unit_price=22.0, unit_price_label="Case Price",
        unit_cost=8.0, year1_capacity=600_000, capacity_unit="cases",
    ),

    financials=FinancialConfig(
        total_budget=10_000_000, fixed_costs=15_000_000, base_revenue=7_000_000,
        profit_reinvestment_rate=0.03, inflation_min=0.04, inflation_max=0.10,
        underuse_threshold=0.15, underuse_penalty_rate=2.5, max_change_rate=0.30,
        demand_noise_std=0.10, scenario_drift_std=0.04, risk_penalty_lambda=1.5,
        num_periods=5, num_eval_scenarios=30, state_decay=0.5,
        vpi_ras_floor=1_563_860, vpi_ras_ceiling=11_368_950,
        vpi_share_floor=23.47, vpi_share_ceiling=28.32,
        competitor_presence_baseline=70_000_000,
    ),

    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    departments=[
        DepartmentParams(name="R&D", S_max=12_000_000, K=2_400_000, alpha=1.2,
            decay=0.60, min_spend=600_000, max_spend=5_000_000,
            state_sensitivity=0.10, catch_up_rate=0.25, sweet_spot_frac=0.70),
        DepartmentParams(name="Sales", S_max=10_500_000, K=2_500_000, alpha=0.9,
            decay=0.15, min_spend=800_000, max_spend=5_000_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80),
        DepartmentParams(name="Operations", S_max=12_000_000, K=1_800_000, alpha=0.85,
            decay=0.50, min_spend=600_000, max_spend=4_000_000,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80),
        DepartmentParams(name="Marketing", S_max=14_600_000, K=2_000_000, alpha=1.10,
            decay=0.35, min_spend=800_000, max_spend=5_000_000,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.60),
    ],

    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd", description="R&D drives flavour innovation, clinical studies, and SDIL-compliant formulation. Returns DELAYED. Synergy with Marketing through clinical credibility.",
            background_description="R&D develops British-inspired flavours, optimizes formulations to comply with the sugar tax (SDIL), conducts hydration research, and innovates DRS-compatible sustainable packaging.",
        ),
        DepartmentMeta(
            name="Sales", color_key="dept_sales", description="Sales gets product onto supermarket shelves and into fitness channels. CAPPED by Operations. UK supermarket buyers are notoriously demanding.",
            background_description="Sales manages supermarket shelf placement at Tesco, Sainsbury's, and Asda, travel retail through WHSmith, e-commerce via Amazon.co.uk and Ocado, and gym channel partnerships.",
        ),
        DepartmentMeta(
            name="Operations", color_key="dept_ops", description="Operations is the BOTTLENECK — but looser than pharma. HGV driver shortages and post-Brexit logistics add UK-specific challenges.",
            background_description="Operations manages UK co-packing relationships, ingredient sourcing, bottling capacity, national distribution logistics, and navigates post-Brexit supply chain complexity.",
        ),
        DepartmentMeta(
            name="Marketing", color_key="dept_mktg", description="Marketing is DOMINANT. Brand awareness is everything. Football culture, ASA-compliant advertising, and social media drive UK beverage sales.",
            background_description="Marketing builds brand awareness through footballer and celebrity endorsements, parkrun and gym event sponsorships, social media campaigns, and ITV/digital advertising. Football culture and the health-conscious commuter lifestyle are the primary cultural touchpoints.",
        ),
    ],

    department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    segments=[
        ConsumerSegment(key="healthcommute", label="Health-Conscious Commuters",
            description="Daily hydration buyers — commuters, office workers, health-aware Londoners. Buy at Boots, M&S Food, and Pret. Driven by low sugar and clean label. Represent ~35% of the market.",
            market_weight=0.35),
        ConsumerSegment(key="sport", label="Sport & Fitness",
            description="Gym members, parkrunners, football players. Buy at gyms and sports retailers. Driven by performance claims and athlete endorsements. Represent ~25% of the market.",
            market_weight=0.25),
        ConsumerSegment(key="youth", label="Youth & Students",
            description="University students, festival-goers, nightlife recovery. Price-sensitive, social-media driven. Represent ~20% of the market.",
            market_weight=0.20),
        ConsumerSegment(key="commercial", label="Offices & Hospitality",
            description="Corporate wellness, hotel chains, NHS hospitals, catering. Bulk recurring. Represent ~20% of the market.",
            market_weight=0.20),
    ],

    segment_colors={"healthcommute": "#3D6B50", "sport": "#4A7B9D", "youth": "#C27D3A", "commercial": "#8B6BAE"},

    sub_decisions={
        "R&D": DepartmentSubDecisions(
            dept_name="R&D", label="R&D Focus", tooltip="Product development priority.",
            options={
                "flavour": SubDecisionOption(key="flavour", label="British Flavour Innovation",
                    description="Elderflower, rhubarb & ginger, blackcurrant — quintessentially British flavour profiles.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Sales": 0.08, "Marketing": 0.05},
                    segment_multipliers={"healthcommute": 1.15, "sport": 1.05, "youth": 1.35, "commercial": 0.90}),
                "clinical": SubDecisionOption(key="clinical", label="Clinical Hydration Studies",
                    description="Peer-reviewed research for credibility and ASA-compliant health claims.",
                    smax_mult=1.20, k_mult=1.25, synergy={"Marketing": 0.12},
                    segment_multipliers={"healthcommute": 1.30, "sport": 1.30, "youth": 0.80, "commercial": 1.15}),
                "sdil": SubDecisionOption(key="sdil", label="Sugar Tax Compliant Reformulation",
                    description="Optimise formula to stay below SDIL threshold — critical for UK pricing competitiveness.",
                    smax_mult=0.95, k_mult=0.80, synergy={"Operations": 0.12, "Sales": 0.06},
                    segment_multipliers={"healthcommute": 1.40, "sport": 1.10, "youth": 1.15, "commercial": 1.25}),
                "packaging": SubDecisionOption(key="packaging", label="Sustainable Packaging",
                    description="Recycled aluminium, DRS-compatible cans, concentrate formats.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Marketing": 0.10},
                    segment_multipliers={"healthcommute": 1.35, "sport": 1.00, "youth": 1.10, "commercial": 1.15}),
            },
            default="sdil",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales", label="Sales Channel", tooltip="Sales CAPPED by Operations.",
            options={
                "supermarket": SubDecisionOption(key="supermarket", label="Supermarket Shelf Push",
                    description="Tesco, Sainsbury's, Asda, Morrisons — the big four plus Aldi and Lidl.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Operations": 0.08},
                    segment_multipliers={"healthcommute": 1.10, "sport": 0.85, "youth": 1.20, "commercial": 0.90}),
                "dtc": SubDecisionOption(key="dtc", label="DTC & E-Commerce",
                    description="Amazon.co.uk, Ocado, brand website subscriptions.",
                    smax_mult=1.10, k_mult=1.05, synergy={"Marketing": 0.10},
                    segment_multipliers={"healthcommute": 1.25, "sport": 1.10, "youth": 1.15, "commercial": 0.80}),
                "gymfitness": SubDecisionOption(key="gymfitness", label="Gym & Sport Channel",
                    description="PureGym, David Lloyd, Virgin Active, football clubs, parkrun events.",
                    smax_mult=1.05, k_mult=0.90, synergy={"Marketing": 0.06},
                    segment_multipliers={"healthcommute": 0.80, "sport": 1.50, "youth": 1.00, "commercial": 1.15}),
                "travel": SubDecisionOption(key="travel", label="Travel & Convenience",
                    description="WHSmith Travel, Pret A Manger, M&S Simply Food, train stations, airports.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Operations": 0.05},
                    segment_multipliers={"healthcommute": 1.45, "sport": 0.80, "youth": 1.10, "commercial": 0.85}),
            },
            default="supermarket",
        ),
        "Operations": DepartmentSubDecisions(
            dept_name="Operations", label="Operations Priority", tooltip="Operations CAPS Sales.",
            options={
                "capacity": SubDecisionOption(key="capacity", label="Bottling Expansion",
                    description="Add co-packing capacity.", smax_mult=1.20, k_mult=1.05, synergy={"Sales": 0.10},
                    segment_multipliers={"healthcommute": 1.10, "sport": 1.05, "youth": 1.15, "commercial": 1.20}),
                "logistics": SubDecisionOption(key="logistics", label="National Distribution",
                    description="Build UK-wide logistics. Address HGV driver shortages and post-Brexit complexity.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Sales": 0.08},
                    segment_multipliers={"healthcommute": 1.10, "sport": 1.05, "youth": 1.10, "commercial": 1.15}),
                "efficiency": SubDecisionOption(key="efficiency", label="Cost Efficiency",
                    description="Optimise production. Reduce per-case cost.", smax_mult=1.05, k_mult=0.85, synergy={"R&D": 0.05},
                    segment_multipliers={"healthcommute": 0.95, "sport": 0.95, "youth": 1.20, "commercial": 1.25}),
                "seasonal": SubDecisionOption(key="seasonal", label="Seasonal Readiness",
                    description="Summer surge preparation. UK demand highly seasonal.",
                    smax_mult=1.10, k_mult=1.00, synergy={"Sales": 0.06},
                    segment_multipliers={"healthcommute": 1.10, "sport": 1.15, "youth": 1.15, "commercial": 1.05}),
            },
            default="capacity",
        ),
        "Marketing": DepartmentSubDecisions(
            dept_name="Marketing", label="Marketing Strategy", tooltip="Marketing is dominant in UK CPG.",
            options={
                "celebrity": SubDecisionOption(key="celebrity", label="Footballer & Celebrity Endorsement",
                    description="Sign a Premier League star or British celebrity. Massive reach but high cost and scandal risk.",
                    smax_mult=1.25, k_mult=1.20, synergy={"Sales": 0.12},
                    segment_multipliers={"healthcommute": 1.10, "sport": 1.40, "youth": 1.35, "commercial": 0.80}),
                "grassroots": SubDecisionOption(key="grassroots", label="Grassroots & Events",
                    description="parkrun sponsorship, gym sampling, marathon hydration stations, festival presence.",
                    smax_mult=1.10, k_mult=0.85, synergy={"Sales": 0.08},
                    segment_multipliers={"healthcommute": 1.05, "sport": 1.45, "youth": 1.20, "commercial": 1.05}),
                "science": SubDecisionOption(key="science", label="Science & NHS Credibility",
                    description="Clinical data, NHS endorsement, British Nutrition Foundation approval.",
                    smax_mult=1.15, k_mult=1.10, synergy={"R&D": 0.10},
                    segment_multipliers={"healthcommute": 1.40, "sport": 1.10, "youth": 0.80, "commercial": 1.25}),
                "mass_media": SubDecisionOption(key="mass_media", label="Mass Media & Digital",
                    description="ITV Sport ads, social media, broad-reach digital campaigns.",
                    smax_mult=1.15, k_mult=1.05, synergy={"Sales": 0.06},
                    segment_multipliers={"healthcommute": 1.00, "sport": 0.95, "youth": 1.35, "commercial": 0.95}),
            },
            default="grassroots",
        ),
    },

    competitors=[
        CompetitorDef(name="LumiSport", industry="UK sports drink incumbent",
            location="London (Kirin-Pacific-owned)", founded="1927",
            description="Britain's original sports drink — decades of brand recognition, football partnerships, massive distribution. Recently reformulated to avoid sugar tax.",
            display_label="UK Sports Drink Incumbent",
            base_revenue=50_000_000, growth_rate=0.02, margin=0.24,
            base_specs={"efficacy": 63, "taste": 74, "cost": 16},
            spec_growth_rates={"efficacy": 0.5, "taste": 0.8, "cost": 0.3},
            base_reach=1.35,  # Dominant UK supermarket and sports retail presence
        ),
        CompetitorDef(name="VivaSport UK", industry="European sports nutrition brand",
            location="Manchester (HQ: Munich)", founded="2015",
            description="German-owned performance brand. Science-forward, strong in gym channel. Growing through fitness influencer partnerships.",
            display_label="European Performance Brand",
            base_revenue=20_000_000, growth_rate=0.15, margin=0.11,
            base_specs={"efficacy": 76, "taste": 71, "cost": 24},
            spec_growth_rates={"efficacy": 2.5, "taste": 1.5, "cost": 0.5},
            base_reach=0.9,  # Growing UK presence, strong online
        ),
        CompetitorDef(name="PowerFlow UK", industry="Beverage giant's UK sports brand",
            location="London (GlobalDrink Holdings subsidiary)", founded="1988",
            description="GlobalDrink Holdings's UK sports drink. Massive distribution through GlobalDrink bottler. Weak on innovation, strong on shelf space.",
            display_label="Beverage Giant's UK Brand",
            base_revenue=35_000_000, growth_rate=0.03, margin=0.2,
            base_specs={"efficacy": 59, "taste": 70, "cost": 14},
            spec_growth_rates={"efficacy": 0.3, "taste": 0.8, "cost": 0.2},
            base_reach=1.3,  # Strong UK FMCG distribution
        ),
        CompetitorDef(name="PureHydrate", industry="UK clean-label startup",
            location="Bristol, United Kingdom", founded="2021",
            description="Bristol-based organic hydration brand. Whole Foods and health stores. Your closest competitor.",
            display_label="UK Clean-Label Startup Rival",
            base_revenue=7_000_000, growth_rate=0.25, margin=0.06,
            base_specs={"efficacy": 72, "taste": 73, "cost": 26},
            spec_growth_rates={"efficacy": 2.5, "taste": 2.5, "cost": 0.4},
            base_reach=0.65,  # Health food and DTC channels only
        ),
    ],

    competitor_labels={
        "LumiSport": "UK Sports Drink Incumbent",
        "VivaSport UK": "European Performance Brand",
        "PowerFlow UK": "Beverage Giant's UK Brand",
        "PureHydrate": "UK Clean-Label Startup Rival",
    },

    product_specs=[
        ProductSpec(key="efficacy", label="Hydration Efficacy", unit="score", base_value=70, higher_is_better=True),
        ProductSpec(key="taste", label="Taste & Appeal", unit="score", base_value=73, higher_is_better=True),
        ProductSpec(key="cost", label="Cost Per Case", unit="£/case", base_value=8.0, higher_is_better=False, display_format=".1f"),
    ],

    spec_evolution_rules=[
        SpecEvolutionRule(spec_key="efficacy", dept_name="R&D",
            base_growth=0.8, spend_sensitivity=4.0, dept_budget_ref=2_400_000,
            sub_decision_bonuses={"clinical": 3.5, "flavour": 0.5, "sdil": 0.0, "packaging": 0.5},
            min_value=55, max_value=95),
        SpecEvolutionRule(spec_key="taste", dept_name="R&D",
            base_growth=1.0, spend_sensitivity=4.0, dept_budget_ref=2_400_000,
            sub_decision_bonuses={"flavour": 4.0, "clinical": 0.5, "sdil": -0.5, "packaging": 1.0},
            min_value=55, max_value=95),
        SpecEvolutionRule(spec_key="cost", dept_name="R&D",
            base_growth=0.1, spend_sensitivity=-0.4, dept_budget_ref=2_400_000,
            sub_decision_bonuses={"sdil": -1.2, "clinical": 0.2, "flavour": 0.2, "packaging": 0.3},
            min_value=4.0, max_value=14.0),
    ],

    segment_spec_preferences={
        "healthcommute": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.35, ideal_value=82, tolerance=15),
            SegmentSpecPreference(spec_key="taste", weight=0.35, ideal_value=82, tolerance=12),
            SegmentSpecPreference(spec_key="cost", weight=0.30, ideal_value=8, tolerance=5),
        ],
        "sport": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.50, ideal_value=85, tolerance=15),
            SegmentSpecPreference(spec_key="taste", weight=0.30, ideal_value=78, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.20, ideal_value=9, tolerance=5),
        ],
        "youth": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.15, ideal_value=70, tolerance=20),
            SegmentSpecPreference(spec_key="taste", weight=0.50, ideal_value=85, tolerance=10),
            SegmentSpecPreference(spec_key="cost", weight=0.35, ideal_value=6, tolerance=4),
        ],
        "commercial": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.30, ideal_value=75, tolerance=18),
            SegmentSpecPreference(spec_key="taste", weight=0.25, ideal_value=75, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.45, ideal_value=6, tolerance=4),
        ],
    },

    performance_index_name="API",
    performance_index_full="AquaPulse Performance Index",
    market_label="isotonic hydration market",

    bottleneck_cap_dept_idx=2, bottleneck_capped_dept_idx=1,
    bottleneck_cap_fraction=0.90,
    delayed_return_dept_idx=0,
    brand_equity_depts=[(3, 1.0), (0, 0.3)],

    general_news_pool=GENERAL_NEWS_POOL,
    dept_news_pool=DEPT_NEWS_POOL,
    competitor_news_pool=COMPETITOR_NEWS_POOL,

    storyboard=StoryboardContent(
        world_headline="The year is 2025. Britain is getting hotter, the sugar tax is reshaping the drinks aisle, and the race for the nation's thirst is on.",
        world_body=(
            "The UK functional beverage market has crossed 1.5 billion pounds. Record-breaking summer "
            "temperatures are rewriting what Brits reach for at Tesco, the SDIL sugar tax is punishing "
            "high-sugar formulations and rewarding reformulation, and the parkrun generation has made "
            "fitness-adjacent hydration a daily habit. But supermarket shelf space in Britain is the most "
            "brutally contested real estate in consumer goods — Tesco, Sainsbury's, and Asda can delist "
            "a brand overnight if velocity slips, and the discounters Aldi and Lidl are growing faster "
            "than anyone. Football culture offers massive marketing reach through Premier League "
            "partnerships, but the Advertising Standards Authority keeps claims honest."
        ),
        market_body="UK isotonic market growing at 8% CAGR. Four consumer segments with very different shopping habits.",
        market_kpis=[("Market Size", "£1.5B+", "dept_rd"), ("Growth Rate", "8% CAGR", "accent"), ("Segments", "4 consumer groups", "dept_mktg")],
        segments_intro="The Boots commuter, the PureGym regular, the festival-goer, and the office manager — four different buyers, four different pitches.",
        company_subtitle="Founded 2022  ·  London  ·  55 employees  ·  Seed+ funded",
        company_body=(
            "AquaPulse began in a Hackney warehouse when two former Harlequins rugby nutritionists decided "
            "that British consumers deserved better than neon-coloured sugar water. They created a gentle, "
            "subtly flavoured isotonic drink inspired by Japanese hydration science — low sugar, SDIL-compliant "
            "from day one, clean label, British-sourced minerals. The first cases went to independent health "
            "food shops in East London, then PureGym took notice, then Whole Foods. Now AquaPulse has a cult "
            "following among London commuters and gym-goers, a growing Ocado presence, and a quality reputation "
            "that Tesco buyers have been quietly watching. The challenge: can a brand born in Hackney "
            "win the Big Four supermarkets and become a household name?"
        ),
        product_subtitle="Isotonic Electrolyte RTD — Gentle hydration, brilliantly British",
        product_body=(
            "500ml aluminium cans, SDIL-compliant from day one. British-sourced electrolyte minerals. "
            "Subtle elderflower and blackcurrant flavours. £22/case (24 cans). Year 1 capacity: 600K cases."
        ),
        product_kpis=[("Case Price", "£22/case", "dept_rd"), ("Efficacy", "70/100", "accent"), ("Taste", "73/100", "dept_sales"), ("Yr 1 Capacity", "600K cases", "dept_ops")],
        role_body=(
            "Allocate over 5 years. Marketing is dominant — footballer endorsements and parkrun "
            "sponsorships drive awareness. But SDIL compliance shapes formulation, and supermarket "
            "velocity determines whether you stay on the shelf."
        ),
        objective_body="API based on profitability (50%) and market share (50%). Consistency beats volatility.",
        departments_intro="Marketing drives brand. Sugar tax compliance drives formulation. Supermarket velocity determines survival.",
        competitors_intro="Britain's drinks aisle is controlled by global empires with local bottling muscle and decades of buyer relationships.",
        ready_headline="Your journey starts now — East London loves you. Can all of Britain?",
        ready_body=(
            "East London loves you. PureGym loves you. But Britain is a nation that buys its drinks "
            "at Tesco and watches its football on Sky. You need supermarket velocity, SDIL compliance, "
            "and cultural relevance. Five years to become a household name."
        ),
    ),

    briefing=BriefingContent(
        world_body=(
            "The UK functional beverage market has crossed 1.5 billion pounds, driven by record heat, the "
            "SDIL sugar tax, and the parkrun generation. Supermarket shelf space is ruthlessly competitive — "
            "Tesco can delist you overnight. Football culture offers reach. ASA keeps claims honest."
        ),
        market_body="Four segments: health-conscious commuters, sport/fitness enthusiasts, youth/students, and offices/hospitality.",
        company_body=(
            "AquaPulse is a London-born isotonic brand — SDIL-compliant from day one, cult following among "
            "gym-goers and commuters, growing Ocado and PureGym presence. 55 employees, Seed+ funded. "
            "Founded by two former rugby nutritionists. The challenge: win the Big Four supermarkets."
        ),
        product_body="500ml aluminium cans, SDIL-compliant, British minerals. £22/case. Year 1: 600K cases.",
        product_kpis=[("Case Price", "£22/case", "dept_rd"), ("Efficacy", "70/100", "accent"), ("Taste", "73/100", "dept_sales"), ("Yr 1 Capacity", "600K cases", "dept_ops")],
        role_body="4 departments, 5 years. Marketing dominant. SDIL compliance shapes your formulation. Supermarket velocity is survival.",
        objective_body="API based on profitability (50%) and market share (50%).",
    ),
    objective_text={},
)

register_scenario("uk", "hydration", UK_HYDRATION)
