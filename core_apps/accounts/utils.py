import secrets
from os import getenv
from typing import Union, List
from django.db import transaction
from .emails import send_account_creation_email
from .models import BankAccount
from django.db import connection


def get_next_sequence_value() -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT NEXTVAL('account_number_seq');")
        return cursor.fetchone()[0]


# def generate_account_number(currency: str) -> str:
#     bank_code = getenv("BANK_CODE")
#     branch_code = getenv("BANK_BRANCH_CODE")

#     currency_codes = {
#         "us_dollar": getenv("CURRENCY_CODE_USD"),
#         "pound": getenv("CURRENCY_CODE_GBP"),
#         "taka": getenv("CURRENCY_CODE_BDT"),
#     }
#     currency_code = currency_codes.get(currency)
#     if not currency_code:
#         raise ValueError(f"Invalid currency: {currency}")
    
#     prefix = f"{bank_code}{branch_code}{currency_code}"

#     remaining_digits = 16 - len(prefix) - 1

#     random_digits = "".join(
#         secrets.choice("0123456789") for _ in range(remaining_digits)
#     )
#     partial_account_number = f"{prefix}{random_digits}"

#     check_digit = calculate_luhn_check_digit(partial_account_number)
#     return f"{partial_account_number}{check_digit}"


def generate_account_number(currency: str) -> str:

    bank_code = getenv("BANK_CODE", "123")
    branch_code = getenv("BANK_BRANCH_CODE", "456")
    currency_codes = {
        "us_dollar": getenv("CURRENCY_CODE_USD", "01"),
        "pound": getenv("CURRENCY_CODE_GBP", "02"),
        "taka": getenv("CURRENCY_CODE_BDT", "03"),
    }
    currency_code = currency_codes.get(currency)

    if not currency_code:
        raise ValueError(f"Invalid currency: {currency}")
    
    prefix = f"{bank_code}{branch_code}{currency_code}"
    remaining_digits = 16 - len(prefix) - 1
    
    next_id = get_next_sequence_value()
    sequence_digits = str(next_id).zfill(remaining_digits)
    
    if len(sequence_digits) > remaining_digits:
        raise RuntimeError("Account number pool exhausted")
    
    partial_account_number = f"{prefix}{sequence_digits}"
    check_digit = calculate_luhn_check_digit(partial_account_number)
    
    return f"{partial_account_number}{check_digit}"


def calculate_luhn_check_digit(number: str) -> int:
    def split_into_digits(n: Union[str, int]) -> List[int]:
        return [int(digit) for digit in str(n)]

    digits = split_into_digits(number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)

    for d in even_digits:
        doubled = d * 2
        total += sum(split_into_digits(doubled))

    return (10 - (total % 10)) % 10