"""
Instant print-price calculation engine.
Pure functions, no DB/IO, fully unit-testable. All amounts in paise (INR *100)
to avoid float rounding issues; divide by 100 for display.
"""
from app.modules.documents.models import BindingType, ColorMode, PrintDocument, SideMode

# Base rate per page, in paise
RATE_BW_PAGE = 150       # ₹1.50
RATE_COLOR_PAGE = 800    # ₹8.00

PAPER_SIZE_MULTIPLIER = {"A4": 1.0, "A3": 1.8, "LETTER": 1.0, "LEGAL": 1.15}
GSM_SURCHARGE_PER_PAGE = {70: 0, 75: 0, 80: 20, 100: 60, 120: 120}  # paise added per page

BINDING_COST = {BindingType.NONE: 0, BindingType.STAPLE: 500, BindingType.SPIRAL: 3000}
LAMINATION_COST_PER_PAGE = 1000
COVER_PAGE_COST = 2000
PREMIUM_PAPER_SURCHARGE_PER_PAGE = 300
EXPRESS_DELIVERY_SURCHARGE_PERCENT = 25
DOUBLE_SIDE_DISCOUNT_PERCENT = 10  # printing double-sided is cheaper per page overall


def calculate_price(doc: PrintDocument) -> int:
    """Returns total price in paise for the given document + settings."""
    per_page_rate = RATE_COLOR_PAGE if doc.color_mode == ColorMode.COLOR else RATE_BW_PAGE
    per_page_rate *= PAPER_SIZE_MULTIPLIER.get(doc.paper_size.upper(), 1.0)
    per_page_rate += GSM_SURCHARGE_PER_PAGE.get(doc.paper_gsm, 0)

    if doc.premium_paper:
        per_page_rate += PREMIUM_PAPER_SURCHARGE_PER_PAGE

    printing_units = doc.page_count * doc.copies
    subtotal = per_page_rate * printing_units

    if doc.side_mode == SideMode.DOUBLE:
        subtotal *= (1 - DOUBLE_SIDE_DISCOUNT_PERCENT / 100)

    if doc.lamination:
        subtotal += LAMINATION_COST_PER_PAGE * printing_units

    subtotal += BINDING_COST.get(doc.binding, 0) * doc.copies

    if doc.cover_page:
        subtotal += COVER_PAGE_COST * doc.copies

    if doc.express_delivery:
        subtotal *= (1 + EXPRESS_DELIVERY_SURCHARGE_PERCENT / 100)

    return round(subtotal)
