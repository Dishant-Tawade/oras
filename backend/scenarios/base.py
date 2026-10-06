"""Scenario definition dataclasses.

Each (country, industry) pair provides a ScenarioDefinition that specifies the simulation world;
the engine, scoring and UI read from it. To add a scenario, build one and call register_scenario().
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


# Locale / Currency

@dataclass
class LocaleConfig:
    """Currency and number formatting for a country."""
    country_code: str                # "US", "CA", "IN", "UK"
    country_name: str                # "United States", "Canada", etc.
    currency_symbol: str             # "$", "£", "₹"
    currency_code: str               # "USD", "CAD", "INR", "GBP"
    currency_prefix: bool = True     # True = "$60M", False = "60M₹" (not used yet)
    # Large-number formatting — for budgets, revenues, competitor figures
    # e.g. "$60M", "₹800Cr"
    large_number_suffix: str = "M"   # "M" for millions, "Cr" for crores
    large_number_divisor: float = 1_000_000  # divide raw value by this then append suffix
    # Small-number formatting — for department-level allocations on sliders
    # e.g. "$3,000K", "₹4,000L"
    small_number_suffix: str = "K"   # "K" for thousands, "L" for lakhs
    small_number_divisor: float = 1_000  # divide raw value by this then append suffix
    # Slider step size — granularity of budget allocation slider
    # e.g. $1,000 steps for US, ₹1,00,000 steps for India
    slider_step: int = 1_000


# Company & Product

@dataclass
class CompanyConfig:
    """The player's company identity."""
    name: str                        # "Voltex Motors"
    product_name: str                # "Voltex Xeno EV Sedan"
    tagline: str                     # "Growth-stage American EV manufacturer"
    location: str                    # "Austin, Texas"
    role_title: str                  # "VP of Finance & Strategy"
    founding_year: str = "2020"
    industry_label: str = ""         # "Electric Vehicles", "Pharmaceuticals", "Fashion"

    # Product-specific display details
    unit_price: float = 42_000.0
    unit_price_label: str = "MSRP"   # or "Wholesale Price" etc.
    unit_cost: float = 28_000.0
    year1_capacity: int = 18_000
    capacity_unit: str = "units"     # "units", "doses", "pieces"


# Product specs are visible metrics that evolve each year with player decisions; each scenario defines its own
# # set (e.g. EV: range, battery, 0-60, tech score).

@dataclass
class ProductSpec:
    """A single measurable product attribute."""
    key: str                         # e.g. "range", "battery", "accel"
    label: str                       # "Range (EPA)"
    unit: str                        # "mi", "kWh", "sec", "/100"
    base_value: float                # Starting value in Year 0
    higher_is_better: bool = True    # False for things like "0-60 time" or "time to market"
    display_format: str = ".0f"      # Python format spec for display


@dataclass
class SpecEvolutionRule:
    """How a product spec changes based on department spend and sub-decisions.

    The spec evolves each year by:
      delta = base_growth
            + (dept_spend / dept_budget_ref) * spend_sensitivity
            + sub_decision_bonus[chosen_option]  (if this year's sub-decision matches)

    The final value is clamped between min_value and max_value.
    """
    spec_key: str                    # Which ProductSpec this rule targets
    dept_name: str                   # Which department drives this spec ("R&D", etc.)
    base_growth: float               # Annual growth with zero spend (market catch-up or decay)
    spend_sensitivity: float         # How much spend accelerates growth
    dept_budget_ref: float           # Reference spend level (e.g. 15M) for normalisation
    sub_decision_bonuses: Dict[str, float] = field(default_factory=dict)  # {option_key: bonus}
    min_value: float = 0.0           # Floor
    max_value: float = float('inf')  # Ceiling


@dataclass
class SegmentSpecPreference:
    """How much a consumer segment values each product spec.

    Weights should sum to ~1.0 across all specs for a segment.
    ideal_value is the value at which the segment is maximally satisfied.
    tolerance controls how quickly satisfaction drops off from ideal.
    """
    spec_key: str
    weight: float                    # Importance weight (0 to 1)
    ideal_value: float               # The "perfect" value for this segment
    tolerance: float                 # How forgiving the segment is (higher = more forgiving)

@dataclass
class ConsumerSegment:
    key: str                         # "budget", "tech", etc.
    label: str                       # "Budget-Conscious Families"
    description: str
    market_weight: float             # 0.35 = 35% of addressable market


# Department Sub-Decision Option

@dataclass
class SubDecisionOption:
    key: str                         # "range", "software", etc.
    label: str                       # "Extended Range & Battery Life"
    description: str
    smax_mult: float = 1.0
    k_mult: float = 1.0
    synergy: Dict[str, float] = field(default_factory=dict)       # {dept_name: smax_bonus}
    segment_multipliers: Dict[str, float] = field(default_factory=dict)  # {seg_key: mult}


@dataclass
class DepartmentSubDecisions:
    dept_name: str
    label: str                       # "R&D Focus"
    tooltip: str
    options: Dict[str, SubDecisionOption] = field(default_factory=dict)
    default: str = ""


# Department Meta (display descriptions)

@dataclass
class DepartmentMeta:
    name: str                        # Must match DepartmentConfig.name
    color_key: str                   # "dept_rd", "dept_sales", etc.
    description: str                 # Mechanics text for objective tab
    background_description: str = "" # Industry context for background tab (no mechanics)


# Competitor AI Personality

@dataclass
class CompetitorPersonality:
    """Defines how a competitor 'plays' the game — their budget, allocation
    tendencies, sub-decision preferences, and adaptiveness.

    When present on a CompetitorDef, the competitor is simulated as an NPC
    player using the same spec evolution and reach mechanics as the human
    player, rather than using hardcoded spec growth rates.
    """
    # Budget
    total_budget: float                          # e.g. 90_000_000 for Apex

    # Base allocation weights (must sum to 1.0)
    # Keys must match department names from the scenario.
    base_allocation_weights: Dict[str, float]    # {"R&D": 0.30, "Sales": 0.25, ...}

    # Per department: (option_key, weight) pairs. Weights are relative and normalised at runtime.
    sub_decision_prefs: Dict[str, List[Tuple[str, float]]]

    # 0.0 = stubborn/thematic, 1.0 = fully adaptive: how far the competitor shifts from its base personality.
    strategic_iq: float = 0.5

    # Noise magnitude (fraction of base allocation that can shift randomly)
    noise_factor: float = 0.20                   # ±20% default

    # Brand equity accumulated before the game; feeds the same brand_boost formula the player uses.
    starting_brand_equity: float = 0.0

    # Display hint (shown in briefing/storyboard)
    spending_tendency: str = ""                   # e.g. "Heavy R&D and Operations investor"


# Competitor

@dataclass
class CompetitorDef:
    name: str
    industry: str
    location: str
    founded: str
    description: str
    display_label: str               # "Silicon Valley EV Disruptor"
    base_revenue: float              # Starting annual revenue
    growth_rate: float               # Annual growth rate
    margin: float                    # Profit margin

    # When set, the competitor is simulated as an NPC player: specs evolve from its allocations and
    # # sub-decisions, and reach from segment multipliers plus brand equity.
    personality: Optional[CompetitorPersonality] = None

    # Baseline specs before any investment takes effect.
    starting_specs: Dict[str, float] = field(default_factory=dict)

    # Legacy fields (used when personality is None — backward compat)
    base_specs: Dict[str, float] = field(default_factory=dict)
    spec_growth_rates: Dict[str, float] = field(default_factory=dict)
    base_reach: float = 1.0


# News pool entries are tuples; see the generation functions in simulator.py.

# General news: (headline, detail, rev_mult_range, prof_impact_range, sentiment)
GeneralNewsTemplate = Tuple[str, str, Tuple[float, float], Tuple[float, float], str]

# Department news: (headline, detail, dept_name, k_mult, smax_mult, sentiment)
DeptNewsTemplate = Tuple[str, str, str, float, float, str]

# Competitor news: same format as general news (used in generate_news_events)
CompetitorNewsTemplate = Tuple[str, str, Tuple[float, float], Tuple[float, float], str]


# Storyboard prose for each step; the frontend handles layout and navigation.

@dataclass
class StoryboardContent:
    """Full content for all 10 storyboard steps.
    Each field is the prose text for that step.
    Steps that use dynamic data (segments, departments, competitors)
    are rendered by the UI using scenario data — the text fields
    here provide the introductory prose for those steps.
    """
    # Step 0: The World
    world_headline: str = ""         # Large opening line
    world_body: str = ""             # Paragraph text

    # Step 1: The Market
    market_body: str = ""            # Paragraph about the market
    market_kpis: List = field(default_factory=list)  # list of (label, value, color_key) tuples

    # Step 2: Consumer Segments
    segments_intro: str = ""         # Intro text before the segment cards

    # Step 3: Your Company
    company_subtitle: str = ""       # Line under company name (e.g. "Founded 2018 · Austin, TX")
    company_body: str = ""           # Paragraph about the company

    # Step 4: The Product
    product_subtitle: str = ""       # Tagline (e.g. "All-Electric Sedan — The make-or-break launch")
    product_body: str = ""           # Paragraph about the product
    product_kpis: List = field(default_factory=list)  # list of (label, value, color_key)

    # Step 5: Your Role
    role_body: str = ""              # Paragraph about the role (beyond the auto-generated dept list)

    # Step 6: The Objective
    objective_body: str = ""         # Paragraph about the scoring objective

    # Step 7: Departments
    departments_intro: str = ""      # Intro text before department cards

    # Step 8: Competitors
    competitors_intro: str = ""      # Intro text before competitor cards

    # Step 9: Ready
    ready_headline: str = ""         # Big text
    ready_body: str = ""             # Final paragraph before "Begin Simulation" button

    # Optional prose for the "Your Mandate" and "Practice Round" slides. When blank, the frontend uses
    # # scenario-neutral defaults derived from the budget and number of periods.
    mandate_body: str = ""    # Frames the core loop: annual budget × N years × locking
    practice_body: str = ""   # Short instructions for the Practice Round sandbox


@dataclass
class BriefingContent:
    """Full prose content for every section of the briefing tab."""
    # Simulation World section
    world_body: str = ""             # "The year is 2025. The EV industry..."
    market_body: str = ""            # "The global passenger EV market..."

    # Your Company section
    company_body: str = ""           # Paragraph about the company background

    # The Product section
    product_body: str = ""           # Paragraph about the product
    product_kpis: List = field(default_factory=list)  # (label, value, color_key)

    # Your Role section
    role_body: str = ""              # Paragraph about responsibilities

    # Main Objective section
    objective_body: str = ""         # Paragraph about VPI/scoring


# Financial Parameters

@dataclass
class FinancialConfig:
    """All the numbers that define the simulation's financial world."""
    total_budget: float = 60_000_000
    fixed_costs: float = 95_000_000
    base_revenue: float = 40_000_000      # Year 0 context
    profit_reinvestment_rate: float = 0.03
    inflation_min: float = 0.06
    inflation_max: float = 0.15
    underuse_threshold: float = 0.15
    underuse_penalty_rate: float = 2.5
    max_change_rate: float = 0.30
    demand_noise_std: float = 0.08
    scenario_drift_std: float = 0.03
    risk_penalty_lambda: float = 1.5
    num_periods: int = 5
    num_eval_scenarios: int = 30
    state_decay: float = 0.5

    # VPI normalization bounds — these MUST be tuned per scenario
    vpi_ras_floor: float = -65_000_000
    vpi_ras_ceiling: float = 260_000_000
    vpi_share_floor: float = 8.0
    vpi_share_ceiling: float = 26.0

    # Market share model: competitor revenue baseline for presence scaling
    # (competitors at this revenue have presence ~1.0)
    competitor_presence_baseline: float = 400_000_000


# Re-exported from simulator; importing it there at module level would be circular.

@dataclass
class DepartmentParams:
    """Simulation parameters for one department.
    This mirrors simulator.DepartmentConfig exactly so scenarios can be
    defined without importing from simulator.py."""
    name: str
    S_max: float
    K: float
    alpha: float
    decay: float
    min_spend: float
    max_spend: float
    state_sensitivity: float = 0.1
    catch_up_rate: float = 0.3
    sweet_spot_frac: float = 0.75


# Timer Config

@dataclass
class TimerConfig:
    course_seconds: int = 300       # 5 minutes
    competition_seconds: int = 1800  # 30 minutes



@dataclass
class ScenarioDefinition:
    """
    Complete definition of a simulation scenario.

    A (country, industry) pair maps to exactly one of these.
    Every piece of content the platform needs — from department parameters
    to storyboard prose — lives here.
    """

    # Identity
    scenario_id: str                 # "us_ev", "india_pharma", etc.
    scenario_label: str              # "United States — Electric Vehicles"

    # Locale & Currency
    locale: LocaleConfig = field(default_factory=lambda: LocaleConfig(
        country_code="US", country_name="United States",
        currency_symbol="$", currency_code="USD",
    ))

    # Company
    company: CompanyConfig = field(default_factory=CompanyConfig)

    # Financial Parameters
    financials: FinancialConfig = field(default_factory=FinancialConfig)

    # Timer
    timer: TimerConfig = field(default_factory=TimerConfig)

    # Departments (simulation parameters)
    departments: List[DepartmentParams] = field(default_factory=list)

    # Department display metadata
    department_meta: List[DepartmentMeta] = field(default_factory=list)

    # Department colors: {dept_name: hex_color}
    department_colors: Dict[str, str] = field(default_factory=dict)

    # Consumer Segments
    segments: List[ConsumerSegment] = field(default_factory=list)

    # Segment colors: {seg_key: hex_color}
    segment_colors: Dict[str, str] = field(default_factory=dict)

    # Sub-Decisions per department
    sub_decisions: Dict[str, DepartmentSubDecisions] = field(default_factory=dict)

    # Competitors
    competitors: List[CompetitorDef] = field(default_factory=list)

    # Competitor display labels: {name: label}
    competitor_labels: Dict[str, str] = field(default_factory=dict)

    # Product specs & evolution
    # The visible product attributes that evolve each year
    product_specs: List[ProductSpec] = field(default_factory=list)
    # Rules for how player specs evolve based on spend + sub-decisions
    spec_evolution_rules: List[SpecEvolutionRule] = field(default_factory=list)
    # How each consumer segment values each spec — dict of {segment_key: [SegmentSpecPreference]}
    segment_spec_preferences: Dict[str, List[SegmentSpecPreference]] = field(default_factory=dict)

    # News pools
    general_news_pool: List[GeneralNewsTemplate] = field(default_factory=list)
    dept_news_pool: List[DeptNewsTemplate] = field(default_factory=list)
    competitor_news_pool: List[CompetitorNewsTemplate] = field(default_factory=list)

    # Storyboard content (all 10 steps)
    storyboard: StoryboardContent = field(default_factory=StoryboardContent)

    # Briefing content (all sections)
    briefing: BriefingContent = field(default_factory=BriefingContent)

    # Objective / scoring description text
    objective_text: Dict[str, str] = field(default_factory=dict)

    # Performance index naming
    performance_index_name: str = "VPI"          # "VPI", "PPI", "FPI"
    performance_index_full: str = "Voltex Performance Index"

    # Market label
    market_label: str = "EV market"              # "EV market", "pharmaceutical market", etc.

    # Grade scale (same structure for all, but thresholds could vary)
    grade_thresholds: Dict[str, int] = field(default_factory=lambda: {
        'S': 850, 'A': 700, 'B': 550, 'C': 400, 'D': 250,
    })

    # Index-based: which department caps which. Default: Operations (2) caps Sales (1) at 85%.
    bottleneck_cap_dept_idx: int = 2       # Operations
    bottleneck_capped_dept_idx: int = 1    # Sales
    bottleneck_cap_fraction: float = 0.85
    # When the cap department (Operations) is funded beyond sales_return * overcap_ratio, its return decays
    # # quadratically. Default ratio 1.5.
    bottleneck_overcap_ratio: float = 1.5
    # Minimum multiplier the penalty can reduce ops return to (floor = 0.6)
    bottleneck_overcap_floor: float = 0.6

    # Which department has delayed returns (index-based).
    # Default: R&D (idx 0) returns delayed by 1 year
    delayed_return_dept_idx: int = 0

    # Brand equity dept indices: which depts contribute to brand score
    # Default: Marketing (idx 3) at 100% + R&D (idx 0) at 50%
    brand_equity_depts: List[Tuple[int, float]] = field(
        default_factory=lambda: [(3, 1.0), (0, 0.5)]
    )

    # Helper methods

    def dept_names(self) -> List[str]:
        """Return ordered list of department names."""
        return [d.name for d in self.departments]

    def segment_keys(self) -> List[str]:
        """Return ordered list of segment keys."""
        return [s.key for s in self.segments]

    def segment_weights(self) -> List[float]:
        """Return ordered list of segment market weights."""
        return [s.market_weight for s in self.segments]

    def segments_dict(self) -> Dict[str, dict]:
        """Return segments in the legacy dict format for backward compat."""
        return {
            s.key: {
                "label": s.label,
                "description": s.description,
                "market_weight": s.market_weight,
            }
            for s in self.segments
        }

    def sub_decisions_dict(self) -> Dict[str, dict]:
        """Return sub-decisions in the legacy dict format for backward compat."""
        result = {}
        for dept_name, dsd in self.sub_decisions.items():
            opts = {}
            for key, opt in dsd.options.items():
                opts[key] = {
                    "label": opt.label,
                    "description": opt.description,
                    "smax_mult": opt.smax_mult,
                    "k_mult": opt.k_mult,
                    "synergy": dict(opt.synergy),
                    "segment_multipliers": dict(opt.segment_multipliers),
                }
            result[dept_name] = {
                "label": dsd.label,
                "tooltip": dsd.tooltip,
                "options": opts,
                "default": dsd.default,
            }
        return result

    def dept_descriptions_dict(self) -> Dict[str, str]:
        """Return {dept_name: description} for objective tab (includes mechanics)."""
        return {m.name: m.description for m in self.department_meta}

    def dept_background_dict(self) -> Dict[str, str]:
        """Return {dept_name: background_description} for background tab (industry context only).
        Falls back to description if background_description is empty."""
        return {m.name: (m.background_description or m.description)
                for m in self.department_meta}

    def competitor_defs_list(self) -> List[dict]:
        """Return competitor definitions as dicts for the generator."""
        return [
            {
                "name": c.name,
                "industry": c.industry,
                "location": c.location,
                "founded": c.founded,
                "description": c.description,
                "base_revenue": c.base_revenue,
                "growth_rate": c.growth_rate,
                "margin": c.margin,
                "base_specs": c.base_specs,
                "spec_growth_rates": c.spec_growth_rates,
                "base_reach": c.base_reach,
                "personality": c.personality,
                "starting_specs": c.starting_specs,
            }
            for c in self.competitors
        ]

    def format_currency(self, value: float, short: bool = True) -> str:
        """Format a monetary value using the scenario's locale.

        short=True:  $60,000K  or  ₹500Cr
        short=False: $60,000,000  or  ₹5,000,000,000
        """
        loc = self.locale
        if short:
            scaled = round(value / loc.large_number_divisor, 1)
            # Drop the decimal if it's .0
            if scaled == int(scaled):
                scaled = int(scaled)
            formatted = f"{scaled:,}{loc.large_number_suffix}"
        else:
            formatted = f"{value:,.0f}"

        if loc.currency_prefix:
            return f"{loc.currency_symbol}{formatted}"
        else:
            return f"{formatted}{loc.currency_symbol}"

    def format_currency_k(self, value: float) -> str:
        """Format in locale-appropriate small units: $60,000K or ₹4,000L"""
        loc = self.locale
        scaled = round(value / loc.small_number_divisor)
        suffix = loc.small_number_suffix
        if scaled < 0:
            s = f"-{loc.currency_symbol}{abs(scaled):,}{suffix}" if loc.currency_prefix \
                else f"-{abs(scaled):,}{suffix}{loc.currency_symbol}"
        else:
            s = f"{loc.currency_symbol}{scaled:,}{suffix}" if loc.currency_prefix \
                else f"{scaled:,}{suffix}{loc.currency_symbol}"
        return s
