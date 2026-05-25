from ksef.utils.ksef_number import is_valid_ksef_number


def test_valid_ksef_number():
    number = "ABC1234567-20260313-5D3A990000FD-B1"

    assert is_valid_ksef_number(number) is True


def test_invalid_ksef_number():
    number = "INVALID-123"

    assert is_valid_ksef_number(number) is False
