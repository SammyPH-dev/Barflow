"""
Stock Service Module

This module reads how much usable stock there is for each ingredient
and finds the ingredients that dropped below their reorder threshold.

A lot is "usable" when its quantity is > 0 and it is not expired.

Author: Zacchary Bedard-Chenier
Date: 20/11/2026
Version: 1.0
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, or_, select

from ..models import Ingredient, LotStock
from .errors import NotFoundError


def get_all_stock_levels(session, today=None):
    """Returns the usable stock of every ingredient, sorted by name.

    Args:
        session: The database session of the request.
        today (date, optional): Date used to know if a lot is expired. Defaults to today.

    Returns:
        A list of stock level dicts (see level_from_row()).
    """
    if today is None:
        today = date.today()

    rows = session.execute(levels_query(today)).all()

    levels_list = []

    for row in rows:
        levels_list.append(level_from_row(row))

    return levels_list


def get_stock_level(session, ingredient_id, today=None):
    """Returns the usable stock of a specific ingredient.

    Args:
        session: The database session of the request.
        ingredient_id (int): The id of the ingredient.
        today (date, optional): Date used to know if a lot is expired. Defaults to today.

    Returns:
        A stock level dict (see level_from_row()).

    Raises:
        NotFoundError: If the ingredient does not exist.
    """
    if today is None:
        today = date.today()

    query = levels_query(today).where(Ingredient._id == ingredient_id)
    row = session.execute(query).first()

    if row is None:
        raise NotFoundError(f'Ingredient with id "{ingredient_id}" not found.')

    return level_from_row(row)


def get_all_alerts(session, today=None):
    """Returns an alert for every ingredient whose usable stock is below its reorder threshold."""
    alerts_list = []

    for level in get_all_stock_levels(session, today):
        if level['below_threshold']:
            alerts_list.append(alert_from_level(level))

    return alerts_list


# helpers used by other services


def usable_lot_filter(today):
    """
    SQL version of the business rule: quantity > 0 and not expired.
    A lot that expires today is still usable.
    A lot without an expiry date (None) never expires.
    Must stay the same as LotStock.is_usable().
    """
    return and_(
        LotStock._quantity > 0,
        or_(LotStock._exp_date.is_(None), LotStock._exp_date >= today),
    )


def crossed_threshold(before, after, threshold):
    """
    True only when the stock goes from above or at the threshold to below it.
    This way, the alert is sent once and not again after every following deduction.
    """
    return before >= threshold > after


def alert_from_level(level):
    """Builds an alert dict from a stock level dict."""
    return make_alert(level['ingredient_id'], level['name'],
                      level['usable_quantity'], level['reorder_threshold'])


def alert_from_ingredient(ingredient, usable_quantity):
    """Build an alert dict from an Ingredient and its usable stock."""
    return make_alert(ingredient._id, ingredient._name,
                      usable_quantity, ingredient._reorder_threshold)


def make_alert(ingredient_id, name, usable_quantity, reorder_threshold):
    """The alert sent when an ingredient drops below its reorder threshold."""
    return {
        'ingredient_id': ingredient_id,
        'name': name,
        'usable_quantity': usable_quantity,
        'reorder_threshold': reorder_threshold
    }


# private helpers of this module


def levels_query(today):
    """Build the SQL query that adds up the usable lots of each ingredient."""
    # outer join, so an ingredient that has no usable lot still shows up, with 0
    return (
        select(
            Ingredient._id,
            Ingredient._name,
            Ingredient._mesure_unit,
            Ingredient._reorder_threshold,
            func.coalesce(func.sum(LotStock._quantity), 0),
            func.min(LotStock._exp_date),
        )
        .outerjoin(
            LotStock,
            and_(LotStock._ingredient_id == Ingredient._id, usable_lot_filter(today)),
        )
        .group_by(
            Ingredient._id,
            Ingredient._name,
            Ingredient._mesure_unit,
            Ingredient._reorder_threshold,
        )
        .order_by(Ingredient._name)
    )


def level_from_row(row):
    """Convert one row of levels_query() into a stock level dict."""
    ingredient_id, name, mesure_unit, threshold, usable, next_expiry = row
    usable = Decimal(usable)

    return {
        'ingredient_id': ingredient_id,
        'name': name,
        'mesure_unit': mesure_unit.value,
        'usable_quantity': usable,
        'reorder_threshold': threshold,
        'below_threshold': usable < threshold,
        # soonest expiry among the usable lots, the recommendation service uses it for its:
        # "recommend those that expire in 7 days or less fist" rule
        'next_expiry': next_expiry
    }
