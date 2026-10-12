"""Generates deterministic fake data for the Country Club database -> data.sql"""
import random
from datetime import date, datetime, timedelta

random.seed(452)
out = []


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def insert(table, cols, rows):
    for r in rows:
        out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(q(x) for x in r)});")
    out.append("")


# ---- MembershipType
types = [
    (1, "Student", "Discounted membership for eligible students", 50.00, 25.00, 1, 1),
    (2, "Individual", "Standard membership for one person", 100.00, 150.00, 1, 1),
    (3, "Family", "Membership for eligible family members", 220.00, 300.00, 6, 1),
    (4, "Premium", "Premium membership with expanded benefits", 350.00, 500.00, 4, 1),
    (5, "Senior", "Legacy discounted plan for members 65+ (no longer sold)", 75.00, 50.00, 2, 0),
]
insert("MembershipType", ["membership_type_id", "type_name", "description", "monthly_fee",
                          "initiation_fee", "max_members", "is_active"], types)
max_members = {t[0]: t[5] for t in types}
monthly = {t[0]: t[3] for t in types}
initiation = {t[0]: t[4] for t in types}

# ---- Facility
facilities = [
    (4001, "Main Golf Course", "Golf", "North Grounds", 100, 0.00, 1),
    (4002, "Swimming Pool", "Swimming", "Recreation Center", 50, 0.00, 1),
    (4003, "Tennis Court 1", "Tennis", "East Grounds", 4, 10.00, 1),
    (4004, "Fitness Center", "Fitness", "Main Building", 30, 0.00, 1),
    (4005, "Private Event Room", "Dining", "Clubhouse", 80, 75.00, 1),
    (4006, "Tennis Court 2", "Tennis", "East Grounds", 4, 10.00, 1),
    (4007, "Executive Golf Course", "Golf", "South Grounds", 60, 25.00, 1),
    (4008, "Lakeside Grill", "Dining", "Clubhouse", 120, 0.00, 1),
    (4009, "Yoga Studio", "Fitness", "Main Building", 20, 15.00, 1),
    (4010, "Indoor Pool", "Swimming", "Recreation Center", 30, 5.00, 0),
]
insert("Facility", ["facility_id", "facility_name", "facility_type", "location", "capacity",
                    "hourly_fee", "is_active"], facilities)
fac_by_id = {f[0]: f for f in facilities}

# ---- MembershipFacility
mf = {
    1: {4002: "Included", 4003: "Included", 4006: "Included", 4004: "Discounted", 4008: "Discounted", 4001: "Restricted"},
    2: {4002: "Included", 4003: "Included", 4006: "Included", 4004: "Included", 4008: "Included",
        4009: "Discounted", 4001: "Discounted", 4007: "Discounted"},
    3: {4002: "Included", 4003: "Included", 4006: "Included", 4004: "Included", 4008: "Included",
        4001: "Discounted", 4007: "Included", 4009: "Discounted", 4010: "Included"},
    4: {f[0]: "Included" for f in facilities},
    5: {4002: "Included", 4004: "Included", 4008: "Included", 4001: "Discounted", 4003: "Restricted"},
}
rows = [(t, f, a) for t, d in mf.items() for f, a in d.items()]
insert("MembershipFacility", ["membership_type_id", "facility_id", "access_level"], rows)

# ---- Membership + Member
first_m = ["James", "Liam", "Noah", "Oliver", "Elijah", "Lucas", "Mason", "Ethan", "Logan", "Henry",
           "Jack", "Owen", "Caleb", "Isaac", "Daniel", "Samuel", "Wyatt", "Carter", "Dylan", "Nathan"]
first_f = ["Olivia", "Emma", "Ava", "Sophia", "Mia", "Amelia", "Harper", "Evelyn", "Ella", "Grace",
           "Chloe", "Lily", "Zoe", "Hannah", "Nora", "Ruby", "Claire", "Layla", "Stella", "Maya"]
last = ["Anderson", "Bennett", "Carter", "Davis", "Edwards", "Foster", "Garcia", "Hughes", "Ito",
        "Jensen", "Kim", "Lopez", "Miller", "Nguyen", "Ortiz", "Parker", "Quinn", "Reyes", "Sorensen",
        "Thompson", "Underwood", "Vasquez", "Walker", "Young", "Zimmerman", "Brooks", "Clark", "Dixon"]

TODAY = date(2026, 10, 12)
plan = []  # (type_id, n_members)
for t, n in [(1, 8), (2, 12), (3, 12), (4, 8), (5, 3)]:
    plan += [t] * n
random.shuffle(plan)

memberships, members, payments = [], [], []
mid, pid, txn = 1001, 3001, 10001
member_id = 2001
used_names = set()


def rnd_date(a, b):
    return a + timedelta(days=random.randint(0, (b - a).days))


def new_name(female=None):
    while True:
        f = random.choice(first_f if (female if female is not None else random.random() < .5) else first_m)
        l = random.choice(last)
        if (f, l) not in used_names:
            used_names.add((f, l))
            return f, l


for t in plan:
    start = rnd_date(date(2023, 1, 1), date(2026, 9, 1))
    freq = random.choice(["Monthly", "Monthly", "Annual"]) if t != 1 else "Monthly"
    r = random.random()
    if t == 5:
        status, end = "Expired", start + timedelta(days=365 * 2)
        if end > TODAY:
            end = TODAY - timedelta(days=random.randint(10, 200))
            start = min(start, end - timedelta(days=365))
    elif r < .72:
        status = "Active"
        end = None if random.random() < .35 else max(start + timedelta(days=365), TODAY + timedelta(days=random.randint(30, 300)))
    elif r < .82:
        status, end = "Suspended", None
    elif r < .92:
        status = "Cancelled"
        end = min(TODAY, start + timedelta(days=random.randint(60, 500)))
    else:
        status = "Expired"
        end = TODAY - timedelta(days=random.randint(5, 150))
        start = min(start, end - timedelta(days=365))
    auto = 1 if (status == "Active" and random.random() < .6) else 0
    memberships.append((mid, t, start.isoformat(), end.isoformat() if end else None, status, freq, auto))

    # members
    last_name = random.choice(last)
    cap = max_members[t]
    if t in (3, 4):
        n = random.randint(2, min(cap, 5))
    elif t == 5:
        n = random.randint(1, 2)
    else:
        n = 1
    roles = ["Primary"]
    if n > 1:
        if t == 5:
            roles.append("Spouse")
        else:
            roles.append("Spouse")
            roles += [random.choice(["Child", "Child", "Dependent"]) for _ in range(n - 2)]
    for i, role in enumerate(roles):
        female = random.random() < .5
        f = random.choice(first_f if female else first_m)
        while (f, last_name) in used_names:
            f = random.choice(first_f if female else first_m)
        used_names.add((f, last_name))
        if role == "Primary":
            dob = date(1946, 1, 1) + timedelta(days=random.randint(0, 365 * 14)) if t == 5 else \
                (rnd_date(date(2000, 1, 1), date(2007, 12, 31)) if t == 1 else rnd_date(date(1960, 1, 1), date(1996, 12, 31)))
        elif role == "Spouse":
            dob = rnd_date(date(1950, 1, 1) if t == 5 else date(1960, 1, 1), date(1996, 12, 31) if t != 5 else date(1960, 12, 31))
        else:
            dob = rnd_date(date(2008, 1, 1), date(2020, 12, 31))
        has_contact = role in ("Primary", "Spouse")
        email = f"{f.lower()}.{last_name.lower()}@example.com" if has_contact and random.random() < .9 else None
        phone = f"801555{random.randint(0, 9999):04d}" if has_contact and random.random() < .85 else None
        mstatus = {"Active": "Active", "Suspended": "Suspended"}.get(status, "Inactive")
        if status == "Active" and random.random() < .05:
            mstatus = "Inactive"
        members.append((member_id, mid, f, last_name, dob.isoformat() if random.random() < .95 else None,
                        email, phone, role, start.isoformat(), mstatus))
        member_id += 1

    # payments
    pay_rows = []
    pay_rows.append((start, initiation[t] + (monthly[t] if freq == "Monthly" else monthly[t] * 12 * .9)))
    horizon = min(end or TODAY, TODAY)
    if freq == "Monthly":
        d = start
        k = 0
        while True:
            d = date(d.year + (d.month // 12), d.month % 12 + 1, min(start.day, 28))
            if d > horizon or k >= 6:
                break
            pay_rows.append((d, monthly[t]))
            k += 1
    else:
        d = start
        while True:
            d = date(d.year + 1, d.month, min(d.day, 28))
            if d > horizon:
                break
            pay_rows.append((d, round(monthly[t] * 12 * .9, 2)))
    for d, amt in pay_rows:
        if d > TODAY:
            continue
        rr = random.random()
        ps = "Completed" if rr < .82 else "Pending" if rr < .88 else "Failed" if rr < .95 else "Refunded"
        if (TODAY - d).days > 60 and ps == "Pending":
            ps = "Completed"
        method = random.choices(["Card", "Cash", "Bank Transfer"], [6, 1, 3])[0]
        ts = datetime(d.year, d.month, d.day, random.randint(8, 18), random.choice([0, 15, 30, 45]), 0)
        ref = None if method == "Cash" and random.random() < .5 else f"TXN-{txn}"
        txn += 1
        payments.append((pid, mid, ts.strftime("%Y-%m-%d %H:%M:%S"), round(float(amt), 2), method, ps, ref))
        pid += 1
    mid += 1

insert("Membership", ["membership_id", "membership_type_id", "start_date", "end_date", "status",
                      "billing_frequency", "auto_renew"], memberships)
insert("Member", ["member_id", "membership_id", "first_name", "last_name", "date_of_birth", "email",
                  "phone", "member_role", "join_date", "status"], members)
insert("Payment", ["payment_id", "membership_id", "payment_date", "amount", "payment_method",
                   "payment_status", "transaction_reference"], payments)

# ---- Reservation: only members of eligible, non-cancelled memberships, facilities they have access to
ms_type = {m[0]: m[1] for m in memberships}
ms_status = {m[0]: m[4] for m in memberships}
res, rid = [], 5001
notes = ["Afternoon tennis", "Family swim", "Fitness session", "Birthday party", "Business lunch",
         "Golf outing", "Yoga class", "Anniversary dinner", "Swim lessons", "Charity event", None, None, None]
bookable = [m for m in members if ms_status[m[1]] in ("Active", "Suspended", "Expired")]
for _ in range(90):
    m = random.choice(bookable)
    t = ms_type[m[1]]
    fid = random.choice(list(mf[t].keys()))
    f = fac_by_id[fid]
    day = rnd_date(date(2026, 4, 1), date(2026, 12, 15))
    hour = random.randint(7, 19)
    dur = random.choice([1, 1, 2, 3, 4]) if f[2] == "Golf" else random.choice([1, 1, 2])
    st = datetime(day.year, day.month, day.day, hour)
    en = st + timedelta(hours=dur)
    cap = f[4]
    ps = random.randint(1, min(cap, 4 if f[2] in ("Tennis", "Golf") else 8 if f[2] != "Dining" else 12))
    if day < TODAY:
        status = random.choices(["Completed", "Cancelled"], [8, 2])[0]
    else:
        status = random.choices(["Confirmed", "Pending", "Cancelled"], [6, 3, 1])[0]
    res.append((rid, m[0], fid, st.strftime("%Y-%m-%d %H:%M:%S"), en.strftime("%Y-%m-%d %H:%M:%S"),
                ps, status, random.choice(notes)))
    rid += 1
insert("Reservation", ["reservation_id", "member_id", "facility_id", "start_time", "end_time",
                       "party_size", "status", "notes"], res)

with open("data.sql", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
print(f"memberships={len(memberships)} members={len(members)} payments={len(payments)} reservations={len(res)}")
