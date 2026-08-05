"""
Regression test for a real bug found during integration testing: admin
updates a pricing rate via the API (values always arrive as floats, e.g.
999.0), which gets stored as the string "999.0" — and int("999.0") raises
ValueError in Python. The original implementation silently swallowed this
as if the value were corrupt and fell back to the default, so an admin's
price change appeared to succeed (200 OK) but never actually took effect.
"""
from app.modules.admin.models import PlatformSetting
from app.modules.admin.pricing_config import load_effective_rates, set_rate


def test_setting_an_int_field_via_a_float_string_takes_effect(db_engine):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_engine)
    db = Session()

    set_rate(db, "rate_bw_page", 999.0)
    db.commit()

    rates = load_effective_rates(db)
    assert rates.rate_bw_page == 999
    assert isinstance(rates.rate_bw_page, int)


def test_unset_rate_falls_back_to_default(db_engine):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_engine)
    db = Session()

    rates = load_effective_rates(db)
    assert rates.rate_bw_page == 150  # DEFAULT_RATES value, untouched


def test_corrupt_setting_value_falls_back_to_default_instead_of_crashing(db_engine):
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_engine)
    db = Session()

    db.add(PlatformSetting(key="pricing.rate_bw_page", value="not-a-number"))
    db.commit()

    rates = load_effective_rates(db)
    assert rates.rate_bw_page == 150  # falls back, doesn't raise
