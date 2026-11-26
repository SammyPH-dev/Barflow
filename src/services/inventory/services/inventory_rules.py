"""
Inventory Validation Rules Module

This module contains the custom validation rules used by the inventory schemas:
non-blank text, non-zero quantities and unique ingredients in a deduction.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""


def validate_not_blank(value):
    # Validates that a text is not only spaces
    if value is not None and not value.strip():
        raise ValueError("This field cannot be empty or blank.")
    return value


def validate_not_zero(value):
    # Validates that a manual adjustment really changes the stock
    if value == 0:
        raise ValueError("The quantity change cannot be zero.")
    return value


def validate_unique_ingredients(items):
    # Validates the list of ingredients of a deduction
    # Each ingredient can only be there once (quantities must be merged if multiple of the same ingredient appears)
    ingredient_ids = [item.ingredient_id for item in items]

    # If the list and its set version don't have the same length,
    # it means that one ingredient was there more than once
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise ValueError("Each ingredient can only appear once, merge the quantities.")
    return items
