# -*- coding: utf-8 -*-


# new
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def new():
    new = SQLFORM(Events, submit_button="add")
    if auth.has_membership("admin"):
        new.element(_id="events_center__row")["_style"] = "display:none;"
        new.element("option", _value=int(auth.user.center))[
            "_selected"
        ] = "selected"
    new.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    new.element(_name="description")["_rows"] = 1
    if new.process().accepted:
        from gluon.custom_import import track_changes
        import Mapp_Utils as Mapp

        track_changes(True)

        evenid = int(new.process().vars.id)
        Mapp.update_mapping(evenid)
        redirect(URL("show", vars={"evenid": evenid}))
    return dict(form=new)


# edit
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def edit():
    evenid = request.vars.evenid
    event = Events[evenid] or redirect(URL("list"))
    edit = SQLFORM(Events, event.id, submit_button="update")
    edit.element(_id="events_id__row")["_style"] = "display:none;"
    edit.element(_name="description")["_rows"] = 1
    edit.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if edit.process().accepted:
        redirect(URL("show", vars={"evenid": evenid}))
    return dict(form=edit, event=evenid)


# list
@auth.requires_login()
def list():
    from gluon import current

    # if exists session.mapp or session.register delete it
    if session.mapp or session.register:
        clear_session()
    session.referer = []
    # search
    search = FORM(
        INPUT(_name="term", _class="form-control"),
        INPUT(_type="submit", _class="btn btn-default", _value=T("go")),
        _class="form-inline navbar-left",
    )
    search.element(_name="term")["_style"] = "width: 220px;"
    search.element(_name="term")["_placeholder"] = T("MM/YYYY")
    # paginator
    from paginator import Paginator, PaginateSelector, PaginateInfo

    paginate_selector = PaginateSelector(anchor="main")
    # select query
    qry = (Events.id > 0) & (Events.is_active == True)
    if request.vars.term == "":
        qry = (Events.id > 0) & (Events.is_active == True)
        current.request.get_vars.page = 1
        paginator = Paginator(
            paginate=paginate_selector.paginate,
            extra_vars={"t": ""},
            anchor="main",
            renderstyle=False,
        )
    elif request.vars.term:
        if "/" in request.vars.term:
            term = request.vars.term.split("/")
            qry = (Events.start_date.month() == term[0]) & (
                Events.start_date.year() == term[1]
            )
        current.request.get_vars.page = 1
        paginator = Paginator(
            paginate=paginate_selector.paginate,
            extra_vars={"t": request.vars.term},
            anchor="main",
            renderstyle=False,
        )
    elif request.vars.t:
        term = request.vars.t.split("/")
        qry = (Events.start_date.month() == term[0]) & (
            Events.start_date.year() == term[1]
        )
        paginator = Paginator(
            paginate=paginate_selector.paginate,
            extra_vars={"t": request.vars.t},
            anchor="main",
            renderstyle=False,
        )
    else:
        paginator = Paginator(
            paginate=paginate_selector.paginate,
            anchor="main",
            renderstyle=False,
        )
    paginator.records = db(qry).count()
    paginate_info = PaginateInfo(
        paginator.page, paginator.paginate, paginator.records
    )

    rows = db(qry).select(
        orderby=~Events.start_date, limitby=paginator.limitby()
    )
    for r in rows:
        r.guests = db(
            (Register.evenid == r.id)
            & (Register.is_active == True)
            & (Register.credit == False)
        ).count()
        r.centid = r.center
    return dict(
        search=search.process(),
        rows=rows,
        records=paginator.records,
        paginator=str(paginator),
        paginate_info=paginate_info,
        paginate_selector=paginate_selector,
    )


# show
@auth.requires_login()
def show():
    from datetime import date

    clear_session()
    evenid = request.vars.evenid
    admin_view = request.vars.admin_view
    view_credits = True if request.vars.view_credits == "True" else False
    event = Events[evenid] or redirect(URL("list"))
    total_registers = len(
        [
            r
            for r in event.register.select()
            if (r.credit == True if view_credits else r.credit == False)
            and r.is_active == True
        ]
    )

    if auth.has_membership("root") or (
        auth.has_membership("admin") and auth.user.center == event.center.id
    ):
        if admin_view:
            session.admin_view = True
            registers = [
                r
                for r in event.register.select()
                if (r.credit == True if view_credits else r.credit == False)
            ]
            if request.vars._formkey:
                if request.vars.unalloc:
                    registers = [
                        r
                        for r in registers
                        if not r.bedroom and r.lodge == "LDG" and r.is_active
                    ]
            else:
                if request.get_vars.unall:
                    registers = [
                        r
                        for r in registers
                        if not r.bedroom and r.lodge == "LDG" and r.is_active
                    ]
        else:
            if session.admin_view:
                del session["admin_view"]
            registers = [
                r
                for r in event.register.select()
                if r.guesid.center == auth.user.center
                and (r.credit == True if view_credits else r.credit == False)
            ]
    else:
        registers = [
            r
            for r in event.register.select()
            if r.guesid.center == auth.user.center
            and (r.credit == True if view_credits else r.credit == False)
        ]
    ids = [str(g.guesid) for g in registers]
    lates = [g.guesid for g in registers if g.late]
    # search
    search = FORM(
        DIV(INPUT(_name="term", _class="form-control"), _class="form-group"),
        INPUT(_type="submit", _class="btn btn-info", _value=T("search")),
        DIV(
            LABEL(INPUT(_name="unalloc", _type="checkbox"), T("not hosteds")),
            _class="checkbox",
            _id="unalloc",
        ),
        _class="form-inline navbar-left",
    )
    if not admin_view:
        search.element(_id="unalloc")["_style"] = "display:none;"
    search.element(_name="term")["_style"] = "width: 18rem;"
    search.element(_name="term")["_placeholder"] = T("search")

    # select query
    extr_vars = {}
    term = None
    if request.vars._formkey:
        request.vars.page = 1
        request.get_vars.page = 1
        if request.vars.t:
            del request.vars.t
            del request.get_vars.t
        if request.vars.unall:
            del request.vars.unall
            del request.get_vars.unall

        if request.vars.term:
            term = request.vars.term
            extr_vars.update({"t": term})
        if request.vars.unalloc:
            extr_vars.update({"unall": True})

    else:
        if request.vars.t:
            term = request.vars.t

    if not term:
        gquery = Guest.id.belongs(ids)
    else:
        like_term = des("%%%s%%" % term.lower())
        gquery = (Guest.name_sa.lower().like(like_term)) & (
            Guest.id.belongs(ids)
        )

    # paginator
    from paginator import Paginator, PaginateSelector, PaginateInfo

    paginate_selector = PaginateSelector(anchor="main")
    paginator = Paginator(
        paginate=paginate_selector.paginate,
        extra_vars=extr_vars,
        anchor="main",
        renderstyle=False,
    )
    paginator.records = db(gquery).count()
    paginate_info = PaginateInfo(
        paginator.page, paginator.paginate, paginator.records
    )
    rows = db(gquery).select(
        orderby=Guest.name_sa, limitby=paginator.limitby()
    )
    # records = db(gquery).count()
    rows = db(gquery).select(orderby=Guest.name_sa, limitby=(0, 10))
    for r in rows:
        for reg in registers:
            if int(r.id) == reg.guesid:
                r.lodge = reg.lodge
                r.no_stairs = reg.no_stairs
                r.no_top_bunk = reg.no_top_bunk
                r.arrival_date = reg.arrival_date
                r.arrival_time = reg.arrival_time
                r.staff = reg.staff
                r.description = reg.description
                r.ps = reg.ps
                r.amount = reg.amount
                r.late = True if reg.late == True else False
                r.regid = reg.id
                r.is_active = reg.is_active
                if reg.lodge == "LDG" and reg.bedroom:
                    _bedroom = Bedroom[reg.bedroom]
                    bedroom = (_bedroom.bedroom, _bedroom.builid.building)
                    r.bedroom = bedroom
                elif reg.lodge == "LDG" and not reg.bedroom:
                    r.bedroom = "unalloc"
                else:
                    r.bedroom = None
                r.age = (
                    get_age(reg.guesid.birthday)
                    if reg.guesid.birthday
                    else None
                )

    return dict(
        search=search.process(),
        event=event,
        rows=rows,
        # records=records,
        records=paginator.records,
        paginator=str(paginator),
        paginate_selector=paginate_selector,
        paginate_info=paginate_info,
        event_records=len(ids),
        lates=lates,
        view_credits=view_credits,
        term=term,
        total_registers=total_registers,
        admin_view=admin_view,
    )


# delete
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def delete():
    evenid = int(request.args(0)) or redirect(URL("list"))
    if db(Register.evenid == evenid).select():
        event = Events[evenid]
        event.update_record(is_active=False)
        mapp = db(Bedrooms_mapping.evenid == evenid).select().first()
        mapp.update_record(is_active=False)
        return "window.location = document.referrer;"
    else:
        db(Events.id == evenid).delete()
        db(Bedrooms_mapping.evenid == evenid).delete()
        return 'location.href="%s";' % URL("events", "list")


# event status (on / off)
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def event_on_off():
    event = Events[request.vars.evenid]
    if event.status == "OPN":
        event.update_record(status="CLS")
    else:
        event.update_record(status="OPN")
    return "document.location.reload(true)"
