PRAGMA foreign_keys = ON;

CREATE TABLE MembershipType (
    membership_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE,
    description TEXT,
    monthly_fee NUMERIC NOT NULL CHECK (monthly_fee >= 0),
    initiation_fee NUMERIC NOT NULL CHECK (initiation_fee >= 0),
    max_members INTEGER NOT NULL CHECK (max_members > 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE Membership (
    membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
    membership_type_id INTEGER NOT NULL REFERENCES MembershipType(membership_type_id),
    start_date DATE NOT NULL,
    end_date DATE,
    status TEXT NOT NULL CHECK (status IN ('Active', 'Suspended', 'Cancelled', 'Expired')),
    billing_frequency TEXT NOT NULL CHECK (billing_frequency IN ('Monthly', 'Annual')),
    auto_renew INTEGER NOT NULL DEFAULT 0 CHECK (auto_renew IN (0, 1)),
    CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE Member (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    membership_id INTEGER NOT NULL REFERENCES Membership(membership_id),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE,
    email TEXT,
    phone TEXT,
    member_role TEXT NOT NULL CHECK (member_role IN ('Primary', 'Spouse', 'Child', 'Dependent')),
    join_date DATE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Active', 'Inactive', 'Suspended'))
);

CREATE TABLE Payment (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    membership_id INTEGER NOT NULL REFERENCES Membership(membership_id),
    payment_date TIMESTAMP NOT NULL,
    amount NUMERIC NOT NULL CHECK (amount > 0),
    payment_method TEXT NOT NULL CHECK (payment_method IN ('Card', 'Cash', 'Bank Transfer')),
    payment_status TEXT NOT NULL CHECK (payment_status IN ('Pending', 'Completed', 'Failed', 'Refunded')),
    transaction_reference TEXT UNIQUE
);

CREATE TABLE Facility (
    facility_id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_name TEXT NOT NULL UNIQUE,
    facility_type TEXT NOT NULL,
    location TEXT,
    capacity INTEGER CHECK (capacity IS NULL OR capacity > 0),
    hourly_fee NUMERIC NOT NULL CHECK (hourly_fee >= 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE MembershipFacility (
    membership_type_id INTEGER NOT NULL REFERENCES MembershipType(membership_type_id),
    facility_id INTEGER NOT NULL REFERENCES Facility(facility_id),
    access_level TEXT NOT NULL CHECK (access_level IN ('Included', 'Discounted', 'Restricted')),
    PRIMARY KEY (membership_type_id, facility_id)
);

CREATE TABLE Reservation (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL REFERENCES Member(member_id),
    facility_id INTEGER NOT NULL REFERENCES Facility(facility_id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    party_size INTEGER NOT NULL CHECK (party_size > 0),
    status TEXT NOT NULL CHECK (status IN ('Pending', 'Confirmed', 'Cancelled', 'Completed')),
    notes TEXT,
    CHECK (end_time > start_time)
);
