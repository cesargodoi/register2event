# -*- coding: utf-8 -*-

# indexes db (postgreSQL)

indexes = [
    "CREATE INDEX IF NOT EXISTS guest__name ON guest (name);",
    "CREATE INDEX IF NOT EXISTS guest__name_sa ON guest (name_sa);",
    "CREATE INDEX IF NOT EXISTS payment_form__evenid ON payment_form (evenid);",
    "CREATE INDEX IF NOT EXISTS register__evenid ON register (evenid);",
    "CREATE INDEX IF NOT EXISTS register__guesid ON register (guesid);",
    "CREATE INDEX IF NOT EXISTS register_payment_form__evenid ON register_payment_form (evenid);",
    "CREATE INDEX IF NOT EXISTS register_payment_form__regid ON register_payment_form (regid);",
    "CREATE INDEX IF NOT EXISTS register_payment_form__payfid ON register_payment_form (payfid);",
    "CREATE INDEX IF NOT EXISTS guest_stay__guesid ON guest_stay (guesid);",
    "CREATE INDEX IF NOT EXISTS guest_stay__center ON guest_stay (center);",
    "CREATE INDEX IF NOT EXISTS bedroom__builid ON bedroom (builid);",
    "CREATE INDEX IF NOT EXISTS building__center ON building (center);",
]

for index in indexes:
    db.executesql(index)
