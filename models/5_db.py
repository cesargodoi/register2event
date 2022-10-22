# Center ######################################################################
center_repr = "%(center)s - %(city)s (%(country)s)"
center_abbr = "%(shortname)s"
Center = db.define_table(
    "center",
    Field("center", unique=True, notnull=True, length=50),
    Field("shortname", length=10),
    Field("city", notnull=True, length=40),
    Field("state_prov", length=2),
    Field("country", length=40),
    Field("email", length=100),
    Field("phone", length=15),
    Field("contact", length=40),
    auth.signature,
    format=center_repr,
)
# validators
Center.center.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "center.center")]


# Guest #######################################################################
def guest_repr(row):
    return "%s [%s - %s - %s(%s)]" % (
        row.name,
        row.enrollment,
        row.center.center,
        row.center.city,
        row.center.country,
    )


Guest = db.define_table(
    "guest",
    Field("center", "reference center", notnull=True),
    Field("enrollment", length=9),
    Field("name", notnull=True, length=50),
    Field("name_sa"),
    Field("id_card", length=40),
    Field("gender", default="M", length=1),
    Field("birthday", "date"),
    Field("city", length=40),
    Field("state_prov", length=2),
    Field("country", length=30),
    Field("aspect", default=""),
    Field("email", length=100),
    Field("cell_phone", length=15),
    Field("sos_contact", length=50),
    Field("sos_phone", length=15),
    Field("credit", "decimal(7,2)", default=0.0),
    Field("ps", "text"),
    auth.signature,
    format=guest_repr,
)
# validators
Guest.center.requires = IS_IN_DB(db, "center.id", center_repr)
Guest.name.requires = IS_NOT_EMPTY()
Guest.name_sa.compute = lambda row: "%s" % des(row.name)
Guest.gender.requires = IS_IN_SET(GENDER)
Guest.aspect.requires = IS_EMPTY_OR(IS_IN_SET(ASPECTS))
Guest.birthday.requires = IS_EMPTY_OR(IS_DATE(format="%d/%m/%Y"))
Guest.credit.requires = IS_DECIMAL_IN_RANGE(None, None, dot=".")


# Credit Log
Credit_Log = db.define_table(
    "credit_log",
    Field("guesid", "reference guest", notnull=True),
    Field("credit", "decimal(7,2)", default=0.0),
    Field("oper", default="ADJ", length=4),
    Field("credit_log", length=250),
    auth.signature,
)
# validators
Credit_Log.guesid.requires = IS_IN_DB(db, "guest.id", guest_repr)
Credit_Log.credit.requires = IS_DECIMAL_IN_RANGE(None, None, dot=".")
Credit_Log.oper.requires = IS_EMPTY_OR(IS_IN_SET(CRED_OPER))


# Building ####################################################################
building_repr = "%(building)s"
Building = db.define_table(
    "building",
    Field("center", "reference center", notnull=True),
    Field("building", notnull=True, length=30),
    Field("description", "text"),
    Field("is_active", "boolean", default=False),
    format=building_repr,
)
# validators
Building.center.requires = IS_IN_DB(db, "center.id", center_repr)
Building.building.requires = [
    IS_NOT_EMPTY(),
    IS_NOT_IN_DB(db, "building.building"),
]


# Bedroom #####################################################################
def bedroom_repr(row):
    return "%s(%s) - %s(%s) [%dB %dT]" % (
        row.builid.building,
        row.builid.center.shortname,
        row.bedroom,
        GENDER_BEDROOM[row.gender],
        row.beds,
        row.top_bunks,
    )


Bedroom = db.define_table(
    "bedroom",
    Field("builid", "reference building", notnull=True),
    Field("bedroom", length=20),
    Field("gender", default="M", length=1),
    Field("floor_room", "integer", default=0),
    Field("beds", "integer", default=0),
    Field("top_bunks", "integer", default=0),
    Field("is_active", "boolean", default=True),
    format=bedroom_repr,
)
# validators
Bedroom.builid.requires = IS_IN_DB(db, "building.id", building_repr)
Bedroom.bedroom.requires = IS_NOT_EMPTY()
Bedroom.gender.requires = IS_IN_SET(GENDER_BEDROOM)


# Activities ##################################################################
activity_repr = "%(activity)s (%(activity_type)s)"
Activities = db.define_table(
    "activities",
    Field("activity", length=40),
    Field("activity_type", default="CNF", length=3),
    format=activity_repr,
)
# validators
Activities.activity.requires = [
    IS_NOT_EMPTY(),
    IS_NOT_IN_DB(db, "activities.activity"),
]
Activities.activity_type.requires = IS_IN_SET(ACTIVITY_TYPES)


# Events ######################################################################
def event_repr(row):
    return "%s(%s) - [%s - %s | deadline: %s status: %s]" % (
        row.activity.activity,
        (center_abbr % row.center),
        row.start_date.strftime("%d/%m/%y"),
        row.end_date.strftime("%d/%m/%y"),
        row.reg_deadline.strftime("%d/%m/%y %H:%M:%S"),
        row.status,
    )


Events = db.define_table(
    "events",
    Field("center", "reference center", notnull=True),
    Field("activity", "reference activities", notnull=True),
    Field("description", "text"),
    Field("reg_deadline", "datetime", notnull=True),
    Field("start_date", "date", notnull=True),
    Field("end_date", "date", notnull=True),
    Field("ref_value", "decimal(7,2)"),
    Field("min_value", "decimal(7,2)"),
    Field("status", default="OPN", length=3),
    auth.signature,
    format=event_repr,
)
# validators
Events.center.requires = IS_IN_DB(db, "center.id", center_repr)
Events.activity.requires = IS_IN_DB(db, "activities.id", activity_repr)
Events.reg_deadline.requires = IS_DATETIME()
Events.start_date.requires = IS_DATE()
Events.end_date.requires = IS_DATE()
Events.ref_value.requires = IS_DECIMAL_IN_RANGE(0, None, dot=",")
Events.min_value.requires = IS_DECIMAL_IN_RANGE(0, None, dot=",")
Events.status.requires = IS_IN_SET(EVENT_STATUS)


# Bank Flag ###################################################################
Bank_Flag = db.define_table(
    "bank_flag", Field("name", length=15, notnull=True), format="%(name)s"
)
# validators
Bank_Flag.name.requires = [
    IS_NOT_EMPTY(),
    IS_UPPER(),
    IS_NOT_IN_DB(db, "bank_flag.name"),
]


# Payment Form ################################################################
def payment_form_repr(row):
    return "%s $%s [%s - %s]" % (
        row.pay_type,
        row.amount,
        row.created_on.strftime("%d/%m/%y %H:%M:%S"),
        row.created_by.first_name,
    )


Payment_Form = db.define_table(
    "payment_form",
    Field("evenid", "reference events"),
    Field("centid", "reference center"),
    Field("pay_type", length=3, default="CSH"),
    Field("bank_flag", "reference bank_flag", notnull=False),
    Field("num_ctrl", length=50),
    Field("guesid", "reference guest"),
    Field("amount", "decimal(7,2)"),
    Field("guests", "list:integer"),
    Field("credit", "boolean", default=False),
    Field("late", "boolean", default=False),
    Field("cancel", "boolean", default=False),
    auth.signature,
    format=payment_form_repr,
)
# validators
Payment_Form.pay_type.requires = IS_IN_SET(PAYMENT_TYPES)
Payment_Form.bank_flag.requires = IS_EMPTY_OR(
    IS_IN_DB(db, "bank_flag.id", "%(name)s")
)
Payment_Form.guesid.requires = IS_EMPTY_OR(
    IS_IN_DB(db, "guest.id", guest_repr)
)
Payment_Form.amount.requires = IS_DECIMAL_IN_RANGE(0, None, dot=",")


# Register ####################################################################
def register_repr(row):
    return "%s %s %s [$%s]" % (
        row.evenid.activity.activity,
        row.evenid.start_date.strftime("%d/%m/%y"),
        row.guesid.name,
        row.amount,
    )


Register = db.define_table(
    "register",
    Field("evenid", "reference events"),
    Field("guesid", "reference guest"),
    Field("lodge", default="LDG"),
    Field("no_stairs", "boolean", default=False),
    Field("no_top_bunk", "boolean", default=False),
    Field("arrival_date", default="D1", length=2),
    Field("arrival_time", default="BL", length=2),
    Field("bedroom", "reference bedroom"),
    Field("housed", "boolean", default=False),
    Field("staff", length=3),
    Field("description", "text"),
    Field("ps", "text"),
    Field("amount", "decimal(7,2)"),
    Field("multiple", "boolean", default=False),
    Field("credit", "boolean", default=False),
    Field("late", "boolean", default=False),
    Field("payforms", "list:integer"),
    auth.signature,
    format=register_repr,
)
# validators
Register.evenid.requires = IS_IN_DB(db, "events.id", event_repr)
Register.guesid.requires = IS_IN_DB(db, "guest.id", guest_repr)
Register.lodge.requires = IS_IN_SET(LODGE_TYPES)
Register.arrival_date.requires = IS_IN_SET(ARRIVAL_DATE)
Register.arrival_time.requires = IS_IN_SET(ARRIVAL_TIME)
Register.bedroom.requires = IS_EMPTY_OR(
    IS_IN_DB(db, "bedroom.id", bedroom_repr)
)
Register.staff.requires = IS_EMPTY_OR(IS_IN_SET(STAFFS))
Register.amount.requires = IS_DECIMAL_IN_RANGE(0, None, dot=",")
# many to many
Register_Payment_Form = db.define_table(
    "register_payment_form",
    Field("evenid", "reference events"),
    Field("regid", "reference register"),
    Field("payfid", "reference payment_form"),
)
# validators
Register_Payment_Form.regid.requires = IS_IN_DB(
    db, "register.id", register_repr
)
Register_Payment_Form.payfid.requires = IS_IN_DB(
    db, "payment_form.id", payment_form_repr
)


# Guest Stay ##################################################################
Guest_Stay = db.define_table(
    "guest_stay",
    Field("guesid", "reference guest", notnull=True),
    Field("center", "reference center", notnull=True),
    Field("lodge", default="LDG"),
    Field("no_stairs", "boolean", default=False),
    Field("no_top_bunk", "boolean", default=False),
    Field("arrival_date", default="D1", length=2),
    Field("arrival_time", default="BL", length=2),
    Field("bedroom", "integer"),
    Field("bedroom_alt", "integer"),
    Field("staff", length=3),
    Field("description", "text"),
    Field("ps", "text"),
)
# validators
Guest_Stay.guesid.requires = IS_IN_DB(db, "guest.id", guest_repr)
Guest_Stay.center.requires = IS_IN_DB(db, "center.id", center_repr)
Guest_Stay.lodge.requires = IS_IN_SET(LODGE_TYPES)
Guest_Stay.arrival_date.requires = IS_IN_SET(ARRIVAL_DATE)
Guest_Stay.arrival_time.requires = IS_IN_SET(ARRIVAL_TIME)
Guest_Stay.staff.requires = IS_EMPTY_OR(IS_IN_SET(STAFFS))


# Bedrooms mapping ############################################################
def bedrooms_mapping_repr(row):
    return "%s %s" % (row.centid, row.evenid)


Bedrooms_mapping = db.define_table(
    "bedrooms_mapping",
    Field("centid", "reference center", notnull=True),
    Field("evenid", "reference events", notnull=True),
    Field("bedrooms", "json"),
    auth.signature,
    format=bedrooms_mapping_repr,
)
# validators
Bedrooms_mapping.centid.requires = IS_IN_DB(db, "center.id", center_repr)
Bedrooms_mapping.evenid.requires = IS_IN_DB(db, "events.id", event_repr)
Bedrooms_mapping.bedrooms.requires = IS_JSON()


# ## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)
