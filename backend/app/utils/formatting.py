def format_inr(amount):
    rupees = str(int(round(amount)))

    if len(rupees) <= 3:
        return "₹" + rupees

    last_three = rupees[-3:]
    rest = rupees[:-3]

    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)

    return "₹" + ",".join(groups) + "," + last_three
