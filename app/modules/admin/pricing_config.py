"""
Bridges the admin-editable PlatformSetting key-value store to the pricing
engine's PricingRates. Each scalar field on PricingRates gets a
"pricing.<field_name>" PlatformSetting row when the admin edits it; anything
not explicitly set falls back to PricingRates' hardcoded default — so the
platform works correctly out of the box with zero admin configuration, and
every value becomes editable without a code change/deploy the moment an
admin touches it.
"""
from dataclasses import fields
from sqlalchemy.orm import Session

from app.modules.admin.repository import PlatformSettingRepository
from app.modules.documents.pricing import DEFAULT_RATES, PricingRates

PRICING_KEY_PREFIX = "pricing."

# Only scalar (int/float) fields are admin-editable via a single setting row —
# the two lookup-table fields (paper_size_multiplier, gsm_surcharge_per_page)
# are intentionally excluded, see pricing.py's module docstring.
EDITABLE_RATE_FIELDS = [
    f.name for f in fields(PricingRates)
    if f.type in (int, float, "int", "float")
]


def load_effective_rates(db: Session) -> PricingRates:
    """Overlays any admin-configured PlatformSetting overrides onto the defaults."""
    settings_repo = PlatformSettingRepository(db)
    overrides: dict = {}
    for field_name in EDITABLE_RATE_FIELDS:
        row = settings_repo.get_by_key(f"{PRICING_KEY_PREFIX}{field_name}")
        if row is not None:
            default_value = getattr(DEFAULT_RATES, field_name)
            try:
                # Values are always stored as float-formatted strings (the
                # admin API accepts float input) — parse as float first, then
                # narrow to int if that's this field's native type, rather
                # than calling int("999.0") directly, which raises ValueError.
                parsed = float(row.value)
                overrides[field_name] = int(parsed) if isinstance(default_value, int) else parsed
            except (TypeError, ValueError):
                continue  # corrupt/manually-edited value — fall back to default rather than crash pricing
    return PricingRates(**overrides) if overrides else DEFAULT_RATES


def get_all_rates_with_defaults(db: Session) -> dict[str, float]:
    """Returns every editable rate's *effective* current value (override or default), for the admin UI."""
    rates = load_effective_rates(db)
    return {name: getattr(rates, name) for name in EDITABLE_RATE_FIELDS}


def set_rate(db: Session, field_name: str, value: float) -> float:
    if field_name not in EDITABLE_RATE_FIELDS:
        raise ValueError(f"'{field_name}' is not an admin-editable pricing field")
    settings_repo = PlatformSettingRepository(db)
    key = f"{PRICING_KEY_PREFIX}{field_name}"
    existing = settings_repo.get_by_key(key)
    if existing:
        settings_repo.update(existing, value=str(value))
    else:
        from app.modules.admin.models import PlatformSetting
        settings_repo.create(PlatformSetting(key=key, value=str(value), description=f"Pricing rate: {field_name}"))
    return value
