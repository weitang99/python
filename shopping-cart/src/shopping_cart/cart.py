from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import re
import sys


# =========================
# Domain Model
# =========================
@dataclass
class Product:
    name: str
    quantity: int
    unit_price: Decimal
    category: str

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Promotion:
    date: datetime
    discount: Decimal
    category: str

    def applies_to(self, product: Product, settlement_date: datetime) -> bool:
        return (
            self.date.date() == settlement_date.date()
            and self.category == product.category
        )


@dataclass
class Coupon:
    expire_date: datetime
    minimum_amount: Decimal
    discount_amount: Decimal

    def is_available(
        self,
        amount: Decimal,
        settlement_date: datetime
    ) -> bool:
        return (
            settlement_date.date() <= self.expire_date.date()
            and amount >= self.minimum_amount
        )

# =========================
# Product Category
# =========================
class ProductCategory:
    ELECTRONICS = "電子"
    FOOD = "食品"
    DAILY = "日用品"
    ALCOHOL = "酒類"

    @classmethod
    def get_category(cls, product_name: str) -> str:
        category_map = {
            "ipad": cls.ELECTRONICS,
            "iphone": cls.ELECTRONICS,
            "顯示器": cls.ELECTRONICS,
            "筆記型電腦": cls.ELECTRONICS,
            "鍵盤": cls.ELECTRONICS,

            "麵包": cls.FOOD,
            "餅乾": cls.FOOD,
            "蛋糕": cls.FOOD,
            "牛肉": cls.FOOD,
            "魚": cls.FOOD,
            "蔬菜": cls.FOOD,

            "餐巾紙": cls.DAILY,
            "收納箱": cls.DAILY,
            "咖啡杯": cls.DAILY,
            "雨傘": cls.DAILY,

            "啤酒": cls.ALCOHOL,
            "白酒": cls.ALCOHOL,
            "伏特加": cls.ALCOHOL,
        }

        if product_name not in category_map:
            raise ValueError(f"未知商品：{product_name}")

        return category_map[product_name]


# =========================
# Parser
# =========================
class CartParser:

    PRODUCT_PATTERN = re.compile(
        r"^(\d+)\*(.+):(\d+(?:\.\d+)?)$"
    )

    @staticmethod
    def parse_date(value: str) -> datetime:
        formats = [
            "%Y.%m.%d",
            "%Y-%m-%d",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        raise ValueError(f"無法解析日期：{value}")

    @classmethod
    def parse_product(cls, line: str) -> Product:
        match = cls.PRODUCT_PATTERN.match(line.strip())

        if not match:
            raise ValueError(f"無法解析商品：{line}")

        quantity = int(match.group(1))
        name = match.group(2)
        unit_price = Decimal(match.group(3))

        category = ProductCategory.get_category(name)

        return Product(
            name=name,
            quantity=quantity,
            unit_price=unit_price,
            category=category
        )

    @classmethod
    def parse_promotion(cls, line: str) -> Promotion:
        parts = line.split("|")

        if len(parts) != 3:
            raise ValueError(f"無法解析促銷資訊：{line}")

        date = cls.parse_date(parts[0].strip())
        discount = Decimal(parts[1].strip())
        category = parts[2].strip()

        return Promotion(
            date=date,
            discount=discount,
            category=category
        )

    @classmethod
    def parse_coupon(cls, line: str) -> Coupon:
        parts = line.split()

        if len(parts) != 3:
            raise ValueError(f"無法解析優惠券：{line}")

        expire_date = cls.parse_date(parts[0])
        minimum_amount = Decimal(parts[1])
        discount_amount = Decimal(parts[2])

        return Coupon(
            expire_date=expire_date,
            minimum_amount=minimum_amount,
            discount_amount=discount_amount
        )


# =========================
# Shopping Cart
# =========================
class ShoppingCart:

    def __init__(
        self,
        products: list[Product],
        promotions: list[Promotion],
        coupon: Optional[Coupon],
        settlement_date: datetime
    ):
        self.products = products
        self.promotions = promotions
        self.coupon = coupon
        self.settlement_date = settlement_date

    def calculate_product_amount(self) -> Decimal:
        total = Decimal("0")

        for product in self.products:
            amount = product.subtotal

            promotion = self._find_promotion(product)

            if promotion is not None:
                amount *= promotion.discount

            total += amount

        return total

    def calculate_coupon_discount(self, amount: Decimal) -> Decimal:
        if self.coupon is None:
            return Decimal("0")

        if self.coupon.is_available(
            amount,
            self.settlement_date
        ):
            return self.coupon.discount_amount

        return Decimal("0")

    def calculate_total(self) -> Decimal:
        amount = self.calculate_product_amount()

        coupon_discount = self.calculate_coupon_discount(amount)

        result = amount - coupon_discount

        return self._round_money(result)

    def _find_promotion(
        self,
        product: Product
    ) -> Optional[Promotion]:
        for promotion in self.promotions:
            if promotion.applies_to(
                product,
                self.settlement_date
            ):
                return promotion

        return None

    @staticmethod
    def _round_money(amount: Decimal) -> Decimal:
        return amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )


# =========================
# Input Parser
# =========================
class InputParser:

    @classmethod
    def parse(cls, text: str) -> ShoppingCart:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        products = []
        promotion = None
        settlement_date = None
        coupon = None

        for line in lines:

            # 促銷：
            # 2015.11.11|0.7|電子
            if "|" in line:
                promotion = CartParser.parse_promotion(line)

            # 商品：
            # 1*ipad:2399.00
            elif "*" in line and ":" in line:
                products.append(
                    CartParser.parse_product(line)
                )

            # 優惠券：
            # 2016.3.2 1000 200
            elif len(line.split()) == 3:
                coupon = CartParser.parse_coupon(line)

            # 結算日期：
            # 2015.11.11
            else:
                settlement_date = CartParser.parse_date(line)

        if settlement_date is None:
            raise ValueError("缺少結算日期")

        return ShoppingCart(
            products=products,
            promotions=(
                [promotion]
                if promotion is not None
                else []
            ),
            coupon=coupon,
            settlement_date=settlement_date
        )


# =========================
# Application
# =========================
def calculate(text: str) -> Decimal:
    cart = InputParser.parse(text)
    return cart.calculate_total()

def read_input() -> str:
    lines = []

    while True:
        line = input()
        lines.append(line)

        # 優惠券
        if len(line.split()) == 3:
            break

        # 結算日期，而且前面已經有商品
        if (
            "*" not in line
            and "|" not in line
            and len(line.split()) == 1
            and any("*" in x for x in lines)
        ):
            break

    return "\n".join(lines)

def main() -> None:
    input_text = read_input()
    # input_text = """
    # 3*蔬菜:5.98
    # 8*餐巾紙:3.20
    # 2015.01.01
    # """

    try:
        result = calculate(input_text)
        print(f"{result:.2f}")

    except ValueError as error:
        print(f"Input Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
