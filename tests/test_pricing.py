"""Unit tests for the document-printing pricing engine (no DB needed)."""
from app.modules.documents.models import BindingType, ColorMode, PrintDocument, SideMode
from app.modules.documents.pricing import calculate_price


def _make_doc(**overrides) -> PrintDocument:
    defaults = dict(
        customer_id="00000000-0000-0000-0000-000000000000",
        file_url="x", file_name="x.pdf", file_type="pdf", page_count=10, copies=1,
        color_mode=ColorMode.BLACK_WHITE, paper_size="A4", paper_gsm=75,
        side_mode=SideMode.SINGLE, binding=BindingType.NONE,
        lamination=False, cover_page=False, premium_paper=False, express_delivery=False,
    )
    defaults.update(overrides)
    return PrintDocument(**defaults)


def test_bw_baseline_price():
    doc = _make_doc(page_count=10, copies=1)
    price = calculate_price(doc)
    assert price == 1500  # 10 pages * ₹1.50


def test_color_more_expensive_than_bw():
    bw = calculate_price(_make_doc(color_mode=ColorMode.BLACK_WHITE))
    color = calculate_price(_make_doc(color_mode=ColorMode.COLOR))
    assert color > bw


def test_double_side_cheaper_than_single():
    single = calculate_price(_make_doc(side_mode=SideMode.SINGLE))
    double = calculate_price(_make_doc(side_mode=SideMode.DOUBLE))
    assert double < single


def test_express_delivery_adds_surcharge():
    normal = calculate_price(_make_doc(express_delivery=False))
    express = calculate_price(_make_doc(express_delivery=True))
    assert express > normal
    assert express == round(normal * 1.25)


def test_spiral_binding_adds_flat_cost_per_copy():
    none_binding = calculate_price(_make_doc(binding=BindingType.NONE, copies=2))
    spiral = calculate_price(_make_doc(binding=BindingType.SPIRAL, copies=2))
    assert spiral - none_binding == 3000 * 2
