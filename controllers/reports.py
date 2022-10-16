# -*- coding: utf-8 -*-
from gluon.storage import Storage


# show cash balance
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def cash_balance():
    event = Events[request.vars.evenid]
    late = True if request.vars.late else False
    form = SQLFORM.factory(
        Field("days", "integer", label=T("days")),
        submit_button=T("day balance"),
    )
    form.add_button(
        T("total balance"),
        URL(
            "show_cash_balance",
            vars=dict(evenid=event.id, total=True, late=late),
        ),
    )
    form.element(_name="days")["_placeholder"] = T("how many days?")
    form.element("button")["_class"] = "btn btn-success btn-lg"
    form.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    form.element(_type="submit")["_onclick"] = (
        "dayBalance(document.getElementById('no_table_days').value,%s);"
        % event.id
    )
    if form.process().accepted:
        redirect(
            URL("reports", "show_cash_balance", vars=dict(**request.vars))
        )
    return dict(form=form)


# show cash balance
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def show_cash_balance():
    from datetime import datetime, timedelta

    evenid = request.vars.evenid
    event = Events[evenid] or redirect(URL("list"))
    query_late = (
        (Payment_Form.late == True)
        if request.vars.late == "True"
        else (Payment_Form.late == False)
    )
    dt1 = request.now
    total_cash_balance = True if request.vars.total == "True" else False
    late = True if request.vars.late == "True" else False
    if total_cash_balance:
        dt2 = event.created_on
    else:
        if request.vars.days:
            dt2 = dt1 - timedelta(days=int(request.vars.days))
        else:
            dt2 = dt1.replace(hour=0, minute=0, second=0)
    rows = db(
        (Payment_Form.evenid == evenid)
        & (Payment_Form.created_on >= dt2)
        & (Payment_Form.created_on < dt1)
        & (Payment_Form.centid == auth.user.center)
        & query_late
    ).select()
    event_records = db(Register.evenid == evenid).count()
    lates = db((Register.evenid == evenid) & (Register.late == True)).count()
    # preparing lists and variables
    generated_credit, used_credit, normal_entry = 0, 0, 0
    GENCRED = []
    CSH, CHK, PRE, DBT, CDT, DPT, TRF, GSC, CANCELED = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    csh, chk, pre, dbt, cdt, dpt, trf, canceled = 0, 0, 0, 0, 0, 0, 0, 0
    for r in rows:
        r.pay_type_str = str(PAYMENT_TYPES[r.pay_type])
        r.bank_flag_str = r.bank_flag.name if r.bank_flag else ""
        if r.credit:
            names = [nano_name(Guest[_gid].name) for _gid in r.guests]
            r.guest_name = "/".join(names) if len(names) > 1 else names[0]
            GENCRED.append(r)
            generated_credit += r.amount
        else:
            if not r.is_active:
                CANCELED.append(r)
                canceled += r.amount
            else:
                if r.pay_type == "GSC":
                    r.guest_name = shortname(r.guesid.name)
                    GSC.append(r)
                    used_credit += r.amount
                else:
                    if r.pay_type == "CSH":
                        CSH.append(r)
                        csh += r.amount
                    if r.pay_type == "CHK":
                        CHK.append(r)
                        chk += r.amount
                    if r.pay_type == "PRE":
                        PRE.append(r)
                        pre += r.amount
                    if r.pay_type == "DBT":
                        DBT.append(r)
                        dbt += r.amount
                    if r.pay_type == "CDT":
                        CDT.append(r)
                        cdt += r.amount
                    if r.pay_type == "DPT":
                        DPT.append(r)
                        dpt += r.amount
                    if r.pay_type == "TRF":
                        TRF.append(r)
                        trf += r.amount
                    normal_entry += r.amount
    GENCRED.sort(key=lambda row: row.created_on)
    return dict(
        event=event,
        normal=normal_entry,
        gencredit=generated_credit,
        usedcredit=used_credit,
        canceled=canceled,
        late=late,
        GENCRED=GENCRED,
        CANCELED=CANCELED,
        GSC=GSC,
        CSH=CSH,
        CHK=CHK,
        PRE=PRE,
        DBT=DBT,
        CDT=CDT,
        DPT=DPT,
        TRF=TRF,
        csh=csh,
        chk=chk,
        pre=pre,
        dbt=dbt,
        cdt=cdt,
        dpt=dpt,
        trf=trf,
        event_records=event_records,
        lates=lates,
        dt1=dt1,
        dt2=dt2,
        total_cash_balance=total_cash_balance,
    )


# payment by guest
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def payment_by_guest():
    from datetime import date

    event = Events[request.vars.evenid] or redirect(URL("list"))
    lates = len([r.id for r in event.register.select() if r.late])
    registers = (
        [
            r
            for r in event.register.select()
            if r.guesid.center == auth.user.center and r.late == True
        ]
        if request.vars.late
        else [
            r
            for r in event.register.select()
            if r.guesid.center == auth.user.center and r.late == False
        ]
    )
    GSCs = []
    for reg in registers:
        payforms = db(Payment_Form.id.belongs(reg.payforms)).select()
        gsc = [
            (int(pf.id), float(pf.amount), pf.credit)
            for pf in payforms
            if pf.pay_type == "GSC"
        ]
        if gsc:
            GSCs.append(gsc)
        _gsc = [
            (int(pf.id), float(pf.amount), pf.credit)
            for pf in payforms
            if pf.credit
        ]
        if _gsc:
            GSCs.append(_gsc)
        reg.payment_forms = [
            (
                pf.pay_type,
                float(pf.amount),
                pf.bank_flag.name if pf.bank_flag else "",
                pf.num_ctrl if pf.num_ctrl else "",
            )
            for pf in payforms
        ]
        reg.name = reg.guesid.name
        reg.name_sa = reg.guesid.name_sa
        reg.aspect = reg.guesid.aspect
        reg.age = get_age(reg.guesid.birthday)
    rows = sorted(registers, key=lambda k: k.name_sa)

    # cuidando do total do crédito gerado / usado
    GSCs = sorted(GSCs, key=lambda k: k[0])
    gsc_id, gsc_gen, gsc_use = 0, 0.0, 0.0
    for g in GSCs:
        if g[0][0] != gsc_id:
            if g[0][2]:
                gsc_gen += g[0][1]
                gsc_id = g[0][0]
            else:
                gsc_use += g[0][1]
                gsc_id = g[0][0]

    return dict(
        event=event,
        rows=rows,
        late=request.vars.late,
        event_records=len(registers),
        lates=lates,
        gsc_gen=gsc_gen,
        gsc_use=gsc_use,
    )


# register info
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def register_info():
    read = read_register(request.args(0))
    payforms, registers = read.payforms, read.registers
    guests, pays = [], []
    title = (
        T("credit launch details")
        if registers[0].credit
        else T("subscription details")
    )
    for n, reg in enumerate(registers):
        num = n + 1
        name = SPAN(shortname(reg.guesid.name))
        amount = reg.amount
        if not reg.is_active:
            num = SPAN(n + 1, _class="text-danger")
            name = DIV(
                shortname(reg.guesid.name),
                XML(" "),
                SPAN(T("canceled"), _class="label label-danger"),
                _class="text-danger",
            )
            amount = SPAN(reg.amount, _class="text-danger")
        g = [num, name, amount]
        guests.append(g)
    for n, pay in enumerate(payforms):
        if pay.pay_type == "GSC":
            gues_cred = "%(name)s" % Guest[pay.guesid]
            p = [n + 1, pay.pay_type, gues_cred, "", pay.amount]
        elif pay.bank_flag:
            bf_name = pay.bank_flag.name
            p = [n + 1, pay.pay_type, bf_name, pay.num_ctrl, pay.amount]
        else:
            p = [n + 1, pay.pay_type, "", "", pay.amount]
        pays.append(p)
    return DIV(
        DIV(
            DIV(
                A(
                    SPAN(XML("&times;"), **{"_aria-hidden": "true"}),
                    _type="button",
                    _class="close",
                    **{"_data-dismiss": "modal", "_aria-label": "Close"},
                ),
                H4(title, _class="modal-title"),
                _class="modal-header",
            ),
            DIV(
                EM(T("registered by"), XML(": ")),
                B(
                    registers[0].created_by.first_name,
                    XML(" "),
                    registers[0].created_by.last_name,
                ),
                XML("&nbsp;&nbsp;&nbsp;&nbsp;"),
                EM(T("on"), XML(": ")),
                B(registers[0].created_on.strftime("%d/%m/%y %H:%M:%S")),
                XML("&nbsp;&nbsp;&nbsp;&nbsp;"),
                EM(T("register"), XML(": ")),
                B(request.args(0)),
                HR(),
                TABLE(
                    THEAD(TR(TH("#"), TH(T("guest")), TH(T("value $")))),
                    TBODY(*[TR(*rows) for rows in guests]),
                    _class="table table-condensed",
                ),
                HR(),
                TABLE(
                    THEAD(
                        TR(
                            TH("#"),
                            TH(T("type")),
                            TH(T("details")),
                            TH(),
                            TH(T("value $")),
                        )
                    ),
                    TBODY(*[TR(*rows) for rows in pays]),
                    _class="table table-condensed",
                ),
                _class="modal-body",
            ),
            DIV(
                A(
                    T("close"),
                    _type="button",
                    _class="btn btn-primary",
                    **{"_data-dismiss": "modal"},
                ),
                _class="modal-footer",
            ),
            _class="modal-content",
        ),
        _class="modal-dialog",
        _role="document",
    )


# locate payment form
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def locate_payment_form():
    # search
    search = SQLFORM.factory(
        Field(
            "bflag",
            requires=IS_EMPTY_OR(IS_IN_DB(db, "bank_flag.id", "%(name)s")),
            label=T("bank/flag"),
        ),
        Field(
            "paytype",
            requires=IS_EMPTY_OR(IS_IN_SET(PAYMENT_TYPES)),
            label=T("type"),
        ),
        Field("ctrl", label=T("control")),
        Field("amount", label=T("$")),
        submit_button=T("locate"),
    )
    search.element(_name="ctrl")["_placeholder"] = T("control number")
    search.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if search.process().accepted:
        if (
            request.vars.bflag
            or request.vars.paytype
            or request.vars.ctrl
            or request.vars.amount
        ):
            queries = []
            if request.vars.bflag:
                queries.append((Payment_Form.bank_flag == request.vars.bflag))
            if request.vars.paytype:
                queries.append((Payment_Form.pay_type == request.vars.paytype))
            if request.vars.ctrl:
                ctrl = "%%%s%%" % request.vars.ctrl.lower()
                queries.append((Payment_Form.num_ctrl.lower().like(ctrl)))
            if request.vars.amount:
                queries.append(
                    (Payment_Form.amount == float(request.vars.amount))
                )
            query = reduce(lambda a, b: (a & b), queries)
            results = db(query).select()
            return dict(search=search, results=results)
        else:
            return dict(search=search, results=None)
    return dict(search=search, results=None)


# summary_to_print
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def summary_to_print():
    evenid = request.vars.evenid
    event = Events[evenid] or redirect(URL("list"))
    registers = event.register.select()
    payment_form = event.payment_form.select()
    present_stay = []
    for reg in registers:
        if reg.is_active and not reg.credit:
            stay_dict = dict(
                payforms=[
                    pf.pay_type
                    for pf in payment_form
                    if reg.guesid in pf.guests
                ],
                guesid=reg.guesid,
                name=reg.guesid.name,
                name_sa=reg.guesid.name_sa,
                amount=reg.amount,
                lodge=reg.lodge,
                no_stairs=reg.no_stairs,
                no_top_bunk=reg.no_top_bunk,
                arrival_date=reg.arrival_date,
                arrival_time=reg.arrival_time,
                staff=reg.staff,
                ps=reg.ps,
            )
            present_stay.append(stay_dict)
    rows = sorted(present_stay, key=lambda k: k["name_sa"])
    return dict(event=event, rows=rows)


# to stn
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def to_stn():
    response.view = "reports/link.html"
    evenid = request.vars.evenid
    event = Events[evenid]
    regists = db(
        (Register.evenid == evenid) & (Register.credit == False)
    ).select()
    registers = [r for r in regists if r.guesid.center == auth.user.center]
    pupils = []
    for r in sorted(registers, key=lambda k: k.guesid.name_sa):
        r.enroll = r.guesid.enrollment
        r.name = r.guesid.name
        r.value = '"R$ %s"' % ("%1.2f" % r.amount).replace(".", ",")
        if r.enroll:
            pupils.append(r)
    # creating a csv file
    filename = f"STN-FREQ_CONF-{event.start_date.strftime('%m%y')}.csv"
    _path = f"applications/register2event/static/docs/{filename}"
    with open(_path, "w", encoding="utf-8") as csv_file:
        csv_file.write(
            ",FREQUENCIAS NA CONFERENCIA - "
            + event.start_date.strftime("%B - %Y")
            + "\n\n"
        )
        csv_file.write("MATRIC.,NOME,VALOR (R$)\n")
        for p in pupils:
            row = f"{str(p.enroll)},{str(p.name)},{p.value}\n"
            print(row)
            csv_file.write(row)

    link = A(T("get your file"), _href=URL("static", "docs/" + filename))

    return dict(link=link)


# frequencies
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def frequencies():
    response.view = "reports/link.html"
    evenid = request.vars.evenid
    event = Events[evenid]
    regists = db(
        (Register.evenid == evenid) & (Register.credit == False)
    ).select()
    registers = [r for r in regists if r.guesid.center == auth.user.center]
    pupils, guests = [], []
    for r in sorted(registers, key=lambda k: k.guesid.name_sa):
        r.enroll = r.guesid.enrollment
        r.name = r.guesid.name_sa
        if r.enroll:
            try:
                pupils.append((int(r.enroll), r.name))
            except:
                guests.append((r.enroll, r.name))
    # creating a csv file
    filename = "FREQ_CONF-%s.txt" % event.start_date.strftime("%m%y")
    _path = f"applications/register2event/static/docs/{filename}"
    with open(_path, "w", encoding="utf-8") as txt_file:
        txt_file.write(
            "FREQUENCIAS NA CONFERENCIA - "
            + event.start_date.strftime("%B - %Y")
            + "\n\n"
        )

        txt_file.write("ALUNOS (so a matricula)\n")
        txt_file.write("-" * 80 + "\n")
        for p in pupils:
            txt_file.write(str(p[0]) + ", ")

        txt_file.write("\n\nALUNOS\n")
        txt_file.write("-" * 80 + "\n")
        for p in pupils:
            txt_file.write(str(p[0]) + " - " + p[1] + "\n")

        txt_file.write("\n\nCONVIDADOS\n")
        txt_file.write("-" * 80 + "\n")
        for g in guests:
            txt_file.write(g[0] + " - " + g[1] + "\n")

    link = A(T("get your file"), _href=URL("static", "docs/" + filename))

    return dict(link=link)


#  admin reports
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def guests_per_bedroom():
    evenid = request.vars.evenid
    bedrooms = sorted(get_bedrooms(evenid), key=lambda k: k[0])
    event = Events[evenid]
    regs = db(
        (Register.evenid == evenid)
        & (Register.credit == False)
        & (Register.is_active == True)
    ).select()
    registers = sorted(regs, key=lambda k: k["guesid"])
    for r in registers:
        r.name = r.guesid.name
        r.name_sa = r.guesid.name_sa
        if r.lodge == "LDG":
            _lodge = filter(lambda x: x[0] == r.guesid, bedrooms)
            if _lodge:
                building = Bedroom[_lodge[0][1]]
                r.bedroom_details = (
                    _lodge[0][3],
                    _lodge[0][2],
                    str(building.builid.building),
                )
                bedrooms.remove(_lodge[0])
            else:
                r.bedroom_details = "not_lodge"
        else:
            r.bedroom_details = "out_of_center"
    rows = sorted(registers, key=lambda k: k["name_sa"])

    return dict(event=event, rows=rows)


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def map_of_bedrooms():
    evenid = request.vars.evenid
    bedrooms = sorted(get_bedrooms(evenid), key=lambda k: k[0])
    event = Events[evenid]
    regs = db(
        (Register.evenid == evenid)
        & (Register.credit == False)
        & (Register.is_active == True)
        & (Register.lodge == "LDG")
    ).select()
    registers = sorted(regs, key=lambda k: k["guesid"])
    for r in registers:
        r.name = r.guesid.name
        r.name_sa = r.guesid.name_sa
        _lodge = filter(lambda x: x[0] == r.guesid, bedrooms)
        if _lodge:
            building = Bedroom[_lodge[0][1]]
            r.bedroom_details = (
                _lodge[0][3],
                _lodge[0][2],
                str(building.builid.building),
            )
            bedrooms.remove(_lodge[0])
        else:
            r.bedroom_details = "not_lodge"
    rows = sorted(registers, key=lambda k: k["bedroom"])

    return dict(event=event, rows=rows)


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def guests_per_staff():
    event = Events[request.vars.evenid]
    rows = dict_registers(event)
    rows.sort(key=lambda k: k.name_sa)
    rows.sort(key=lambda k: k.staff, reverse=True)

    return dict(event=event, rows=rows)


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def guests_per_aspect():
    event = Events[request.vars.evenid]
    rows = dict_registers(event)
    rows.sort(key=lambda k: k.name_sa)
    rows.sort(key=lambda k: k.aspect)

    return dict(event=event, rows=rows)


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def pupils_guests():
    event = Events[request.vars.evenid]
    rows = [reg for reg in dict_registers(event) if reg.aspect == "PG"]
    rows.sort(key=lambda k: k.name_sa)

    return dict(event=event, rows=rows)


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def pupils_guests_center():
    event = Events[request.vars.evenid]
    rows = [
        reg
        for reg in dict_registers(event)
        if reg.aspect == "PG" and reg.centid == auth.user.center
    ]
    rows.sort(key=lambda k: k.name_sa)

    return dict(event=event, rows=rows)


@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def total_by_center():
    event = Events[request.vars.evenid]
    rows = [r for r in dict_registers(event) if r.centid == auth.user.center]
    rows.sort(key=lambda k: k.pg_type)
    center = dict_center_totals(rows)

    return dict(event=event, _center=center)


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def total_by_centers():
    event = Events[request.vars.evenid]
    rows = dict_registers(event)
    rows.sort(key=lambda k: k.center)
    centers = dict_centers_totals(rows)

    return dict(event=event, centers=centers)


def dict_registers(event):
    # from datetime import date
    registers = db(
        (Register.evenid == event.id)
        & (Register.credit == False)
        & (Register.is_active == True)
    ).select()
    rows = []
    for r in registers:
        age = get_age(r.guesid.birthday)
        guest = Storage(
            id=int(r.id),
            name=str(r.guesid.name),
            name_sa=str(r.guesid.name_sa),
            age=age,
            aspect=str(r.guesid.aspect) if r.guesid.aspect else None,
            payed=float(r.amount),
            staff=str(r.staff) if r.staff else None,
            description=str(r.description) if r.description else None,
            city="%s (%s)" % (r.guesid.city, r.guesid.country),
            center=center_abbr % r.guesid.center,
            center_repr=center_repr % r.guesid.center,
            centid=int(r.guesid.center),
            ps=r.guesid.ps if r.guesid.ps else None,
        )
        if guest.aspect == "PG":
            guest.expected = 0.0
            guest.pg_type = "pgst"
        elif (not age or age >= 18) and r.amount == 0.0:
            guest.expected = 0.0
            guest.pg_type = "free"
        elif not age or age >= 18:
            guest.expected = float(event.min_value)
            guest.pg_type = "full"
        elif age >= 7 and age < 18:
            guest.expected = float(event.min_value) / 2
            guest.pg_type = "half"
        elif age < 7:
            guest.expected = 0.0
            guest.pg_type = "free"
        rows.append(guest)

    return rows


def dict_center_totals(rows):
    center = Storage(
        center=rows[0].center_repr,
        half_payed=0.0,
        half_expected=0.0,
        full_payed=0.0,
        full_expected=0.0,
        free_payed=0.0,
        free_expected=0.0,
        pgst_payed=0.0,
        pgst_expected=0.0,
        full=0,
        half=0,
        free=0,
        pgst=0,
    )
    for r in rows:
        if r.pg_type == "full":
            center.full += 1
            center.full_payed += r.payed
            center.full_expected += r.expected
        elif r.pg_type == "half":
            center.half += 1
            center.half_payed += r.payed
            center.half_expected += r.expected
        elif r.pg_type == "free":
            center.free += 1
            center.free_payed += r.payed
        elif r.pg_type == "pgst":
            center.pgst += 1
            center.pgst_payed += r.payed

    return center


def dict_centers_totals(rows):
    centid, _ids = 0, []
    for r in rows:
        if centid != r.centid:
            _ids.append(r.centid)
            centid = r.centid
    centers = []
    for _id in _ids:
        _rows = [r for r in rows if r.centid == _id]
        _center = None
        full, half, free, pgst = (
            0,
            0,
            0,
            0,
        )
        full_payed, full_expected = 0.0, 0.0
        half_payed, half_expected = 0.0, 0.0
        free_payed, free_expected = 0.0, 0.0
        pgst_payed, pgst_expected = 0.0, 0.0
        for _r in _rows:
            if _center != _r.center_repr:
                _center = _r.center_repr
            if _r.pg_type == "full":
                full += 1
                full_payed += _r.payed
                full_expected += _r.expected
            elif _r.pg_type == "half":
                half += 1
                half_payed += _r.payed
                half_expected += _r.expected
            elif _r.pg_type == "free":
                free += 1
                free_payed += _r.payed
            elif _r.pg_type == "pgst":
                pgst += 1
                pgst_payed += _r.payed
        center = Storage(
            center=_center,
            full=full,
            full_payed=full_payed,
            full_expected=full_expected,
            half=half,
            half_payed=half_payed,
            half_expected=half_expected,
            free=free,
            free_payed=free_payed,
            free_expected=free_expected,
            pgst=pgst,
            pgst_payed=pgst_payed,
            pgst_expected=pgst_expected,
        )
        centers.append(center)

    return centers


def conf_days(d1, d2):
    if d2 < d1:
        d2 += 7

    return (d2 - d1) + 1


# guests_per_meals
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def guests_per_meals():
    evenid = request.vars.evenid
    event = Events[evenid] or redirect(URL("list"))
    registers = event.register.select()
    present_stay = []
    for reg in registers:
        if reg.is_active and not reg.credit:
            stay_dict = dict(
                guesid=reg.guesid,
                name=reg.guesid.name,
                lodge=reg.lodge,
                a_date=reg.arrival_date,
                a_time=reg.arrival_time,
            )
            present_stay.append(stay_dict)
    rows = sorted(present_stay, key=lambda k: k["a_date"])
    # counters
    M1, M2, M3, M4, M5, M6, M7, M8 = 0, 0, 0, 0, 0, 0, 0, 0
    HB1, HB2, HB3 = 0, 0, 0
    for r in rows:
        if r["a_date"] == "D0" and r["a_time"] == "BB":
            M1 += 1  # eve lunch
            if r["lodge"] in ["HTL", "HSE"]:
                HB1 += 1
        elif r["a_date"] == "D0" and r["a_time"] == "BL":
            M1 += 1  # eve lunch
            if r["lodge"] in ["HTL", "HSE"]:
                HB1 += 1
        elif r["a_date"] == "D0" and r["a_time"] == "BD":
            M2 += 1  # eve dinner
            if r["lodge"] in ["HTL", "HSE"]:
                HB1 += 1
        elif r["a_date"] == "D0" and r["a_time"] == "AD":
            M3 += 1  # day1 breakfast
            if r["lodge"] in ["HTL", "HSE"]:
                HB1 += 1
        elif r["a_date"] == "D1" and r["a_time"] == "BB":
            M3 += 1  # day1 breakfast
            if r["lodge"] in ["HTL", "HSE"]:
                HB1 += 1
        elif r["a_date"] == "D1" and r["a_time"] == "BL":
            M4 += 1  # day1 lunch
            if r["lodge"] in ["HTL", "HSE"]:
                HB2 += 1
        elif r["a_date"] == "D1" and r["a_time"] == "BD":
            M5 += 1  # day1 dinner
            if r["lodge"] in ["HTL", "HSE"]:
                HB2 += 1
        elif r["a_date"] == "D1" and r["a_time"] == "AD":
            M6 += 1  # day2 breakfast
            if r["lodge"] in ["HTL", "HSE"]:
                HB2 += 1
        elif r["a_date"] == "D2" and r["a_time"] == "BB":
            M6 += 1  # day2 breakfast
            if r["lodge"] in ["HTL", "HSE"]:
                HB2 += 1
        elif r["a_date"] == "D2" and r["a_time"] == "BL":
            M7 += 1  # day2 lunch
            if r["lodge"] in ["HTL", "HSE"]:
                HB3 += 1
        elif r["a_date"] == "D2" and r["a_time"] == "BD":
            M8 += 1  # day2 dinner (if 3 days conference)
            if r["lodge"] in ["HTL", "HSE"]:
                HB3 += 1
    meals = [
        M1,
        (M1 + M2),
        (M1 + M2 + M3),
        (M1 + M2 + M3 + M4),
        (M1 + M2 + M3 + M4 + M5),
        (M1 + M2 + M3 + M4 + M5 + M6),
        (M1 + M2 + M3 + M4 + M5 + M6 + M7),
        (M1 + M2 + M3 + M4 + M5 + M6 + M7 + M8),
    ]
    guests_out = [HB1, (HB1 + HB2), (HB1 + HB2 + HB3)]

    return dict(
        event=event,
        conf_days=conf_days(
            event.start_date.weekday(), event.end_date.weekday()
        ),
        rows=len(rows),
        meals=meals,
        guests_out=guests_out,
    )
