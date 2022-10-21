# -*- coding: utf-8 -*-


# new
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def new():
    new = SQLFORM(Guest, submit_button="add")
    if auth.has_membership("root") or auth.has_membership("admin"):
        new.element("option", _value=int(auth.user.center))[
            "_selected"
        ] = "selected"
    elif auth.user.center:
        new.element(_id="guest_center__row")["_style"] = "display:none;"
        new.element("option", _value=int(auth.user.center))[
            "_selected"
        ] = "selected"
    if not auth.has_membership("root"):
        new.element(_id="guest_credit__row")["_style"] = "display:none;"
    new.element(_name="ps")["_rows"] = 1
    new.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if new.process().accepted:
        guesid = int(new.process().vars.id)
        if request.vars.reg:
            redirect(URL("register", "confirm_guest", vars={"guesid": guesid}))
        redirect(URL("show", vars={"guesid": guesid, "tab": "home"}))
    return dict(form=new)


# edit
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def edit():
    guesid = request.vars.guesid
    edit = SQLFORM(Guest, guesid, submit_button="update")
    edit.element(_id="guest_id__row")["_style"] = "display:none;"
    if auth.has_membership("root"):
        edit.element(_id="guest_credit__row")["_style"] = "display:none;"
    edit.element(_name="ps")["_rows"] = 1
    edit.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if edit.process().accepted:
        if request.vars.on_reg:
            redirect(URL("register", "confirm_guest", vars={"guesid": guesid}))
        redirect(URL("show", vars={"guesid": guesid, "tab": "home"}))
    return dict(form=edit, guest=guesid)


# new_guest_stay
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def new_stay():
    new_stay = SQLFORM(Guest_Stay, submit_button="add")
    stay_adjust_to_view(new_stay)
    if new_stay.process().accepted:
        if request.vars.on_reg:
            vars = {"guesid": request.vars.guest_id}
            redirect(URL("register", "confirm_guest", vars={**vars}))
        else:
            vars = {
                "guesid": new_stay.process().vars.guesid,
                "tab": "stay",
            }
            redirect(URL("show", vars={**vars}))
    return dict(form=new_stay, guesid=request.vars.guesid)


# edit stay
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def edit_stay():
    guest = Guest[request.vars.guest_id]
    edit_stay = SQLFORM(
        Guest_Stay, request.vars.stayid, submit_button="update"
    )
    stay_adjust_to_view(edit_stay, edit=True)
    if edit_stay.process().accepted:
        if request.vars.on_reg:
            vars = {"guesid": request.vars.guest_id}
            redirect(URL("register", "confirm_guest", vars={**vars}))
        else:
            vars = {"guesid": request.vars.guest_id, "tab": "stay"}
            redirect(URL("show", vars={**vars}))

    return dict(form=edit_stay, guest=guest.name, stay=request.vars.stayid)


# helper to stay adjust to view ###############################################
def stay_adjust_to_view(form, edit=False):
    if request.vars.guest_id:
        elm_guesid = form.element(_name="guesid")
        elm_guesid.element("option", _value=request.vars.guest_id)[
            "_selected"
        ] = "selected"
    if request.vars.center_id:
        elm_centid = form.element(_name="center")
        elm_centid.element("option", _value=request.vars.center_id)[
            "_selected"
        ] = "selected"
        form.element(_id="guest_stay_center__row")["_style"] = "display:none;"
    form.element(_id="guest_stay_guesid__row")["_style"] = "display:none;"
    form.element(_id="guest_stay_bedroom__row")["_style"] = "display:none;"
    form.element(_id="guest_stay_bedroom_alt__row")["_style"] = "display:none;"
    form.element(_id="guest_stay_description__row")["_style"] = "display:none;"
    form.element(_name="ps")["_rows"] = 1
    form.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if edit:
        form.element(_id="guest_stay_id__row")["_style"] = "display:none;"
        if auth.has_membership("root") or auth.has_membership("admin"):
            form.element(_id="guest_stay_bedroom__row")[
                "_style"
            ] = "display:block;"  # esconder
            form.element(_id="guest_stay_bedroom_alt__row")[
                "_style"
            ] = "display:block;"  # esconder
            form.element(_id="guest_stay_description__row")[
                "_style"
            ] = "display:block;"
            form.element(_name="description")["_rows"] = 1


# list
@auth.requires_login()
def list():
    # if exists session.mapp or session.register delete it
    if session.mapp or session.register:
        clear_session()
    # search
    search = FORM(
        INPUT(_name="term", _class="form-control"),
        INPUT(_type="submit", _class="btn btn-default", _value=T("go")),
        _class="form-inline navbar-left",
    )
    search.element(_name="term")["_style"] = "width: 200px;"
    search.element(_name="term")["_placeholder"] = T("search")

    # paginator
    from paginator import Paginator, PaginateSelector, PaginateInfo

    paginate_selector = PaginateSelector(anchor="main")
    # select query
    if request.vars.term or request.vars.term == "":
        term = request.vars.term
    elif request.vars.t:
        term = request.vars.t
    else:
        term = request.vars.term
    if not term:
        query = (
            (Guest.id > 0)
            & (Guest.is_active == True)
            & (Guest.center == auth.user.center)
        )
        extr_vars = {"t": ""}
    else:
        if term.isdigit():
            query = (Guest.enrollment == term) & (
                Guest.center == auth.user.center
            )
            extr_vars = {"t": ""}
        else:
            like_term = des("%%%s%%" % term.lower())
            query = (
                (Guest.name_sa.lower().like(like_term))
                & (Guest.is_active == True)
                & (Guest.center == auth.user.center)
            )
            extr_vars = {"t": term}
    paginator = Paginator(
        paginate=paginate_selector.paginate,
        anchor="main",
        extra_vars=extr_vars,
        renderstyle=False,
    )
    paginator.records = db(query).count()
    paginate_info = PaginateInfo(
        paginator.page, paginator.paginate, paginator.records
    )
    rows = db(query).select(limitby=paginator.limitby(), orderby=Guest.name_sa)

    return dict(
        search=search.process(),
        rows=rows,
        records=paginator.records,
        paginator=str(paginator),
        paginate_selector=paginate_selector,
        paginate_info=paginate_info,
    )


# show
@auth.requires_login()
def show():
    from datetime import date

    guesid = request.vars.guesid
    guest = Guest[guesid] or redirect(URL("list"))
    guest.age = get_age(guest.birthday) if guest.birthday else ""
    stays = db(Guest_Stay.guesid == guesid).select() or None
    credit_log = guest.credit_log.select(orderby=~Credit_Log.id)
    historic = db(Register.guesid == guesid).select(
        orderby=~Register.created_on
    )
    tab = request.vars.tab if request.vars.tab else "home"
    return dict(
        guest=guest,
        stays=stays,
        credit_log=credit_log,
        historic=historic,
        tab_pres=tab,
    )


# delete
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def delete():
    guesid = int(request.args(0)) or redirect(URL("list"))
    guest = Guest[guesid]
    if db(Register.guesid == guesid).select():
        guest.update_record(is_active=False)
        return "window.location = document.referrer;"
    else:
        guest.delete_record()
        return "window.location = document.referrer;"


# delete stay
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def delete_stay():
    stay = Guest_Stay[request.args(0)]
    guesid = stay.guesid
    if stay:
        stay.delete_record()
        db.commit()
        return "window.location = document.referrer;"
