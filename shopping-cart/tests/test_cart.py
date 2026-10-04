from decimal import Decimal

from shopping_cart.cart import (
    CartParser,
    Coupon,
    Product,
    ProductCategory,
    Promotion,
    calculate,
)


def test_product_subtotal():
    product = Product(
        name="ipad",
        quantity=2,
        unit_price=Decimal("2399.00"),
        category=ProductCategory.ELECTRONICS,
    )

    assert product.subtotal == Decimal("4798.00")


def test_promotion_applies():
    promotion = Promotion(
        date=CartParser.parse_date("2015.11.11"),
        discount=Decimal("0.7"),
        category="電子",
    )

    product = Product(
        name="ipad",
        quantity=1,
        unit_price=Decimal("2399.00"),
        category="電子",
    )

    settlement_date = CartParser.parse_date("2015.11.11")

    assert promotion.applies_to(
        product,
        settlement_date
    )


def test_promotion_does_not_apply_when_date_is_different():
    promotion = Promotion(
        date=CartParser.parse_date("2015.11.11"),
        discount=Decimal("0.7"),
        category="電子",
    )

    product = Product(
        name="ipad",
        quantity=1,
        unit_price=Decimal("2399.00"),
        category="電子",
    )

    settlement_date = CartParser.parse_date("2015.11.12")

    assert not promotion.applies_to(
        product,
        settlement_date
    )


def test_coupon_available():
    coupon = Coupon(
        expire_date=CartParser.parse_date("2016.03.02"),
        minimum_amount=Decimal("1000"),
        discount_amount=Decimal("200"),
    )

    settlement_date = CartParser.parse_date("2015.11.11")

    assert coupon.is_available(
        Decimal("1000"),
        settlement_date
    )


def test_coupon_not_available_when_amount_is_too_low():
    coupon = Coupon(
        expire_date=CartParser.parse_date("2016.03.02"),
        minimum_amount=Decimal("1000"),
        discount_amount=Decimal("200"),
    )

    settlement_date = CartParser.parse_date("2015.11.11")

    assert not coupon.is_available(
        Decimal("999.99"),
        settlement_date
    )


def test_case_a():
    input_text = """
    2015.11.11|0.7|電子

    1*ipad:2399.00
    1*顯示器:1799.00
    12*啤酒:25.00
    5*麵包:9.00

    2015.11.11
    2016.3.2 1000 200
    """

    result = calculate(input_text)

    assert result == Decimal("3083.60")


def test_case_b():
    input_text = """
    3*蔬菜:5.98
    8*餐巾紙:3.20
    2015.01.01
    """

    result = calculate(input_text)

    assert result == Decimal("43.54")