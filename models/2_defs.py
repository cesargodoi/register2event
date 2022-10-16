from datetime import date
from gluon.storage import Storage


# useful functions ############################################################
def get_age(birthday):
    return int((date.today() - birthday).days // 365) if birthday else None


def clear_session():
    if session.register or session.register == "":
        del session.register
    if session.mapp or session.mapp == "":
        del session.mapp
    if (
        session.unenroll_credit_multiple
        or session.unenroll_credit_multiple == ""
    ):
        del session.unenroll_credit_multiple


def read_register(num, pf=False):
    if pf:
        m2m_rows = db(Register_Payment_Form.payfid == num).select()
        if not m2m_rows:
            return False
    else:
        reg = Register[num]
        if not reg:
            return False
        m2m_rows = db(
            Register_Payment_Form.payfid.belongs(reg.payforms)
        ).select()
        if not m2m_rows:
            return False
    regids = set(r.regid for r in m2m_rows)
    payfids = set(r.payfid for r in m2m_rows)
    return Storage(
        registers=db(db.register.id.belongs(regids)).select(),
        payforms=db(db.payment_form.id.belongs(payfids)).select(),
        reg2pay=m2m_rows,
    )


def step1_add_or_edit(guesid):
    session.register.paying.append(
        {"guest": guesid, "amount": ("%1.2f" % 0.0)}
    )
    redirect(URL("register", "register_step2"))


def CKeditor(field, value):
    return TEXTAREA(
        _id=str(field).replace(".", "_"),
        _name=field.name,
        _class="text ckeditor",
        value=value,
        _cols=80,
        _rows=10,
    )


def phone_format(n):
    try:
        if ("-" in n) or (" " in n) or ("_" in n) or ("." in n):
            n = n.replace("-", "")
            n = n.replace(" ", "")
            n = n.replace("_", "")
            n = n.replace(".", "")
        if n != "":
            if len(n) == 11:
                n = n[:2] + " " + n[2:7] + "." + n[7:]
            elif len(n) == 10 or len(n) > 11 or len(n) < 10:
                n = n[:2] + " " + n[2:6] + "." + n[6:]
    except:
        n = ""
    return n


def des(txt, codif="utf-8"):
    from unicodedata import normalize

    if not isinstance(txt, str):
        txt = str(txt)
    return (
        normalize("NFKD", txt)
        .encode("ASCII", "ignore")
        .decode("ASCII")
        .lower()
    )


def back():
    http_ref = request.env.http_referer
    ref = http_ref.split("/")
    referer = "/" + "/".join(ref[3:])
    if not "_formkey=" in referer:
        if request.env.request_uri != referer:
            try:
                if not referer in session.referer:
                    session.referer.append(referer)
            except:
                session.referer = [referer]
        try:
            if request.env.request_uri == session.referer[-2]:
                session.referer.pop(-1)
                session.referer.pop(-1)
        except:
            session.referer
    back = "/".join(ref[:3]) + session.referer[-1]
    return back


def shortname(item, max_len=25):
    if len(item) > max_len:
        item_split = item.split(" ")
        if len(item_split) > 2:
            order = [item_split[0], item_split[1]]
            next_to_short = 2
            names_to_shortname = len(item_split) - 3
            if len(item_split[1]) <= 3:
                order.append(item_split[2])
                next_to_short = 3
                names_to_shortname = len(item_split) - 4
            for nts in range(names_to_shortname):
                name_to_short = item_split[next_to_short + nts]
                if len(name_to_short) > 3:
                    abbr = "%s." % name_to_short[0]
                    order.append(abbr)
            order.append(item_split[-1])
            return " ".join(order)
        else:
            return item
    else:
        return item


def shortname_reports(item, max_len=12):
    if len(item) > max_len and len(item) > 2:
        item_split = item.split(" ")
        new_name = [item_split[0]]
        # abreviar
        for n in range(len(item_split) - 1):
            if n < len(item_split) - 2:
                if len(item_split[n + 1]) > 3:
                    abbr = "%s." % item_split[n + 1][0]
                    new_name.append(abbr)
                else:
                    new_name.append(item_split[n + 1])
            else:
                new_name.append(item_split[n + 1])
        return " ".join(new_name)
    else:
        return item


def nano_name(item):
    _split = item.split(" ")
    return "%s %s." % (_split[0], _split[-1][0])


def log(function):
    def wrapper_function():
        from datetime import datetime

        date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        url = request.url.split("/")
        try:
            args = [arg for arg in request.args]
        except:
            args = ""
        try:
            kwargs = [
                "%s=%s" % (kwarg, request.vars[kwarg])
                for kwarg in request.vars
                if not kwarg.startswith("_form")
            ]
        except:
            kwargs = ""
        txt = "%s - %s(%s) --> C=%s F=%s args=%s vars=%s \n" % (
            date,
            auth.user.email,
            auth.user_groups.values()[0],
            url[2],
            url[3],
            str(args),
            str(kwargs),
        )
        with open(
            "applications/register2event/log_register2event.txt", "a"
        ) as log:
            log.write(txt)
        return function()

    return wrapper_function


def test_performance(function):
    def wrapper_function():
        import mem_profile
        import time

        print("-" * 80)
        print(
            "Memory (Before): {}Mb".format(mem_profile.memory_usage_psutil())
        )
        t1 = time.clock()
        function()
        t2 = time.clock()
        print(
            "Memory (After) : {}Mb".format(mem_profile.memory_usage_psutil())
        )
        print("Took {} Seconds".format(t2 - t1))
        return function()

    return wrapper_function


def str_to_date(string):
    from datetime import datetime

    if "/" in string:
        separator = "/"
    else:
        separator = "-"
    dt_split = string.split(separator)
    if len(dt_split[0]) == 2:
        date = datetime(int(dt_split[2]), int(dt_split[1]), int(dt_split[0]))
    else:
        date = datetime(int(dt_split[0]), int(dt_split[1]), int(dt_split[2]))
    return date


def center_abbr(center):
    center_split = center.split(" - ")
    abbr = ""
    if len(center_split[0].split()) > 1:
        for word in center_split[0].split():
            if len(word) > 2:
                abbr += word[0].upper()
    else:
        abbr = center_split[0]
    return abbr


def adjust_register_payforms(registers, payforms, evenid):
    for r in registers:
        for pf in payforms:
            db.register_payment_form.insert(regid=r, payfid=pf, evenid=evenid)


def adjust_bedroom_mapp(evenid):
    mapping = db(Bedrooms_mapping.evenid == evenid).select().first()
    regs = db(Register.evenid == evenid).select()
    registers = [
        int(r.guesid)
        for r in regs
        if r.lodge == "LDG" and not r.credit and r.is_active
    ]
    for bedroom in mapping.bedrooms:
        for n, guesid in enumerate(bedroom[1]):
            if guesid != 0 and guesid not in registers:
                bedroom[1][n] = 0
        for n, guesid in enumerate(bedroom[2]):
            if guesid != 0 and guesid not in registers:
                bedroom[2][n] = 0
    new_mapp = mapping.bedrooms
    mapping.update_record(bedrooms=new_mapp)


def get_bedrooms(evenid):
    _bedrooms = db(Bedrooms_mapping.evenid == evenid).select().first()
    bedrooms = []
    for bedroom in _bedrooms.bedrooms:
        if sum(bedroom[1] + bedroom[2]) > 0:
            bed = [
                [n, bedroom[0], "bed", bedroom[5]]
                for n in bedroom[1]
                if n != 0
            ]
            bedrooms += bed
            top = [
                [n, bedroom[0], "top", bedroom[5]]
                for n in bedroom[2]
                if n != 0
            ]
            bedrooms += top
    return bedrooms


def get_bedroom(evenid, guesid):
    map = db(Bedrooms_mapping.evenid == evenid).select().first()
    for _bedroom in map.bedrooms:
        if int(guesid) in _bedroom[1] + _bedroom[2]:
            bedroom = _bedroom
            break
        else:
            bedroom = None
    return bedroom
