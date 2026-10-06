"""
scenarios/in_hydration.py — India × Hydration Drink scenario.

TazaHydra — a Mumbai-based isotonic RTD brand targeting India's massive
summer hydration market. Kirana distribution, cricket culture, Bollywood
endorsements, FSSAI regulatory. Mass-market ₹500/case positioning.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.in_hydration_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


IN_HYDRATION = ScenarioDefinition(
    scenario_id="in_hydration",
    scenario_label="India — Hydration Drink",

    locale=LocaleConfig(
        country_code="IN", country_name="India",
        currency_symbol="₹", currency_code="INR", currency_prefix=True,
        large_number_suffix="Cr", large_number_divisor=10_000_000,
        small_number_suffix="L", small_number_divisor=100_000,
        slider_step=100_000,
    ),

    company=CompanyConfig(
        name="TazaHydra",
        product_name="TazaHydra Isotonic Electrolyte Drink",
        tagline="India ka hydration — taza, clean, effective",
        location="Mumbai, Maharashtra",
        role_title="VP of Finance & Strategy",
        founding_year="2022",
        industry_label="Food & Beverage — Hydration",
        unit_price=500.0,           # ₹500/case (24 × 250ml bottles) — mass-market ₹20-25 per bottle
        unit_price_label="Case Price",
        unit_cost=180.0,
        year1_capacity=1_200_000,   # India: very high volume, low price
        capacity_unit="cases",
    ),

    financials=FinancialConfig(
        total_budget=800_000_000,           # ₹80 Cr
        fixed_costs=1_200_000_000,          # ₹120 Cr
        base_revenue=500_000_000,           # ₹50 Cr
        profit_reinvestment_rate=0.03,
        inflation_min=0.06, inflation_max=0.14,
        underuse_threshold=0.15, underuse_penalty_rate=2.5,
        max_change_rate=0.30,
        demand_noise_std=0.12,              # India: more volatile (monsoon, heat waves)
        scenario_drift_std=0.05,
        risk_penalty_lambda=1.5,
        num_periods=5, num_eval_scenarios=30, state_decay=0.5,
        vpi_ras_floor=80_925_800,
        vpi_ras_ceiling=901_569_500,
        vpi_share_floor=21.35, vpi_share_ceiling=25.9,
        competitor_presence_baseline=5_000_000_000,     # ₹500 Cr
    ),

    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    departments=[
        DepartmentParams(name="R&D", S_max=960_000_000, K=192_000_000, alpha=1.2,
            decay=0.60, min_spend=48_000_000, max_spend=400_000_000,
            state_sensitivity=0.10, catch_up_rate=0.25, sweet_spot_frac=0.70),
        DepartmentParams(name="Sales", S_max=840_000_000, K=200_000_000, alpha=0.9,
            decay=0.15, min_spend=64_000_000, max_spend=400_000_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80),
        DepartmentParams(name="Operations", S_max=960_000_000, K=144_000_000, alpha=0.85,
            decay=0.50, min_spend=48_000_000, max_spend=320_000_000,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80),
        DepartmentParams(name="Marketing", S_max=1_200_000_000, K=160_000_000, alpha=1.10,
            decay=0.35, min_spend=64_000_000, max_spend=400_000_000,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.60),
    ],

    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd", description="R&D drives heat-stable formulations, sachet formats, and Indian flavour innovation. Returns DELAYED. Synergy with Marketing through clinical credibility.",
            background_description="R&D develops Indian flavour profiles like nimbu pani and aam panna electrolyte blends, creates heat-stable formulations for 45-degree summers, develops affordable sachet formats, and conducts hydration research.",
        ),
        DepartmentMeta(
            name="Sales", color_key="dept_sales", description="Sales drives kirana distribution, modern trade placement, and quick commerce. CAPPED by Operations. India's 12M+ kirana stores are the ultimate distribution challenge.",
            background_description="Sales manages kirana store distribution across India's 12 million neighbourhood shops, modern trade placement at Reliance Retail and DMart, quick commerce through Blinkit and Swiggy, and institutional accounts.",
        ),
        DepartmentMeta(
            name="Operations", color_key="dept_ops", description="Operations is the BOTTLENECK — but looser than pharma. Monsoon logistics, summer surge capacity, and PET bottle supply are India-specific challenges.",
            background_description="Operations manages co-packing facilities, PET bottle sourcing, monsoon-proof logistics, summer surge capacity planning, and last-mile delivery to kirana stores across Tier-2 and Tier-3 cities.",
        ),
        DepartmentMeta(
            name="Marketing", color_key="dept_mktg", description="Marketing is DOMINANT. Cricket, Bollywood, and Instagram drive Indian beverage brands. Celebrity endorsements can make or break a brand overnight.",
            background_description="Marketing builds brand awareness through Bollywood and cricket celebrity endorsements, cricket tournament sponsorships, street-level sampling, and IPL/Instagram campaigns. Cricket culture and Bollywood celebrity power are the dominant forces in Indian consumer marketing.",
        ),
    ],

    department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    segments=[
        ConsumerSegment(key="summer", label="Mass-Market Summer Hydration",
            description="India's vast population buying hydration during 40°C+ summers. Kirana stores, railway stations, roadside vendors. Extremely price-sensitive at ₹20-30 per bottle. Represent ~40% of the market.",
            market_weight=0.40),
        ConsumerSegment(key="fitness", label="Urban Fitness & Sport",
            description="Metro gym-goers, cricket players, runners. Buy at modern trade, gyms, and online. Performance and taste matter. Represent ~22% of the market.",
            market_weight=0.22),
        ConsumerSegment(key="wellness", label="Health & Wellness (Premium)",
            description="Health-conscious urban Indians in Tier-1 cities. Buy at Nature's Basket, organic stores, and quick commerce. Clean label, low sugar. Represent ~15% of the market.",
            market_weight=0.15),
        ConsumerSegment(key="commercial", label="Offices, Hospitals & Canteens",
            description="IT parks, hospitals, factory canteens, railway caterers. Bulk recurring. Driven by cost per unit and reliability. Represent ~23% of the market.",
            market_weight=0.23),
    ],

    segment_colors={"summer": "#3D6B50", "fitness": "#4A7B9D", "wellness": "#C27D3A", "commercial": "#8B6BAE"},

    sub_decisions={
        "R&D": DepartmentSubDecisions(
            dept_name="R&D", label="R&D Focus", tooltip="Product development priority.",
            options={
                "flavour": SubDecisionOption(key="flavour", label="Indian Flavour Innovation",
                    description="Nimbu pani electrolyte, mango, aam panna, kokum — flavours India loves.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Sales": 0.08, "Marketing": 0.05},
                    segment_multipliers={"summer": 1.35, "fitness": 1.10, "wellness": 1.00, "commercial": 0.90}),
                "clinical": SubDecisionOption(key="clinical", label="Clinical Hydration Studies",
                    description="Commission research at Indian medical colleges proving superior hydration in extreme heat.",
                    smax_mult=1.20, k_mult=1.25, synergy={"Marketing": 0.12},
                    segment_multipliers={"summer": 0.90, "fitness": 1.30, "wellness": 1.40, "commercial": 1.10}),
                "costreduce": SubDecisionOption(key="costreduce", label="₹15 Sachet Format Development",
                    description="Ultra-low-cost single-serve sachet for kirana and street vendor distribution.",
                    smax_mult=0.95, k_mult=0.75, synergy={"Operations": 0.15, "Sales": 0.08},
                    segment_multipliers={"summer": 1.50, "fitness": 0.70, "wellness": 0.60, "commercial": 1.30}),
                "heatstable": SubDecisionOption(key="heatstable", label="Heat-Stable Formulation",
                    description="Optimise for India's 48°C+ summers. Extended shelf life without cold chain.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Operations": 0.10},
                    segment_multipliers={"summer": 1.30, "fitness": 1.05, "wellness": 1.10, "commercial": 1.20}),
            },
            default="heatstable",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales", label="Sales Channel", tooltip="Sales CAPPED by Operations.",
            options={
                "kirana": SubDecisionOption(key="kirana", label="Kirana & Traditional Trade",
                    description="India's 12M+ neighbourhood shops. The volume play — but requires massive distribution infrastructure.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Operations": 0.08},
                    segment_multipliers={"summer": 1.50, "fitness": 0.75, "wellness": 0.65, "commercial": 1.10}),
                "moderntrade": SubDecisionOption(key="moderntrade", label="Modern Trade & Quick Commerce",
                    description="Reliance Retail, DMart, Big Bazaar, Blinkit, Swiggy Instamart.",
                    smax_mult=1.10, k_mult=1.05, synergy={"Marketing": 0.08},
                    segment_multipliers={"summer": 0.90, "fitness": 1.25, "wellness": 1.35, "commercial": 0.95}),
                "gymfitness": SubDecisionOption(key="gymfitness", label="Gym & Cricket Channel",
                    description="Cult.fit, Gold's Gym, cricket academies, sports retailers.",
                    smax_mult=1.05, k_mult=0.90, synergy={"Marketing": 0.06},
                    segment_multipliers={"summer": 0.70, "fitness": 1.50, "wellness": 1.10, "commercial": 1.05}),
                "institutional": SubDecisionOption(key="institutional", label="Institutional & Railway",
                    description="IT park canteens, hospital cafeterias, railway station kiosks, factory canteens.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Operations": 0.05},
                    segment_multipliers={"summer": 1.10, "fitness": 0.80, "wellness": 0.70, "commercial": 1.50}),
            },
            default="kirana",
        ),
        "Operations": DepartmentSubDecisions(
            dept_name="Operations", label="Operations Priority", tooltip="Operations CAPS Sales.",
            options={
                "capacity": SubDecisionOption(key="capacity", label="Bottling Scale-Up with PLI",
                    description="Expand production capacity. Qualify for PLI scheme.",
                    smax_mult=1.20, k_mult=1.05, synergy={"Sales": 0.10},
                    segment_multipliers={"summer": 1.25, "fitness": 1.05, "wellness": 0.95, "commercial": 1.20}),
                "monsoon": SubDecisionOption(key="monsoon", label="Monsoon-Proof Distribution",
                    description="Build rain-resistant logistics, flood-proof warehouses, and all-weather delivery fleet.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Sales": 0.08},
                    segment_multipliers={"summer": 1.15, "fitness": 1.05, "wellness": 1.05, "commercial": 1.15}),
                "efficiency": SubDecisionOption(key="efficiency", label="Production Cost Efficiency",
                    description="Optimise bottling, local sourcing, reduce per-case cost to enable ₹20 retail pricing.",
                    smax_mult=1.05, k_mult=0.85, synergy={"R&D": 0.05},
                    segment_multipliers={"summer": 1.30, "fitness": 0.90, "wellness": 0.85, "commercial": 1.25}),
                "lastmile": SubDecisionOption(key="lastmile", label="Last-Mile Kirana Network",
                    description="Build distribution to 50,000+ kirana stores across Tier-2 and Tier-3 cities.",
                    smax_mult=1.10, k_mult=1.00, synergy={"Sales": 0.10},
                    segment_multipliers={"summer": 1.35, "fitness": 0.80, "wellness": 0.70, "commercial": 1.10}),
            },
            default="capacity",
        ),
        "Marketing": DepartmentSubDecisions(
            dept_name="Marketing", label="Marketing Strategy",
            tooltip="Marketing is dominant. Cricket, Bollywood, and social media drive Indian beverage brands.",
            options={
                "celebrity": SubDecisionOption(key="celebrity", label="Bollywood & Cricket Celebrity Endorsement",
                    description="Sign a Bollywood star or cricketer. Massive reach across India's 1.4B consumers. High cost, high risk.",
                    smax_mult=1.25, k_mult=1.20, synergy={"Sales": 0.12},
                    segment_multipliers={"summer": 1.35, "fitness": 1.30, "wellness": 0.85, "commercial": 0.90}),
                "grassroots": SubDecisionOption(key="grassroots", label="Cricket & Street Sampling",
                    description="Cricket tournament sponsorships, gully cricket sampling, marathon hydration, gym events.",
                    smax_mult=1.10, k_mult=0.85, synergy={"Sales": 0.08},
                    segment_multipliers={"summer": 1.20, "fitness": 1.45, "wellness": 1.05, "commercial": 1.10}),
                "science": SubDecisionOption(key="science", label="Medical & Health Credibility",
                    description="AIIMS studies, doctor endorsements, hospital partnerships. Position as medical-grade hydration.",
                    smax_mult=1.15, k_mult=1.10, synergy={"R&D": 0.10},
                    segment_multipliers={"summer": 0.90, "fitness": 1.10, "wellness": 1.45, "commercial": 1.20}),
                "mass_media": SubDecisionOption(key="mass_media", label="IPL & Digital Mass Media",
                    description="IPL advertising, Instagram Reels, vernacular YouTube. Broad-reach Indian digital campaigns.",
                    smax_mult=1.15, k_mult=1.05, synergy={"Sales": 0.06},
                    segment_multipliers={"summer": 1.30, "fitness": 1.00, "wellness": 0.80, "commercial": 1.00}),
            },
            default="celebrity",
        ),
    },

    competitors=[
        CompetitorDef(name="ElectraFresh",
            industry="Indian FMCG conglomerate hydration brand",
            location="Mumbai (Varuna FMCG subsidiary)", founded="2018",
            description="Varuna FMCG-backed mass-market hydration brand. Massive kirana distribution, cricket partnerships, ₹15-20 price point. The volume king.",
            display_label="FMCG Giant's Hydration Brand",
            base_revenue=3_500_000_000, growth_rate=0.08, margin=0.18,
            base_specs={"efficacy": 58, "taste": 72, "cost": 140},
            spec_growth_rates={"efficacy": 0.5, "taste": 1.0, "cost": 3},
            base_reach=1.5,  # Unmatched pan-India FMCG distribution
        ),
        CompetitorDef(name="VitalSip India",
            industry="International premium hydration brand",
            location="Mumbai (Japanese parent)", founded="2020",
            description="Japanese-backed Japanese isotonic-style brand entering India. Premium positioning, modern trade focus, limited kirana reach.",
            display_label="International Premium Hydration",
            base_revenue=1_200_000_000, growth_rate=0.20, margin=0.1,
            base_specs={"efficacy": 75, "taste": 78, "cost": 250},
            spec_growth_rates={"efficacy": 2.0, "taste": 2.0, "cost": 8},
            base_reach=0.85,  # Metro and modern trade focused, limited rural
        ),
        CompetitorDef(name="PowerZone India",
            industry="Global sports drink — Indian operations",
            location="Gurugram (OmniCorp Beverages subsidiary)", founded="1965",
            description="OmniCorp Beverages's Indian sports drink. Massive distribution, cricket sponsorships, aggressive pricing. Weak on health positioning.",
            display_label="Global Sports Drink (Indian Arm)",
            base_revenue=2_800_000_000, growth_rate=0.05, margin=0.2,
            base_specs={"efficacy": 55, "taste": 70, "cost": 130},
            spec_growth_rates={"efficacy": 0.3, "taste": 0.8, "cost": 2},
            base_reach=1.2,  # Strong modern trade presence across India
        ),
        CompetitorDef(name="NeerJal",
            industry="Indian Ayurvedic hydration startup",
            location="Bengaluru, India", founded="2021",
            description="Bengaluru startup combining traditional Indian ingredients (tulsi, amla, rock salt) with modern electrolyte science. Strong tech-city following.",
            display_label="Ayurvedic Hydration Startup",
            base_revenue=600_000_000, growth_rate=0.30, margin=0.06,
            base_specs={"efficacy": 68, "taste": 74, "cost": 200},
            spec_growth_rates={"efficacy": 3.0, "taste": 2.5, "cost": 5},
            base_reach=0.75,  # Growing but currently niche e-commerce/pharmacy
        ),
    ],

    competitor_labels={
        "ElectraFresh": "FMCG Giant's Hydration Brand",
        "VitalSip India": "International Premium Hydration",
        "PowerZone India": "Global Sports Drink (Indian Arm)",
        "NeerJal": "Ayurvedic Hydration Startup",
    },

    product_specs=[
        ProductSpec(key="efficacy", label="Hydration Efficacy", unit="score", base_value=68, higher_is_better=True),
        ProductSpec(key="taste", label="Taste & Appeal", unit="score", base_value=72, higher_is_better=True),
        ProductSpec(key="cost", label="Cost Per Case", unit="₹/case", base_value=180.0, higher_is_better=False, display_format=",.0f"),
    ],

    spec_evolution_rules=[
        SpecEvolutionRule(spec_key="efficacy", dept_name="R&D",
            base_growth=0.8, spend_sensitivity=4.0, dept_budget_ref=180_000_000,
            sub_decision_bonuses={"clinical": 3.5, "flavour": 0.5, "costreduce": -1.0, "heatstable": 1.5},
            min_value=50, max_value=95),
        SpecEvolutionRule(spec_key="taste", dept_name="R&D",
            base_growth=1.0, spend_sensitivity=4.0, dept_budget_ref=180_000_000,
            sub_decision_bonuses={"flavour": 4.0, "clinical": 0.5, "costreduce": -1.5, "heatstable": 0.5},
            min_value=50, max_value=95),
        SpecEvolutionRule(spec_key="cost", dept_name="R&D",
            base_growth=2, spend_sensitivity=-8, dept_budget_ref=180_000_000,
            sub_decision_bonuses={"costreduce": -20, "clinical": 5, "flavour": 3, "heatstable": 4},
            min_value=80, max_value=350),
    ],

    segment_spec_preferences={
        "summer": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.20, ideal_value=65, tolerance=20),
            SegmentSpecPreference(spec_key="taste", weight=0.35, ideal_value=80, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.45, ideal_value=130, tolerance=60),
        ],
        "fitness": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.45, ideal_value=82, tolerance=15),
            SegmentSpecPreference(spec_key="taste", weight=0.30, ideal_value=78, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.25, ideal_value=180, tolerance=80),
        ],
        "wellness": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.40, ideal_value=85, tolerance=12),
            SegmentSpecPreference(spec_key="taste", weight=0.35, ideal_value=82, tolerance=12),
            SegmentSpecPreference(spec_key="cost", weight=0.25, ideal_value=200, tolerance=80),
        ],
        "commercial": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.25, ideal_value=70, tolerance=20),
            SegmentSpecPreference(spec_key="taste", weight=0.25, ideal_value=75, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.50, ideal_value=120, tolerance=50),
        ],
    },

    performance_index_name="THI",
    performance_index_full="TazaHydra Performance Index",
    market_label="isotonic hydration market",

    bottleneck_cap_dept_idx=2, bottleneck_capped_dept_idx=1,
    bottleneck_cap_fraction=0.90,
    delayed_return_dept_idx=0,
    brand_equity_depts=[(3, 1.0), (0, 0.3)],

    general_news_pool=GENERAL_NEWS_POOL,
    dept_news_pool=DEPT_NEWS_POOL,
    competitor_news_pool=COMPETITOR_NEWS_POOL,

    storyboard=StoryboardContent(
        world_headline="The year is 2025. India has 1.4 billion people, summers that hit 48 degrees, and a hydration market that is about to explode.",
        world_body=(
            "India's functional beverage market has crossed 5,000 crore rupees and is growing at 25% "
            "annually — the fastest rate of any major market in the world. The drivers are elemental: "
            "summers that routinely exceed 45 degrees across North India, a cricket-obsessed population "
            "that watches IPL with a cold drink in hand, and a booming urban fitness culture in metros "
            "like Mumbai, Bangalore, and Delhi. But the Indian market plays by different rules. The mass "
            "market runs on 20-rupee sachets sold through 12 million kirana stores where the shopkeeper's "
            "recommendation matters more than any Instagram ad. Varuna FMCG and OmniCorp dominate through "
            "sheer distribution muscle. And every summer, dozens of new brands launch — most disappear "
            "by monsoon."
        ),
        market_body="Indian isotonic market growing at 25% CAGR — the fastest in the world. Four segments spanning village kiranas to Blinkit deliveries.",
        market_kpis=[("Market Size", "₹5,000 Cr+", "dept_rd"), ("Growth Rate", "25% CAGR", "accent"), ("Segments", "4 consumer groups", "dept_mktg")],
        segments_intro="The kirana shopkeeper in Lucknow and the Cult.fit member in Bangalore live in different Indias. You need to sell to both.",
        company_subtitle="Founded 2022  ·  Mumbai  ·  120 employees  ·  Series A funded",
        company_body=(
            "TazaHydra started at a fitness expo in Mumbai's BKC district. The founder — an IIT Bombay "
            "food scientist who spent three years at a Japanese beverage company — was convinced that India "
            "deserved a hydration drink designed for Indian summers, Indian taste buds, and Indian price "
            "points. The first batch used a heat-stable electrolyte formula that survived 45-degree Delhi "
            "summers without cold chain, flavoured with nimbu and rock salt — ingredients every Indian "
            "grandmother would recognise. It sold out at the expo in 90 minutes. Mumbai's gym community "
            "adopted it first, then Bangalore's tech crowd found it on quick commerce, then cricket "
            "coaches started buying cases for their academies. Now TazaHydra is the fastest-growing "
            "independent hydration brand in India's top 5 metros. But 70% of the market lives in Tier-2 "
            "and Tier-3 cities, and the kirana store owner has never heard of you."
        ),
        product_subtitle="Isotonic Electrolyte Drink — Designed for Indian summers, priced for Indian wallets",
        product_body=(
            "250ml PET bottles in cases of 24. Heat-stable formula survives 48-degree summers without "
            "cold chain. Nimbu pani and aam panna flavours. FSSAI-compliant. ₹500/case (~₹20 per bottle "
            "at retail). Year 1 capacity: 1.2 million cases."
        ),
        product_kpis=[("Case Price", "₹500/case", "dept_rd"), ("Efficacy", "68/100", "accent"), ("Taste", "72/100", "dept_sales"), ("Yr 1 Capacity", "1.2M cases", "dept_ops")],
        role_body=(
            "Allocate over 5 years. Marketing is dominant — Bollywood and cricket celebrity endorsements "
            "can catapult a brand from obscurity to household name overnight. But kirana distribution "
            "requires ground-level execution, and monsoon logistics will test your Operations."
        ),
        objective_body="THI based on profitability (50%) and market share (50%). Consistency beats volatility.",
        departments_intro="Marketing drives brand. Kirana distribution drives volume. Summer readiness drives revenue. Monsoon resilience determines survival.",
        competitors_intro="FMCG empires with decades of kirana relationships and global beverage giants with bottomless budgets want this market too.",
        ready_headline="Your journey starts now — Mumbai's gyms love you. Can 1.4 billion Indians say the same?",
        ready_body=(
            "Mumbai's gyms love you. Bangalore's tech crowd finds you on Blinkit. But India is 1.4 "
            "billion people and 12 million kirana stores, and the shopkeeper in Lucknow does not know "
            "your name. You need to survive the summer, the monsoon, and the FMCG giants. Five years. "
            "Make them count."
        ),
    ),

    briefing=BriefingContent(
        world_body=(
            "India's hydration market has crossed 5,000 crore rupees, growing at 25% CAGR — the fastest "
            "in the world. 48-degree summers, IPL cricket culture, and booming metro fitness drive demand. "
            "The mass market runs on 20-rupee sachets through 12 million kirana stores. Varuna FMCG and "
            "OmniCorp dominate. Dozens of brands launch every summer; most disappear by monsoon."
        ),
        market_body="Four segments: mass-market summer hydration, urban fitness and sport, health and wellness, and institutional buyers.",
        company_body=(
            "TazaHydra is Mumbai's fastest-growing hydration brand — heat-stable formula with Indian "
            "flavours, cult following in top 5 metros, growing fast on quick commerce. Founded by an "
            "IIT Bombay food scientist. 120 employees, Series A. The challenge: crack kirana distribution."
        ),
        product_body="250ml PET isotonic, heat-stable, nimbu and aam panna flavours. ₹500/case. Year 1: 1.2M cases.",
        product_kpis=[("Case Price", "₹500/case", "dept_rd"), ("Efficacy", "68/100", "accent"), ("Taste", "72/100", "dept_sales"), ("Yr 1 Capacity", "1.2M cases", "dept_ops")],
        role_body="4 departments, 5 years. Marketing dominant. Bollywood and cricket endorsements are high-risk, high-reward.",
        objective_body="THI based on profitability (50%) and market share (50%).",
    ),
    objective_text={},
)

register_scenario("in", "hydration", IN_HYDRATION)
