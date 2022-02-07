from django import template

register = template.Library()


def field_name_to_label(value):
    if value == "profit":
        value = "Udbytte"
    elif value == "balance_after":
        value = "Saldo efter"
    elif value == "balance_before":
        value = "Saldo før"
    elif value == "unit_price":
        value = "Salgspris"
    elif value == "unit_amount":
        value = "Antal enheder"
    elif value == "demand":
        value = "Efterspørgsel"
    elif value == "units_sold":
        value = "Solgt"
    elif value == "was_forced":
        value = "Was forced"
    else:
        value = "N/A"
    return value.title()


def get_attribute(value, arg):

    if hasattr(value, str(arg)):
        attr = getattr(value, arg)
        if attr == None:
            return ' ---- '
        else:
            return attr


def subtract(value, arg):
    return value - arg


def to_float(value):
    return str(value)


register.filter('field_name_to_label', field_name_to_label)
register.filter('get_attribute', get_attribute)
register.filter('subtract', subtract)
register.filter('to_float', to_float)
