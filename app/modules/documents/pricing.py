"""
Instant print-price calculation engine.
Pure function, no DB/IO, fully unit-testable — DB-backed rate overrides are
resolved by the caller (see app/modules/admin/pricing_config.py) and passed
in as a `PricingRates` value, so this module has zero dependency on the DB
and existing tests that call `calculate_price(doc)` with no rates argument
keep working unchanged (they get the hardcoded defaults below).

Scope note: paper-size multiplier and GSM surcharge tables stay code-defined
(they're structurally a lookup table, not a single scalar admin knob) — see
PricingRates below for exactly which rates ARE admin-editable via
PlatformSetting. Glossy/matte finish, "heavy ink" surcharge, hard-binding,
GST, and bulk-quantity discounts are not yet modeled as document-print
fields at all (only spiral/staple/none binding and premium_paper exist
today) — extending those requires new PrintDocument fields, which is a
separate, larger schema change flagged here rather than silently faked.
"""
from dataclasses import dataclass, field

from app.modules.documents.models import BindingType, ColorMode, PrintDocument, SideMode


@dataclass(frozen=True)
class PricingRates:
    """All amounts in paise (INR * 100). Scalar fields here are exactly the
    knobs exposed as admin-editable PlatformSetting rows — see pricing_config.py."""

    rate_bw_page: int = 150            # ₹1.50
    rate_color_page: int = 800         # ₹8.00
    binding_cost_staple: int = 500
    binding_cost_spiral: int = 3000
    lamination_cost_per_page: int = 1000
    cover_page_cost: int = 2000
    premium_paper_surcharge_per_page: int = 300
    express_delivery_surcharge_percent: float = 25
    double_side_discount_percent: float = 10

    # Structural lookup tables — not exposed as single admin-editable scalars.
    paper_size_multiplier: dict = field(
        default_factory=lambda: {"A4": 1.0, "A3": 1.8, "LETTER": 1.0, "LEGAL": 1.15}
    )
    gsm_surcharge_per_page: dict = field(
        default_factory=lambda: {70: 0, 75: 0, 80: 20, 100: 60, 120: 120}
    )

    def binding_cost(self, binding: BindingType) -> int:
        return {
            BindingType.NONE: 0,
            BindingType.STAPLE: self.binding_cost_staple,
            BindingType.SPIRAL: self.binding_cost_spiral,
        }.get(binding, 0)


DEFAULT_RATES = PricingRates()


def calculate_price(doc: PrintDocument, rates: PricingRates = DEFAULT_RATES) -> int:
    """Returns total price in paise for the given document + settings."""
    per_page_rate = rates.rate_color_page if doc.color_mode == ColorMode.COLOR else rates.rate_bw_page
    per_page_rate *= rates.paper_size_multiplier.get(doc.paper_size.upper(), 1.0)
    per_page_rate += rates.gsm_surcharge_per_page.get(doc.paper_gsm, 0)

    if doc.premium_paper:
        per_page_rate += rates.premium_paper_surcharge_per_page

    printing_units = doc.page_count * doc.copies
    subtotal = per_page_rate * printing_units

    if doc.side_mode == SideMode.DOUBLE:
        subtotal *= (1 - rates.double_side_discount_percent / 100)

    if doc.lamination:
        subtotal += rates.lamination_cost_per_page * printing_units

    subtotal += rates.binding_cost(doc.binding) * doc.copies

    if doc.cover_page:
        subtotal += rates.cover_page_cost * doc.copies

    if doc.express_delivery:
        subtotal *= (1 + rates.express_delivery_surcharge_percent / 100)

    return round(subtotal)
