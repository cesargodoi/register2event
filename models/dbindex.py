# -*- coding: utf-8 -*-

# indexes db (postgreSQL)

# indexes = [
#     "CREATE INDEX IF NOT EXISTS guest__indexes ON guest (name, name_sa);",
#     "CREATE INDEX IF NOT EXISTS payment_form__index ON payment_form (evenid);",
#     "CREATE INDEX IF NOT EXISTS register__indexes ON register (evenid, guesid);",
#     "CREATE INDEX IF NOT EXISTS register_payment_form__indexes ON register_payment_form (evenid, regid, payfid);",
#     "CREATE INDEX IF NOT EXISTS guest_stay__indexes ON guest_stay (guesid, center, bedroom, bedroom_alt);",
#     "CREATE INDEX IF NOT EXISTS bedroom__index ON bedroom (builid);",
#     "CREATE INDEX IF NOT EXISTS building__index ON building (center);",
# ]

# for index in indexes:
#     db.executesql(index)
