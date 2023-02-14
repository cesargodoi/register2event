from gluon.contrib.appconfig import AppConfig

# once in production, remove reload=True to gain full speed
myconf = AppConfig(reload=False)

# db connect - set fake_migrate_all=True to reload
db = DAL(
    "postgres://postgres:locrio9@localhost:5432/r2e_db",
    check_reserved=["all"],
    fake_migrate_all=True,
)

# default view/generic.extension or controller/function.extension
response.generic_patterns = ["*"] if request.is_local else []

# choose a style for forms ('bootstrap3_stacked' or 'bootstrap2' ...)
response.formstyle = myconf.take("forms.formstyle")
response.form_label_separator = myconf.take("forms.separator")


from gluon.tools import Auth, Service, PluginManager

auth = Auth(db)
service = Service()
plugins = PluginManager()

## configurar o current
from gluon import current

current.auth = auth
current.db = db

## create all tables needed by auth if not custom tables
auth.settings.extra_fields["auth_user"] = [Field("center", "integer")]
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = True
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = (
    "logging" if request.is_local else myconf.take("smtp.sender")
)
mail.settings.sender = myconf.take("smtp.sender")
mail.settings.login = myconf.take("smtp.login")

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## force to pt-br
T.force("pt-br")
