# -*- coding: utf-8 -*-

from gluon.tools import Crud

crud = Crud(db)


def dbadmin():
    crud.messages.submit_button = T('Submit')
    return dict(form=crud())


@auth.requires_login()
def index():
    # if exists session.mapp or session.register delete it
    if session.mapp or session.register:
        clear_session()
    query = (Events.id > 0) & (Events.status == 'OPN') & (Events.is_active == True)
    rows = db(query).select(orderby=~Events.start_date)
    for r in rows:
        r.guests = db((Register.evenid == r.id) &
                      (Register.is_active == True) &
                      (Register.credit == False)).count()
    # response.flash = "Welcome!"
    return dict(message=T('Welcome to reg2event!'),
                rows=rows)


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    if request.args(0) == 'not_authorized':
        response.view = 'default/not_autorized.html'
        return dict(home=URL('default', 'index'))
    form = auth()
    if 'profile' in request.args:
        form.element(_id="auth_user_center__row")["_style"] = "display:none;"
    form.element(_type='submit')['_class'] = "btn btn-outline btn-primary btn-lg btn-block"
    return dict(form=form)


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


# Grids to admin
# Center
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def manage_center():
    response.view = 'default/manage.html'
    grid = SQLFORM.grid(Center,
                        orderby=[Center.state_prov, Center.center],
                        showbuttontext=False)
    return dict(grid=grid)


# Guest
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def manage_guest():
    response.view = 'default/manage.html'
    grid = SQLFORM.grid(Guest,
                        orderby=[Guest.name_sa],
                        showbuttontext=False)
    return dict(grid=grid)


# Building
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def manage_building():
    response.view = 'default/manage.html'
    grid = SQLFORM.grid(Building,
                        orderby=[Building.building],
                        showbuttontext=False)
    return dict(grid=grid)


# Bedroom
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def manage_bedroom():
    response.view = 'default/manage.html'
    grid = SQLFORM.grid(Bedroom,
                        orderby=[Bedroom.builid],
                        showbuttontext=False)
    return dict(grid=grid)


# Activities
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def manage_activities():
    response.view = 'default/manage.html'
    grid = SQLFORM.grid(Activities,
                        orderby=[Activities.activity_type],
                        showbuttontext=False)
    return dict(grid=grid)


# Events
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def manage_events():
    response.view = 'default/manage.html'
    grid = SQLFORM.grid(Events,
                        orderby=[Events.center, Events.activity],
                        showbuttontext=False)
    return dict(grid=grid)


# Bank Flag
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def manage_bank_flag():
    response.view = 'default/manage.html'
    grid = SQLFORM.grid(Bank_Flag,
                        orderby=[Bank_Flag.name],
                        showbuttontext=False)
    return dict(grid=grid)


# Payment Form
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def manage_payment_form():
    response.view = 'default/manage.html'
    grid = SQLFORM.grid(Payment_Form,
                        orderby=[Payment_Form.bank_flag,
                                 Payment_Form.created_on],
                        showbuttontext=False)
    return dict(grid=grid)


# Register
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def manage_register():
    response.view = 'default/manage.html'
    grid = SQLFORM.grid(Register,
                        orderby=[Register.evenid, Register.guesid],
                        showbuttontext=False)
    return dict(grid=grid)


# Guest Stay
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def manage_guest_stay():
    response.view = 'default/manage.html'
    grid = SQLFORM.grid(Guest_Stay,
                        orderby=[Guest_Stay.id],
                        showbuttontext=False)
    return dict(grid=grid)


# Change center
@auth.requires_login()
@auth.requires(auth.has_membership('root') or auth.has_membership('admin'))
def change_center():
    response.view = 'default/manage.html'
    CENTERS = {c.id:center_repr % c for c in db(Center).select(orderby=Center.id)}
    grid = SQLFORM.factory(
        Field('center',
              requires=IS_IN_SET(CENTERS),
              default=1,
              label=T('center')),
        submit_button=T('change center')
    )
    if grid.process().accepted:
        auth.user.center = int(request.vars.center)
        redirect(URL('default', 'index'))
    return dict(grid=grid)


def status():
    return dict(request=request, session=session, response=response)


# kill them all
@auth.requires_login()
@auth.requires(auth.has_membership('root'))
def kill_them_all():
    if session.kill_register or session.kill_register == '':
        del session.kill_register

    search = SQLFORM.factory(
        Field('type',
              requires=IS_IN_SET(['register', 'payform']),
              default='register'),
        Field('number'),
        submit_button=T('search')
    )

    if search.process().accepted:
        if request.vars.type == 'payform':
            read = read_register(request.vars.number, pf=True)
        else:
            read = read_register(request.vars.number)

        registers, _registers, payforms, _payforms, _gsc = [], [], [], [], []

        if read:
            title = T('credit launch details') \
                    if read.registers[0].credit \
                    else T('subscription details')
            if read.registers:
                evenid = int(read.registers[0].evenid)

                for reg in read.registers:
                    name = shortname(reg.guesid.name)
                    active = 'active' if reg.is_active else 'inactive'
                    g = (reg.id, name, reg.amount, active)
                    registers.append(g)
                    _registers.append(int(reg.id))

            if read.payforms:
                if not evenid:
                    evenid = int(read.payforms[0].evenid)

                for pay in read.payforms:
                    active = 'active' if pay.is_active else 'inactive'
                    if pay.pay_type == 'GSC':
                        _gsc.append([int(pay.guesid), float(pay.amount)])
                        gues_cred = '%(name)s' % Guest[pay.guesid]
                        p = (pay.id, pay.pay_type, gues_cred, '', pay.amount, active)
                    elif pay.bank_flag:
                        bf_name = pay.bank_flag.name
                        p = (pay.id, pay.pay_type, bf_name, pay.num_ctrl, pay.amount, active)
                    else:
                        p = (pay.id, pay.pay_type, '', '', pay.amount, active)
                    payforms.append(p)
                    _payforms.append(int(pay.id))

            session.kill_register = Storage()
            session.kill_register.evenid = evenid
            session.kill_register.key = str(CRYPT(digest_alg='sha1', salt=False)(request.vars.number)[0])
            session.kill_register.registers = _registers
            session.kill_register.payforms = _payforms
            session.kill_register.gsc = _gsc

            _event = Events[evenid]
            event = "%s - %s [%s - %s]" % (
                _event.activity.activity,
                _event.center.shortname,
                _event.start_date.strftime('%d/%m/%y'),
                _event.end_date.strftime('%d/%m/%y')
            )

            return dict(search=search,
                        info=True,
                        event=event,
                        event_status=_event.status,
                        title=title,
                        registers=registers,
                        payforms=payforms,
                        number=request.vars.number)
        else:
            return dict(search=search,
                        info=True,
                        event=None,
                        event_status=None,
                        title=T('There are no register or forms of payment.'),
                        registers=None,
                        payforms=None)

    return dict(search=search,
                info=False)


def kill_register():
    from gluon.custom_import import track_changes
    track_changes(True)
    import Reg_Utils as Reg

    if str(CRYPT(digest_alg='sha1', salt=False)(request.vars.number)[0]) != session.kill_register.key:
        redirect(URL('default', 'index'))

    if session.kill_register.gsc:
        for gsc in session.kill_register.gsc:
            evenid = session.kill_register.evenid
            Reg.update_credit_and_log(gsc[0], evenid, gsc[1], 'RPY')

    if session.kill_register.registers:
        registers = db(Register.id.belongs(session.kill_register.registers)).delete()

    if session.kill_register.payforms:
        payforms = db(Payment_Form.id.belongs(session.kill_register.payforms)).delete()

    del session.kill_register

    return 'location.href="%s";' % URL('default', 'kill_them_all')



# adjust bedroom alternative
@auth.requires_login()
@auth.requires(auth.has_membership('root'))
def adj_bedroom_alt():
    SCF = [act.id for act in db(Activities.activity_type=='SCF').select()]
    EVENTS = {
        ev.id:event_repr(ev) % ev for ev in db(
            (Events.center==2) & (Events.activity.belongs(SCF))
        ).select(orderby=~Events.id)
    }
    form = SQLFORM.factory(
        Field('event',
              requires=IS_IN_SET(EVENTS),
              label=T('event')
        ),
        submit_button=T('update')
    )
    if form.process().accepted:
        stays_on_center = db(Guest_Stay.center==2).select()

        registers = db(
            (Register.evenid==request.vars.event) & 
            (Register.credit==False) &
            (Register.is_active==True)
        ).select()

        for reg in registers:
            last_stay = [sty for sty in stays_on_center if sty.guesid == reg.guesid]
            if last_stay and last_stay[0].bedroom_alt != reg.bedroom:
                _stay = db(
                    (Guest_Stay.center==2) & (Guest_Stay.guesid==reg.guesid)
                ).select().first()
                _stay.update_record(bedroom_alt=reg.bedroom)

        redirect(URL('default', 'index'))

    return dict(form=form)