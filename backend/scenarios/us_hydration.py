"""
scenarios/us_hydration.py — United States × Hydration Drink scenario.

HydraVive — an Austin-based isotonic electrolyte RTD brand (Japanese isotonic-style
everyday hydration). CPG-tuned mechanics: Marketing dominant, Operations bottleneck
looser, R&D has weaker standalone impact but strong Marketing synergy.
"""

from scenarios import register_scenario
from scenarios.base import (
    ScenarioDefinition, LocaleConfig, CompanyConfig, FinancialConfig,
    TimerConfig, DepartmentParams, DepartmentMeta, ConsumerSegment,
    SubDecisionOption, DepartmentSubDecisions, CompetitorDef,
    StoryboardContent, BriefingContent,
    ProductSpec, SpecEvolutionRule, SegmentSpecPreference,
)

from scenarios.us_hydration_news import COMPETITOR_NEWS_POOL, DEPT_NEWS_POOL, GENERAL_NEWS_POOL


US_HYDRATION = ScenarioDefinition(
    scenario_id="us_hydration",
    scenario_label="United States — Hydration Drink",

    locale=LocaleConfig(
        country_code="US", country_name="United States",
        currency_symbol="$", currency_code="USD",
        currency_prefix=True,
        large_number_suffix="M", large_number_divisor=1_000_000,
    ),

    company=CompanyConfig(
        name="HydraVive",
        product_name="HydraVive Isotonic Electrolyte Drink",
        tagline="Everyday hydration, scientifically formulated",
        location="Austin, Texas",
        role_title="VP of Finance & Strategy",
        founding_year="2022",
        industry_label="Food & Beverage — Hydration",
        unit_price=28.0,            # $28 per case (24 × 500ml bottles)
        unit_price_label="Case Price",
        unit_cost=10.0,
        year1_capacity=800_000,     # 800K cases/yr
        capacity_unit="cases",
    ),

    financials=FinancialConfig(
        total_budget=15_000_000,
        fixed_costs=22_000_000,
        base_revenue=10_000_000,
        profit_reinvestment_rate=0.03,
        inflation_min=0.03,
        inflation_max=0.09,
        underuse_threshold=0.15,
        underuse_penalty_rate=2.5,
        max_change_rate=0.30,
        demand_noise_std=0.10,      # Higher noise — CPG is more volatile
        scenario_drift_std=0.04,
        risk_penalty_lambda=1.5,
        num_periods=5,
        num_eval_scenarios=30,
        state_decay=0.5,
        # Placeholder — Monte Carlo calibrated
        vpi_ras_floor=3_341_360,
        vpi_ras_ceiling=18_181_200,
        vpi_share_floor=20.4,
        vpi_share_ceiling=24.78,
        competitor_presence_baseline=100_000_000,
    ),

    timer=TimerConfig(course_seconds=300, competition_seconds=1800),

    # CPG-tuned departments:
    # Marketing has highest S_max (brand is everything in CPG)
    # R&D has lowest ceiling (formulation helps but doesn't transform)
    # Operations bottleneck is looser (0.90 cap vs 0.85 for EV)
    departments=[
        DepartmentParams(
            name="R&D", S_max=18_000_000, K=3_600_000, alpha=1.2,
            decay=0.60, min_spend=900_000, max_spend=7_500_000,
            state_sensitivity=0.10, catch_up_rate=0.25, sweet_spot_frac=0.70,
        ),
        DepartmentParams(
            name="Sales", S_max=16_000_000, K=3_800_000, alpha=0.9,
            decay=0.15, min_spend=1_200_000, max_spend=7_500_000,
            state_sensitivity=0.05, catch_up_rate=0.35, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Operations", S_max=18_000_000, K=2_700_000, alpha=0.85,
            decay=0.50, min_spend=900_000, max_spend=6_000_000,
            state_sensitivity=0.12, catch_up_rate=0.30, sweet_spot_frac=0.80,
        ),
        DepartmentParams(
            name="Marketing", S_max=22_000_000, K=3_000_000, alpha=1.10,
            decay=0.35, min_spend=1_200_000, max_spend=7_500_000,
            state_sensitivity=0.10, catch_up_rate=0.30, sweet_spot_frac=0.60,
        ),
    ],

    department_meta=[
        DepartmentMeta(
            name="R&D", color_key="dept_rd", description=(
            "R&D drives new flavours, formulation improvement, clinical hydration studies, and "
            "packaging innovation. Returns are DELAYED by one year — new products take time to "
            "develop and launch. R&D's strongest synergy is with Marketing: clinical evidence "
            "gives your brand ammunition to make credible health claims."
        ),
            background_description="R&D develops new flavour profiles, optimizes the electrolyte formulation, conducts clinical hydration studies, and innovates packaging formats for sustainability.",
        ),
        DepartmentMeta(
            name="Sales", color_key="dept_sales", description=(
            "Sales gets your product onto retail shelves, into e-commerce listings, and behind "
            "gym cooler doors. Returns are immediate but CAPPED by Operations — you can't fill "
            "orders you can't produce. In CPG, losing shelf space is fast and regaining it is slow."
        ),
            background_description="Sales manages retail shelf placement at grocery and convenience chains, e-commerce marketplace presence, gym and fitness channel partnerships, and corporate wellness accounts.",
        ),
        DepartmentMeta(
            name="Operations", color_key="dept_ops", description=(
            "Operations is the BOTTLENECK but looser than in pharma or automotive — beverage "
            "co-packing can scale more gradually. Still, if you can't produce enough cases to fill "
            "retailer orders, you lose listings."
        ),
            background_description="Operations manages co-packing relationships, ingredient sourcing, bottling line capacity, warehouse logistics, and nationwide distribution to retail partners.",
        ),
        DepartmentMeta(
            name="Marketing", color_key="dept_mktg", description=(
            "Marketing is the DOMINANT department in CPG. This is a brand game — consumer "
            "awareness and perception drive everything. The S-curve is steep: below threshold "
            "you're invisible, above it you build compounding brand equity. But over-spending "
            "wastes budget faster than in other industries."
        ),
            background_description="Marketing builds brand awareness and consumer demand through celebrity and influencer endorsements, grassroots event sampling, social media campaigns, and mass media advertising. In the beverage industry, brand recognition is the primary driver of purchase behaviour.",
        ),
    ],

    department_colors={"R&D": "#4A7B9D", "Sales": "#C27D3A", "Operations": "#3D7A5A", "Marketing": "#8B6BAE"},

    segments=[
        ConsumerSegment(key="fitness", label="Fitness & Sport",
            description="Gym-goers, runners, CrossFit enthusiasts. Buy at gyms, specialty retailers, and online. Driven by performance claims and athlete endorsements. Represent ~30% of the market.",
            market_weight=0.30),
        ConsumerSegment(key="wellness", label="Health & Wellness",
            description="Health-conscious consumers who want clean-label daily hydration. Buy at Whole Foods, natural grocery, and DTC. Driven by ingredients and credibility. Represent ~25% of the market.",
            market_weight=0.25),
        ConsumerSegment(key="mainstream", label="Mainstream Convenience",
            description="Impulse buyers at gas stations, convenience stores, and mass retail. Price-sensitive, taste-driven. The volume play. Represent ~25% of the market.",
            market_weight=0.25),
        ConsumerSegment(key="commercial", label="Offices, Gyms & Hospitality",
            description="Corporate wellness, gym chains, hotels, hospitals. Bulk recurring purchases. Driven by reliability and cost per unit. Represent ~20% of the market.",
            market_weight=0.20),
    ],

    segment_colors={"fitness": "#3D6B50", "wellness": "#4A7B9D", "mainstream": "#C27D3A", "commercial": "#8B6BAE"},

    sub_decisions={
        "R&D": DepartmentSubDecisions(
            dept_name="R&D", label="R&D Focus",
            tooltip="Choose your product development priority.",
            options={
                "flavour": SubDecisionOption(key="flavour", label="New Flavour Development",
                    description="Expand the product line with new taste profiles to capture broader consumer preferences.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Sales": 0.08, "Marketing": 0.05},
                    segment_multipliers={"fitness": 1.10, "wellness": 1.05, "mainstream": 1.35, "commercial": 0.90}),
                "clinical": SubDecisionOption(key="clinical", label="Clinical Hydration Studies",
                    description="Commission peer-reviewed research proving superior hydration absorption.",
                    smax_mult=1.20, k_mult=1.25, synergy={"Marketing": 0.12},
                    segment_multipliers={"fitness": 1.30, "wellness": 1.35, "mainstream": 0.80, "commercial": 1.10}),
                "costreduce": SubDecisionOption(key="costreduce", label="Formulation Cost Reduction",
                    description="Optimise ingredient blend to reduce cost per case while maintaining quality.",
                    smax_mult=0.90, k_mult=0.75, synergy={"Operations": 0.15},
                    segment_multipliers={"fitness": 0.85, "wellness": 0.75, "mainstream": 1.40, "commercial": 1.35}),
                "packaging": SubDecisionOption(key="packaging", label="Sustainable Packaging Innovation",
                    description="Develop eco-friendly packaging — recycled aluminium, plant-based bottles, concentrate formats.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Marketing": 0.10},
                    segment_multipliers={"fitness": 1.05, "wellness": 1.40, "mainstream": 0.90, "commercial": 1.15}),
            },
            default="clinical",
        ),
        "Sales": DepartmentSubDecisions(
            dept_name="Sales", label="Sales Channel Strategy",
            tooltip="Choose your primary distribution channel. Sales is CAPPED by Operations.",
            options={
                "massretail": SubDecisionOption(key="massretail", label="Mass Retail Push",
                    description="Focus on Walmart, Target, Kroger, Costco shelf placement.",
                    smax_mult=1.15, k_mult=1.10, synergy={"Operations": 0.08},
                    segment_multipliers={"fitness": 0.85, "wellness": 0.80, "mainstream": 1.50, "commercial": 0.90}),
                "dtc": SubDecisionOption(key="dtc", label="DTC & E-Commerce",
                    description="Amazon, brand website subscriptions, and online marketplace dominance.",
                    smax_mult=1.10, k_mult=1.05, synergy={"Marketing": 0.10},
                    segment_multipliers={"fitness": 1.20, "wellness": 1.30, "mainstream": 0.85, "commercial": 0.80}),
                "gymfitness": SubDecisionOption(key="gymfitness", label="Gym & Fitness Channel",
                    description="Exclusive placement at gym chains, CrossFit boxes, and fitness studios.",
                    smax_mult=1.05, k_mult=0.90, synergy={"Marketing": 0.06},
                    segment_multipliers={"fitness": 1.50, "wellness": 1.10, "mainstream": 0.70, "commercial": 1.15}),
                "convenience": SubDecisionOption(key="convenience", label="Convenience & Impulse",
                    description="7-Eleven, Circle K, gas stations — impulse cooler placement.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Operations": 0.05},
                    segment_multipliers={"fitness": 0.90, "wellness": 0.75, "mainstream": 1.45, "commercial": 0.85}),
            },
            default="massretail",
        ),
        "Operations": DepartmentSubDecisions(
            dept_name="Operations", label="Operations Priority",
            tooltip="Operations CAPS Sales — you can't fill shelves you can't stock.",
            options={
                "capacity": SubDecisionOption(key="capacity", label="Bottling Line Expansion",
                    description="Add co-packing capacity and second bottling line.",
                    smax_mult=1.20, k_mult=1.05, synergy={"Sales": 0.10},
                    segment_multipliers={"fitness": 1.10, "wellness": 1.00, "mainstream": 1.25, "commercial": 1.20}),
                "logistics": SubDecisionOption(key="logistics", label="National Distribution Build-Out",
                    description="Build cold chain, warehouse network, and last-mile delivery for all 50 states.",
                    smax_mult=1.10, k_mult=1.15, synergy={"Sales": 0.08},
                    segment_multipliers={"fitness": 1.05, "wellness": 1.10, "mainstream": 1.15, "commercial": 1.15}),
                "efficiency": SubDecisionOption(key="efficiency", label="Production Cost Efficiency",
                    description="Optimise bottling efficiency, reduce waste, negotiate better ingredient contracts.",
                    smax_mult=1.05, k_mult=0.85, synergy={"R&D": 0.05},
                    segment_multipliers={"fitness": 0.95, "wellness": 0.95, "mainstream": 1.20, "commercial": 1.25}),
                "seasonal": SubDecisionOption(key="seasonal", label="Peak Season Readiness",
                    description="Build inventory buffers and flexible capacity for summer demand surges.",
                    smax_mult=1.10, k_mult=1.00, synergy={"Sales": 0.06},
                    segment_multipliers={"fitness": 1.15, "wellness": 1.05, "mainstream": 1.20, "commercial": 1.05}),
            },
            default="capacity",
        ),
        "Marketing": DepartmentSubDecisions(
            dept_name="Marketing", label="Marketing Strategy",
            tooltip="Marketing is the dominant lever in CPG. The brand game drives everything.",
            options={
                "celebrity": SubDecisionOption(key="celebrity", label="Celebrity & Influencer Endorsement",
                    description="Sign a major athlete or celebrity as brand ambassador. High cost, massive reach, but risky.",
                    smax_mult=1.25, k_mult=1.20, synergy={"Sales": 0.12},
                    segment_multipliers={"fitness": 1.40, "wellness": 1.00, "mainstream": 1.35, "commercial": 0.85}),
                "grassroots": SubDecisionOption(key="grassroots", label="Grassroots & Sampling",
                    description="Event sampling, gym partnerships, marathon sponsorships, street teams.",
                    smax_mult=1.10, k_mult=0.85, synergy={"Sales": 0.08},
                    segment_multipliers={"fitness": 1.45, "wellness": 1.20, "mainstream": 0.90, "commercial": 1.10}),
                "science": SubDecisionOption(key="science", label="Science & Credibility",
                    description="Lead with clinical data, doctor endorsements, hospital partnerships.",
                    smax_mult=1.15, k_mult=1.10, synergy={"R&D": 0.10},
                    segment_multipliers={"fitness": 1.15, "wellness": 1.40, "mainstream": 0.80, "commercial": 1.20}),
                "mass_media": SubDecisionOption(key="mass_media", label="Mass Media & Digital",
                    description="TV ads, social media campaigns, broad reach awareness. Classic CPG playbook.",
                    smax_mult=1.15, k_mult=1.05, synergy={"Sales": 0.06},
                    segment_multipliers={"fitness": 0.95, "wellness": 0.90, "mainstream": 1.40, "commercial": 1.00}),
            },
            default="grassroots",
        ),
    },

    competitors=[
        CompetitorDef(name="TitanAde",
            industry="Global sports drink conglomerate",
            location="Chicago, Illinois (OmniCorp Beverages subsidiary)", founded="1965",
            description="The dominant US sports drink brand. Massive distribution, NFL/NBA partnerships, and decades of brand recognition. Outspends everyone on marketing.",
            display_label="Dominant Sports Drink Giant",
            base_revenue=80_000_000, growth_rate=0.03, margin=0.25,
            base_specs={"efficacy": 65, "taste": 72, "cost": 22},
            spec_growth_rates={"efficacy": 0.5, "taste": 1.0, "cost": 0.5},
            base_reach=1.5,  # Ubiquitous US retail presence, massive ad spend
        ),
        CompetitorDef(name="VitalDrip",
            industry="DTC wellness hydration brand",
            location="Los Angeles, California", founded="2018",
            description="Instagram-native electrolyte brand. Beautiful packaging, influencer-driven growth, strong DTC subscription model. Powder + RTD portfolio.",
            display_label="DTC Wellness Hydration Brand",
            base_revenue=35_000_000, growth_rate=0.18, margin=0.12,
            base_specs={"efficacy": 75, "taste": 78, "cost": 32},
            spec_growth_rates={"efficacy": 2.0, "taste": 2.0, "cost": 0.8},
            base_reach=0.9,  # Strong online/DTC, limited traditional retail
        ),
        CompetitorDef(name="PowerFlow Beverages",
            industry="Mass-market sports drink brand",
            location="Atlanta, Georgia (GlobalDrink Holdings subsidiary)", founded="1988",
            description="GlobalDrink Holdings' answer to TitanAde. Massive distribution through GlobalDrink's bottler network. Aggressive pricing, weak on innovation.",
            display_label="Beverage Giant's Sports Brand",
            base_revenue=55_000_000, growth_rate=0.04, margin=0.22,
            base_specs={"efficacy": 60, "taste": 70, "cost": 20},
            spec_growth_rates={"efficacy": 0.3, "taste": 0.8, "cost": 0.3},
            base_reach=1.35,  # Extensive beverage distribution network
        ),
        CompetitorDef(name="ElectroPure",
            industry="Clean-label electrolyte startup",
            location="Boulder, Colorado", founded="2020",
            description="Organic, clean-label electrolyte brand. Strong at Whole Foods and natural grocery. Science-focused positioning. Your closest competitor.",
            display_label="Clean-Label Startup Rival",
            base_revenue=15_000_000, growth_rate=0.22, margin=0.08,
            base_specs={"efficacy": 80, "taste": 74, "cost": 34},
            spec_growth_rates={"efficacy": 3.0, "taste": 2.5, "cost": 0.5},
            base_reach=0.7,  # Niche health channels, growing DTC
        ),
    ],

    competitor_labels={
        "TitanAde": "Dominant Sports Drink Giant",
        "VitalDrip": "DTC Wellness Hydration Brand",
        "PowerFlow Beverages": "Beverage Giant's Sports Brand",
        "ElectroPure": "Clean-Label Startup Rival",
    },

    product_specs=[
        ProductSpec(key="efficacy", label="Hydration Efficacy", unit="score", base_value=72, higher_is_better=True),
        ProductSpec(key="taste", label="Taste & Appeal", unit="score", base_value=75, higher_is_better=True),
        ProductSpec(key="cost", label="Cost Per Case", unit="$/case", base_value=10.0, higher_is_better=False, display_format=".1f"),
    ],

    spec_evolution_rules=[
        SpecEvolutionRule(spec_key="efficacy", dept_name="R&D",
            base_growth=0.8, spend_sensitivity=4.0, dept_budget_ref=3_500_000,
            sub_decision_bonuses={"clinical": 3.5, "flavour": 0.5, "costreduce": -1.0, "packaging": 0.5},
            min_value=55, max_value=95),
        SpecEvolutionRule(spec_key="taste", dept_name="R&D",
            base_growth=1.0, spend_sensitivity=4.0, dept_budget_ref=3_500_000,
            sub_decision_bonuses={"flavour": 4.0, "clinical": 0.5, "costreduce": -1.5, "packaging": 1.0},
            min_value=55, max_value=95),
        SpecEvolutionRule(spec_key="cost", dept_name="R&D",
            base_growth=0.1, spend_sensitivity=-0.5, dept_budget_ref=3_500_000,
            sub_decision_bonuses={"costreduce": -1.5, "clinical": 0.3, "flavour": 0.2, "packaging": 0.4},
            min_value=5.0, max_value=18.0),
    ],

    segment_spec_preferences={
        "fitness": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.50, ideal_value=85, tolerance=15),
            SegmentSpecPreference(spec_key="taste", weight=0.30, ideal_value=80, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.20, ideal_value=10, tolerance=6),
        ],
        "wellness": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.40, ideal_value=85, tolerance=12),
            SegmentSpecPreference(spec_key="taste", weight=0.35, ideal_value=82, tolerance=12),
            SegmentSpecPreference(spec_key="cost", weight=0.25, ideal_value=12, tolerance=6),
        ],
        "mainstream": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.15, ideal_value=70, tolerance=20),
            SegmentSpecPreference(spec_key="taste", weight=0.45, ideal_value=85, tolerance=12),
            SegmentSpecPreference(spec_key="cost", weight=0.40, ideal_value=8, tolerance=5),
        ],
        "commercial": [
            SegmentSpecPreference(spec_key="efficacy", weight=0.30, ideal_value=75, tolerance=18),
            SegmentSpecPreference(spec_key="taste", weight=0.25, ideal_value=75, tolerance=15),
            SegmentSpecPreference(spec_key="cost", weight=0.45, ideal_value=8, tolerance=5),
        ],
    },

    performance_index_name="HVI",
    performance_index_full="HydraVive Performance Index",
    market_label="isotonic hydration market",

    # CPG-tuned mechanics
    bottleneck_cap_dept_idx=2,       # Operations
    bottleneck_capped_dept_idx=1,    # Sales
    bottleneck_cap_fraction=0.90,    # Looser than EV (0.85) — co-packing scales easier
    delayed_return_dept_idx=0,       # R&D
    brand_equity_depts=[(3, 1.0), (0, 0.3)],  # Marketing IS the brand in CPG, R&D minor

    general_news_pool=GENERAL_NEWS_POOL,
    dept_news_pool=DEPT_NEWS_POOL,
    competitor_news_pool=COMPETITOR_NEWS_POOL,

    storyboard=StoryboardContent(
        world_headline="The year is 2025. America is thirsty — and everyone from startups to beverage empires wants to quench it.",
        world_body=(
            "The US isotonic drink market has crossed $10 billion and it is accelerating. Record-breaking "
            "heat waves are rewriting consumer habits, gym culture has gone mainstream, and wellness "
            "influencers have turned electrolyte drinks into a lifestyle statement. But the battlefield "
            "is brutal. OmniCorp Beverages and GlobalDrink Holdings control supermarket shelf space with "
            "iron fists, Instagram-native DTC brands are multiplying weekly, and the average American now "
            "sees dozens of hydration ads per day. Shelf velocity — how fast your product sells per linear "
            "foot — is the metric that decides whether you survive or get delisted. The brands that crack "
            "the code of authentic health credibility, mainstream taste appeal, and relentless distribution "
            "execution will own the next decade. The rest will be footnotes."
        ),
        market_body=(
            "The US isotonic hydration market is growing at 12% annually. Four consumer segments "
            "drive demand — each with different purchase behaviour and brand expectations."
        ),
        market_kpis=[
            ("Market Size", "$10B+ annually", "dept_rd"),
            ("Growth Rate", "12% CAGR", "accent"),
            ("Segments", "4 consumer groups", "dept_mktg"),
        ],
        segments_intro="Winning in hydration means matching your brand to the right consumer in the right channel.",
        company_subtitle="Founded 2022  ·  Austin, TX  ·  85 employees  ·  Series A funded",
        company_body=(
            "HydraVive started three years ago in a commercial kitchen in East Austin. The founder — a "
            "former sports nutritionist who worked with Olympic track athletes — was frustrated that every "
            "electrolyte drink on the market was either packed with sugar or tasted like medicine. She "
            "formulated a clean-label isotonic drink with osmolality-optimized absorption and a gentle, "
            "non-sweet flavour profile inspired by Japanese hydration science. The first batch sold out "
            "at a local CrossFit box in two hours. Word spread through Austin's fitness community, then "
            "to Houston, then Dallas. Now HydraVive has cult status across Texas and a growing DTC "
            "following on the coasts. A $8M Series A just closed. The problem: OmniCorp's sales team "
            "has started asking grocery buyers about you. The clock is ticking."
        ),
        product_subtitle="Isotonic Electrolyte RTD — Everyday hydration, scientifically formulated",
        product_body=(
            "HydraVive is a ready-to-drink isotonic electrolyte beverage in 500ml aluminium cans. "
            "Gentle flavour profile (not aggressively sweet), osmolality-optimised for rapid "
            "absorption, and clean label with no artificial ingredients. Sold by the case "
            "(24 × 500ml). Year 1 production capacity: 800,000 cases."
        ),
        product_kpis=[
            ("Case Price", "$28/case", "dept_rd"),
            ("Efficacy Score", "72/100", "accent"),
            ("Taste Score", "75/100", "dept_sales"),
            ("Yr 1 Capacity", "800K cases", "dept_ops"),
        ],
        role_body=(
            "Allocate HydraVive's budget across R&D, Sales, Operations, and Marketing over 5 years. "
            "This is a brand game — Marketing is the dominant lever. Celebrity endorsements can "
            "catapult awareness but carry risk. Shelf space is earned, not given."
        ),
        objective_body=(
            "Your HVI score (0–1000+) is based on risk-adjusted profitability (50%) and "
            "isotonic hydration market share (50%)."
        ),
        departments_intro="In CPG, Marketing drives everything. But you still need shelf space (Sales) and product to fill it (Operations).",
        competitors_intro="The big beverage companies want this market too. These are your rivals.",
        ready_headline="Your journey starts now — Austin loves you. Can America?",
        ready_body=(
            "You have a product people love, a brand that is growing, and a window that is closing. "
            "The grocery buyers are watching your velocity numbers. The influencers are waiting for "
            "your pitch. And somewhere in a Chicago boardroom, a beverage executive is deciding whether "
            "to launch a copycat. You have five years. Make them count."
        ),
    ),

    briefing=BriefingContent(
        world_body=(
            "The US isotonic market has crossed $10B, growing at 12% annually. Record heat waves, "
            "mainstream fitness culture, and wellness influencers drive demand. OmniCorp and GlobalDrink "
            "control shelf space while DTC startups flood Instagram. Shelf velocity decides who survives."
        ),
        market_body=(
            "Four segments: fitness enthusiasts, health/wellness consumers, mainstream convenience "
            "buyers, and commercial/institutional. Each needs a different approach."
        ),
        company_body=(
            "HydraVive is an Austin-based cult favourite — a clean-label isotonic RTD with a loyal Texas "
            "following and growing DTC presence. Founded by a former Olympic sports nutritionist. Series A "
            "funded, 85 employees. Proven product-market fit; needs national distribution before the "
            "beverage giants notice."
        ),
        product_body=(
            "Isotonic electrolyte RTD in 500ml aluminium cans. $28/case. Clinically formulated, "
            "gentle flavour. Year 1 capacity: 800K cases."
        ),
        product_kpis=[
            ("Case Price", "$28/case", "dept_rd"),
            ("Efficacy Score", "72/100", "accent"),
            ("Taste Score", "75/100", "dept_sales"),
            ("Yr 1 Capacity", "800K cases", "dept_ops"),
        ],
        role_body=(
            "Allocate across 4 departments. Marketing is king in CPG — celebrity endorsements "
            "and brand building are your biggest levers."
        ),
        objective_body="HVI based on profitability (50%) and market share (50%).",
    ),
    objective_text={},
)


register_scenario("us", "hydration", US_HYDRATION)
