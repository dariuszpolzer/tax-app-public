from calculator_tax import calculate_pit_scale


def test_tax_zero_below_threshold():
    result = calculate_pit_scale(20000)

    from decimal import Decimal

    assert result.tax == Decimal("0.00")

    assert result.taxable_income == 20000


def test_tax_first_bracket():
    result = calculate_pit_scale(60000)

    expected = 60000 * 0.12 - 3600
    assert round(result.tax, 2) == round(expected, 2)


def test_tax_second_bracket():
    result = calculate_pit_scale(200000)

    expected = 10800 + (200000 - 120000) * 0.32
    assert round(result.tax, 2) == round(expected, 2)


def test_tax_with_costs():
    result = calculate_pit_scale(
        income=100000,
        other_costs=20000,
        delegation_costs=5000,
    )

    taxable = 100000 - 20000 - 5000
    expected = taxable * 0.12 - 3600

    assert round(result.taxable_income, 2) == taxable
    assert round(result.tax, 2) == round(expected, 2)
