"""
scenarios/ca_hydration.py — Canada × Hydration Drink scenario.

PeakFlow Beverages — a Vancouver-based isotonic RTD brand targeting
Canada's active outdoor and hockey culture. Bilingual requirements.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.ca_hydration_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


CA_HYDRATION = ScenarioDefinition(
    scenario_id="ca_hydration",
    scenario_label="Canada — Hydration Drink",

    locale=LocaleConfig(
        country_code="CA", country_name="Canada",
        currency_symbol="C$", currency_code="CAD",
        currency_prefix=True,
        large_number_suffix="M", large_number_divisor=1_000_000,
    ),

    company=CompanyConfig(
        name="PeakFlow Beverages",
        product_name="PeakFlow Isotonic Electrolyte Drink",
        tagline="Hydration for every season, every Canadian",
        location="Vancouver, British Columbia",
        role_title="VP of Finance & Strategy",
        founding_year="2022",
        industry_label="Food & Beverage — Hydration",
        unit_price=32.0,
        unit_price_label="Case Price",
        unit_cost=12.0,
        year1_capacity=500_000,
        capacity_unit="cases",
    ),

    financials=FinancialConfig(
        total_budget=12_000_000,
        fixed_costs=17_000_000,
        base_revenue=8_000_000,
        profit_reinvestment_rate=0.03,
        inflation_min=0.03,
        inflation_max=0.09,
        underuse_threshold=0.15,
        underuse_penalty_rate=2.5,
        max_change_rate=0.30,
        demand_noise_std=0.10,
        scenario_drift_std=0.04,
        risk_penalty_lambda=1.5,
        num_periods=5,
        num_eval_scenarios=30,
        state_decay=0.5,
        vpi_ras_floor=3_318_380,
        vpi_ras_ceiling=15_279_850,
        vpi_share_floor=22.81,
        vpi_share_ceiling=27.58,
        competitor_presence_baseline=80_000_000,
    ),

    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    departments=[
        DepartmentParams(
            name="R&D", S_max=14_500_000, K=2_900_000, alpha=1.2,
            decay=0.60, min_spend=720_000, max_spend=6_000_000,
            state_sensitivity=0.10, catch_up_rate=0.25, sweet_spot_frac=0.70,
        ),
        DepartmentParams(
            name="Sales", S_max=12_800_000, K=3_000_000, alpha=0.9,
            decay=0.15, min_spend=960_000, max_spend=6_000_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Operations", S_max=14_500_000, K=2_200_000, alpha=0.85,
            decay=0.50, min_spend=720_000, max_spend=4_800_000,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Marketing", S_max=17_600_000, K=2_400_000, alpha=1.10,
            decay=0.35, min_spend=960_000, max_spend=6_000_000,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.60,
        ),
    ],

    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd", description=(
            "R&D drives new flavours, clinical studies, and packaging innovation. Returns are "
            "DELAYED. R&D's strongest synergy is with Marketing — clinical hydration data gives "
            "your brand credibility for health claims."
        ),
            background_description="R&D develops Canadian-inspired flavour profiles, optimizes formulations for health claims, conducts hydration research, and innovates sustainable packaging for the Canadian market.",
        ),
        DepartmentMeta(
            name="Sales", color_key="dept_sales", description=(
            "Sales gets product onto Canadian retail shelves and into fitness channels. "
            "CAPPED by Operations. Bilingual packaging and coast-to-coast logistics add complexity."
        ),
            background_description="Sales manages grocery shelf placement at Loblaws, Sobeys, and Metro, e-commerce through Amazon.ca, gym channel partnerships with GoodLife Fitness, and bilingual retail execution.",
        ),
        DepartmentMeta(
            name="Operations", color_key="dept_ops", description=(
            "Operations is the BOTTLENECK — but looser than pharma. Canada's extreme climate "
            "and vast geography create unique logistics challenges for beverage distribution."
        ),
            background_description="Operations manages co-packing in Canada, ingredient sourcing, bottling capacity, coast-to-coast cold chain logistics, and bilingual packaging production.",
        ),
        DepartmentMeta(
            name="Marketing", color_key="dept_mktg", description=(
            "Marketing is the DOMINANT lever. Brand awareness drives everything in CPG. "
            "Hockey culture, outdoor lifestyle, and bilingual campaigns are your tools."
        ),
            background_description="Marketing builds brand awareness through athlete endorsements, outdoor event sponsorships, grassroots gym sampling, and bilingual mass media campaigns. Hockey culture and outdoor lifestyle are the primary cultural touchpoints for Canadian consumers.",
        ),
    ],

    department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    segments=[
        ConsumerSegment(key="active", label="Active Lifestyle & Outdoor",
            description="Hockey players, skiers, hikers, runners — Canadians who live outdoors year-round. Buy at sporting goods stores, gyms, and online. Represent ~32% of the market.",
            market_weight=0.32),
        ConsumerSegment(key="wellness", label="Health & Wellness",
            description="Health-conscious Canadians who prefer natural, organic ingredients. Shop at Whole Foods, natural grocery, and DTC. Represent ~25% of the market.",
            market_weight=0.25),
        ConsumerSegment(key="everyday", label="Everyday Hydration",
            description="Mainstream grocery shoppers at Loblaws, Metro, Sobeys. Price-sensitive, taste-driven. The volume play. Represent ~23% of the market.",
            market_weight=0.23),
        ConsumerSegment(key="commercial", label="Offices, Gyms & Hospitality",
            description="Corporate wellness, GoodLife Fitness, hotels, hospitals. Bulk recurring. Represent ~20% of the market.",
            market_weight=0.20),
    ],

    segment_colors={"active": "#3D6B50", "wellness": "#4A7B9D", "everyday": "#C27D3A", "commercial": "#8B6BAE"},

    sub_decisions={
        "R&D": DepartmentSubDecisions(
            dept_name="R&D", label="R&D Focus", tooltip="Choose your product development priority.",
            options={
                "flavour": SubDecisionOption(key="flavour", label="Canadian Flavour Innovation",
                    description="Develop flavours inspired by Canadian ingredients — wild blueberry, maple electrolyte, Okanagan apple.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Sales": 0.08, "Marketing": 0.05},
                    segment_multipliers={"active": 1.10, "wellness": 1.10, "everyday": 1.35, "commercial": 0.90}),
                "clinical": SubDecisionOption(key="clinical", label="Clinical Hydration Studies",
                    description="Commission peer-reviewed research proving superior hydration for athletes and active Canadians.",
                    smax_mult=1.20, k_mult=1.25, synergy={"Marketing": 0.12},
                    segment_multipliers={"active": 1.30, "wellness": 1.35, "everyday": 0.80, "commercial": 1.10}),
                "costreduce": SubDecisionOption(key="costreduce", label="Formulation Cost Reduction",
                    description="Optimise ingredient blend to reduce cost per case.",
                    smax_mult=0.90, k_mult=0.75, synergy={"Operations": 0.15},
                    segment_multipliers={"active": 0.85, "wellness": 0.75, "everyday": 1.40, "commercial": 1.35}),
                "packaging": SubDecisionOption(key="packaging", label="Sustainable Canadian Packaging",
                    description="Recycled aluminium, compostable packaging, concentrate format for reduced shipping across Canada.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Marketing": 0.10},
                    segment_multipliers={"active": 1.10, "wellness": 1.40, "everyday": 0.90, "commercial": 1.15}),
            },
            default="clinical",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales", label="Sales Channel Strategy", tooltip="Sales is CAPPED by Operations.",
            options={
                "massretail": SubDecisionOption(key="massretail", label="National Grocery Push",
                    description="Loblaws, Metro, Sobeys, Costco — national grocery shelf placement.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Operations": 0.08},
                    segment_multipliers={"active": 0.85, "wellness": 0.80, "everyday": 1.50, "commercial": 0.90}),
                "dtc": SubDecisionOption(key="dtc", label="DTC & E-Commerce",
                    description="Amazon.ca, brand website subscriptions, online marketplace focus.",
                    smax_mult=1.10, k_mult=1.05, synergy={"Marketing": 0.10},
                    segment_multipliers={"active": 1.15, "wellness": 1.30, "everyday": 0.85, "commercial": 0.80}),
                "gymfitness": SubDecisionOption(key="gymfitness", label="Gym & Sports Channel",
                    description="GoodLife Fitness exclusivity, hockey arenas, ski lodges, outdoor retailers like MEC.",
                    smax_mult=1.05, k_mult=0.90, synergy={"Marketing": 0.06},
                    segment_multipliers={"active": 1.50, "wellness": 1.05, "everyday": 0.70, "commercial": 1.20}),
                "convenience": SubDecisionOption(key="convenience", label="Convenience & Impulse",
                    description="Circle K, Petro-Canada, Couche-Tard — convenience store impulse placement.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Operations": 0.05},
                    segment_multipliers={"active": 0.90, "wellness": 0.75, "everyday": 1.45, "commercial": 0.85}),
            },
            default="massretail",
        ),
        "Operations": DepartmentSubDecisions(
            dept_name="Operations", label="Operations Priority", tooltip="Operations CAPS Sales.",
            options={
                "capacity": SubDecisionOption(key="capacity", label="Bottling Expansion",
                    description="Add co-packing capacity — second bottling partner.",
                    smax_mult=1.20, k_mult=1.05, synergy={"Sales": 0.10},
                    segment_multipliers={"active": 1.10, "wellness": 1.00, "everyday": 1.25, "commercial": 1.20}),
                "logistics": SubDecisionOption(key="logistics", label="Coast-to-Coast Distribution",
                    description="Build national logistics across Canada's 6,000km — cold chain, regional warehouses.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Sales": 0.08},
                    segment_multipliers={"active": 1.10, "wellness": 1.10, "everyday": 1.15, "commercial": 1.15}),
                "efficiency": SubDecisionOption(key="efficiency", label="Production Cost Efficiency",
                    description="Optimise bottling, reduce waste, negotiate ingredient contracts.",
                    smax_mult=1.05, k_mult=0.85, synergy={"R&D": 0.05},
                    segment_multipliers={"active": 0.95, "wellness": 0.95, "everyday": 1.20, "commercial": 1.25}),
                "seasonal": SubDecisionOption(key="seasonal", label="Seasonal Demand Management",
                    description="Build inventory for summer surges and manage winter drawdowns.",
                    smax_mult=1.10, k_mult=1.00, synergy={"Sales": 0.06},
                    segment_multipliers={"active": 1.15, "wellness": 1.05, "everyday": 1.15, "commercial": 1.05}),
            },
            default="capacity",
        ),
        "Marketing": DepartmentSubDecisions(
            dept_name="Marketing", label="Marketing Strategy",
            tooltip="Marketing is the dominant lever. Brand wins in CPG.",
            options={
                "celebrity": SubDecisionOption(key="celebrity", label="Athlete & Celebrity Endorsement",
                    description="Sign a Canadian hockey star, Olympic athlete, or outdoor personality. High cost, massive reach.",
                    smax_mult=1.25, k_mult=1.20, synergy={"Sales": 0.12},
                    segment_multipliers={"active": 1.40, "wellness": 0.95, "everyday": 1.35, "commercial": 0.85}),
                "grassroots": SubDecisionOption(key="grassroots", label="Grassroots & Outdoor Events",
                    description="Marathons, Tough Mudder, ski events, hockey tournaments, community sport sampling.",
                    smax_mult=1.10, k_mult=0.85, synergy={"Sales": 0.08},
                    segment_multipliers={"active": 1.45, "wellness": 1.15, "everyday": 0.90, "commercial": 1.10}),
                "science": SubDecisionOption(key="science", label="Science & Health Credibility",
                    description="Lead with clinical data, naturopath endorsements, Health Canada NHP claims.",
                    smax_mult=1.15, k_mult=1.10, synergy={"R&D": 0.10},
                    segment_multipliers={"active": 1.15, "wellness": 1.40, "everyday": 0.80, "commercial": 1.20}),
                "mass_media": SubDecisionOption(key="mass_media", label="Bilingual Mass Media",
                    description="TV (Hockey Night in Canada), social media, bilingual digital campaigns across English and French Canada.",
                    smax_mult=1.15, k_mult=1.05, synergy={"Sales": 0.06},
                    segment_multipliers={"active": 0.95, "wellness": 0.90, "everyday": 1.40, "commercial": 1.00}),
            },
            default="grassroots",
        ),
    },

    competitors=[
        CompetitorDef(name="TitanAde Canada",
            industry="Global sports drink — Canadian subsidiary",
            location="Mississauga (HQ: Chicago/OmniCorp Beverages)", founded="1965",
            description="Dominant Canadian sports drink. NHL partnerships, massive distribution through OmniCorp bottler network.",
            display_label="Dominant Sports Drink (Canadian Arm)",
            base_revenue=60_000_000, growth_rate=0.03, margin=0.24,
            base_specs={"efficacy": 64, "taste": 71, "cost": 18},
            spec_growth_rates={"efficacy": 0.5, "taste": 1.0, "cost": 0.4},
            base_reach=1.4,  # Near-universal Canadian retail distribution
        ),
        CompetitorDef(name="NorthStar Hydration",
            industry="Canadian wellness drink brand",
            location="Toronto, Ontario", founded="2019",
            description="Toronto-based clean-label hydration brand. Strong DTC, wellness-positioned. Your closest competitor.",
            display_label="Canadian Wellness Hydration Rival",
            base_revenue=20_000_000, growth_rate=0.20, margin=0.1,
            base_specs={"efficacy": 74, "taste": 76, "cost": 28},
            spec_growth_rates={"efficacy": 2.0, "taste": 2.0, "cost": 0.6},
            base_reach=0.85,  # Growing wellness channel reach
        ),
        CompetitorDef(name="PowerFlow Canada",
            industry="Beverage giant's sports brand — Canadian operations",
            location="Toronto (HQ: Atlanta/GlobalDrink Holdings)", founded="1988",
            description="GlobalDrink Holdings's sports drink in Canada. Massive distribution through GlobalDrink's Canadian bottler. Weak on innovation.",
            display_label="Beverage Giant's Brand (Canadian Arm)",
            base_revenue=40_000_000, growth_rate=0.04, margin=0.21,
            base_specs={"efficacy": 60, "taste": 69, "cost": 16},
            spec_growth_rates={"efficacy": 0.3, "taste": 0.8, "cost": 0.3},
            base_reach=1.3,  # Strong national beverage distribution
        ),
        CompetitorDef(name="ArcticVive",
            industry="Canadian outdoor hydration startup",
            location="Calgary, Alberta", founded="2021",
            description="Calgary startup targeting outdoor and winter sport enthusiasts. Cold-weather-tested, adventure-branded.",
            display_label="Canadian Outdoor Startup Rival",
            base_revenue=8_000_000, growth_rate=0.25, margin=0.06,
            base_specs={"efficacy": 70, "taste": 73, "cost": 30},
            spec_growth_rates={"efficacy": 2.5, "taste": 2.5, "cost": 0.4},
            base_reach=0.65,  # Specialty outdoor and health channels only
        ),
    ],

    competitor_labels={
        "TitanAde Canada": "Dominant Sports Drink (Canadian Arm)",
        "NorthStar Hydration": "Canadian Wellness Hydration Rival",
        "PowerFlow Canada": "Beverage Giant's Brand (Canadian Arm)",
        "ArcticVive": "Canadian Outdoor Startup Rival",
    },

    product_specs=[
        ProductSpec(key="efficacy", label="Hydration Efficacy", unit="score", base_value=71, higher_is_better=True),
        ProductSpec(key="taste", label="Taste & Appeal", unit="score", base_value=74, higher_is_better=True),
        ProductSpec(key="cost", label="Cost Per Case", unit="C$/case", base_value=12.0, higher_is_better=False, display_format=".1f"),
    ],

    spec_evolution_rules=[
        SpecEvolutionRule(spec_key="efficacy", dept_name="R&D",
            base_growth=0.8, spend_sensitivity=4.0, dept_budget_ref=2_800_000,
            sub_decision_bonuses={"clinical": 3.5, "flavour": 0.5, "costreduce": -1.0, "packaging": 0.5},
            min_value=55, max_value=95),
        SpecEvolutionRule(spec_key="taste", dept_name="R&D",
            base_growth=1.0, spend_sensitivity=4.0, dept_budget_ref=2_800_000,
            sub_decision_bonuses={"flavour": 4.0, "clinical": 0.5, "costreduce": -1.5, "packaging": 1.0},
            min_value=55, max_value=95),
        SpecEvolutionRule(spec_key="cost", dept_name="R&D",
            base_growth=0.1, spend_sensitivity=-0.5, dept_budget_ref=2_800_000,
            sub_decision_bonuses={"costreduce": -1.5, "clinical": 0.3, "flavour": 0.2, "packaging": 0.4},
            min_value=6.0, max_value=20.0),
    ],

    segment_spec_preferences={
        "active": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.50, ideal_value=85, tolerance=15),
            SegmentSpecPreference(spec_key="taste", weight=0.30, ideal_value=80, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.20, ideal_value=12, tolerance=7),
        ],
        "wellness": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.40, ideal_value=85, tolerance=12),
            SegmentSpecPreference(spec_key="taste", weight=0.35, ideal_value=82, tolerance=12),
            SegmentSpecPreference(spec_key="cost", weight=0.25, ideal_value=14, tolerance=7),
        ],
        "everyday": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.15, ideal_value=70, tolerance=20),
            SegmentSpecPreference(spec_key="taste", weight=0.45, ideal_value=85, tolerance=12),
            SegmentSpecPreference(spec_key="cost", weight=0.40, ideal_value=10, tolerance=6),
        ],
        "commercial": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.30, ideal_value=75, tolerance=18),
            SegmentSpecPreference(spec_key="taste", weight=0.25, ideal_value=75, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.45, ideal_value=9, tolerance=5),
        ],
    },

    performance_index_name="PFI",
    performance_index_full="PeakFlow Performance Index",
    market_label="isotonic hydration market",

    bottleneck_cap_dept_idx=2,
    bottleneck_capped_dept_idx=1,
    bottleneck_cap_fraction=0.90,
    delayed_return_dept_idx=0,
    brand_equity_depts=[(3, 1.0), (0, 0.3)],

    general_news_pool=GENERAL_NEWS_POOL,
    dept_news_pool=DEPT_NEWS_POOL,
    competitor_news_pool=COMPETITOR_NEWS_POOL,

    storyboard=StoryboardContent(
        world_headline="The year is 2025. From frozen hockey rinks to sun-baked mountain trails, Canada is waking up to hydration.",
        world_body=(
            "Canada's functional beverage market has crossed C$2 billion. What was once a niche for "
            "marathon runners has become an everyday habit for commuters, students, and weekend warriors. "
            "But the Canadian market plays by different rules: bilingual packaging adds cost and complexity, "
            "the country stretches 6,000 km coast to coast making distribution a logistical puzzle, and "
            "winter months suppress demand while summer heat domes create panic buying. OmniCorp and "
            "GlobalDrink control 70% of Canadian shelf space through their bottler networks, and scrappy "
            "local startups keep emerging from Toronto, Vancouver, and Calgary. The brands that embrace "
            "Canada's outdoor culture, navigate its vast seasonal bilingual landscape, and survive the "
            "brutal winter quarter will win."
        ),
        market_body=(
            "The Canadian isotonic market is growing at 9% annually, driven by outdoor recreation, "
            "hockey culture, and health consciousness. Four segments compete for wallet share."
        ),
        market_kpis=[
            ("Market Size", "C$2B+", "dept_rd"),
            ("Growth Rate", "9% CAGR", "accent"),
            ("Segments", "4 consumer groups", "dept_mktg"),
        ],
        segments_intro="Each segment buys differently — the GoodLife gym-goer and the Loblaws weekly shopper are two different people.",
        company_subtitle="Founded 2022  ·  Vancouver, BC  ·  65 employees  ·  Series A funded",
        company_body=(
            "PeakFlow started in a shared commercial kitchen in Kitsilano, Vancouver. The founder — a "
            "former Canadian national team nutritionist — noticed that elite athletes were mixing their own "
            "electrolyte blends because nothing on the shelf was clean enough. She created a subtle, lightly "
            "flavoured isotonic drink using Canadian-sourced ingredients and tested it on the Sea-to-Sky "
            "trail running community. Within six months, every MEC store in BC was asking for it. The brand "
            "spread through hiking clubs, ski lodges, and GoodLife Fitness locations. Now PeakFlow is the "
            "top-selling independent hydration brand in Western Canada — but breaking into Ontario and "
            "Quebec, where the big grocery chains decide your fate, is a different game entirely."
        ),
        product_subtitle="Isotonic Electrolyte RTD — Hydration from coast to coast",
        product_body=(
            "PeakFlow is a 500ml isotonic electrolyte drink in recycled aluminium cans with bilingual "
            "English/French labelling. Canadian-sourced minerals, no artificial ingredients. C$32/case "
            "(24 cans). Tested through BC winters and Alberta chinooks. Year 1 capacity: 500,000 cases."
        ),
        product_kpis=[
            ("Case Price", "C$32/case", "dept_rd"),
            ("Efficacy Score", "71/100", "accent"),
            ("Taste Score", "74/100", "dept_sales"),
            ("Yr 1 Capacity", "500K cases", "dept_ops"),
        ],
        role_body=(
            "Allocate PeakFlow's budget over 5 years. This is a brand game — Marketing drives awareness, "
            "but you need shelf space (Sales) and cases to fill it (Operations). Athlete endorsements "
            "and outdoor event sampling are your biggest levers. The winter quarter will test your resolve."
        ),
        objective_body="PFI based on profitability (50%) and market share (50%). Consistency beats volatility.",
        departments_intro="Marketing is dominant in CPG — but shelf space (Sales) and production (Operations) enable delivery.",
        competitors_intro="The global beverage empires and local startups all want the same shelf space you need.",
        ready_headline="Your journey starts now — Vancouver loves you. Can all of Canada?",
        ready_body=(
            "Vancouver is yours. The West Coast trail runners swear by you. But Canada is a country of "
            "regions, and winning in BC does not mean winning at Loblaws. You need to cross the Rockies, "
            "charm Quebec in French, and survive the winter quarter. Five years. Coast to coast."
        ),
    ),

    briefing=BriefingContent(
        world_body=(
            "Canada's functional beverage market has crossed C$2B, growing at 9% CAGR. Bilingual packaging, "
            "6,000km coast-to-coast distribution, and extreme seasonality define the challenge. OmniCorp and "
            "GlobalDrink control 70% of shelf space. Hockey culture and outdoor lifestyle drive demand."
        ),
        market_body="Four segments: active/outdoor, wellness, everyday, commercial. Each needs different approach.",
        company_body=(
            "PeakFlow is Vancouver's cult hydration brand — born on BC's mountain trails, now the "
            "top independent isotonic in Western Canada. 65 employees, Series A. Founded by a former "
            "national team nutritionist. The challenge: break into Ontario and Quebec."
        ),
        product_body="Isotonic RTD, 500ml recycled aluminium cans, bilingual. C$32/case. Year 1: 500K cases.",
        product_kpis=[
            ("Case Price", "C$32/case", "dept_rd"),
            ("Efficacy Score", "71/100", "accent"),
            ("Taste Score", "74/100", "dept_sales"),
            ("Yr 1 Capacity", "500K cases", "dept_ops"),
        ],
        role_body="Allocate across 4 departments. Marketing dominant. Celebrity endorsements are high-risk, high-reward.",
        objective_body="PFI based on profitability (50%) and market share (50%).",
    ),
    objective_text={},
)


register_scenario("ca", "hydration", CA_HYDRATION)
