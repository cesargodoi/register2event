# -*- coding: utf-8 -*-
from gluon.storage import Storage
from gluon.custom_import import track_changes
import Reg_Utils as Reg

track_changes(True)


@auth.requires_login()
def guest_selector():
    if not request.vars.guest:
        return ""
    pattern = "%" + request.vars.guest.lower() + "%"
    if auth.has_membership("root") or (
        auth.has_membership("admin")
        and auth.user.center == request.vars.centid
    ):
        query = Guest.name_sa.lower().like(pattern)
    else:
        query = Guest.name_sa.lower().like(pattern) & (
            Guest.center == auth.user.center
        )
    selected = [
        [des(row.name), row.id]
        for row in db(query).select(orderby=Guest.name_sa, limitby=(0, 10))
    ]

    return [
        str(
            DIV(
                k[0],
                _onclick="window.open('%s', '_self')"
                % URL("register", "confirm_guest", vars={"guesid": k[1]}),
                _onmouseover="this.style.backgroundColor='orange'",
                _onmouseout="this.style.backgroundColor='white'",
            )
        )
        for k in selected
    ]


# register step 1
@auth.requires_login()
def register_step1():
    if not request.vars.evenid and not request.vars.centid:
        clear_session()
        redirect(URL("events", "list"))
    evenid = int(request.vars.evenid)
    centid = int(request.vars.centid)
    gencredit = True if request.vars.gencredit else False
    late = True if request.vars.late else False
    load = session.register
    if not load or (load.evenid != evenid):
        Reg.init(evenid=evenid, centid=centid, gencredit=gencredit, late=late)
    return dict(evenid=evenid, gencredit=gencredit)


# confirm guest
@auth.requires_login()
def confirm_guest():
    from datetime import date

    guest = Guest[request.vars.guesid]
    credit_log = guest.credit_log.select(
        Credit_Log.credit_log, orderby=Credit_Log.created_on
    ).last()
    guest.credit_log = credit_log.credit_log if credit_log else ""
    guest.age = get_age(guest.birthday) if guest.birthday else ""
    evenid = session.register.evenid
    centid = session.register.centid
    stay = [s for s in guest.guest_stay.select() if s.center == centid]
    # verifying if the guest was registrated
    if (
        db(
            (Register.evenid == evenid)
            & (Register.guesid == guest.id)
            & (Register.credit == False)
        )
        .select(orderby=Register.id)
        .first()
    ):
        # JGC = Just Generate Credit  GWR = Guest Was Registered
        guest.status = "JGC" if session.register.gencredit else "GWR"
    else:
        # GC = Generate Credit  RG = Register Guest
        guest.status = "GC" if session.register.gencredit else "RG"
    return dict(guest=guest, stay=stay, evenid=evenid, centid=centid)


# include guest
@auth.requires_login()
def include_guest():
    guest = Guest[request.vars.guesid]
    ref_value_tax = Events[session.register.evenid].ref_value
    payer = Storage(
        guesid=int(guest.id),
        name=guest.name,
        credit=guest.credit,
        amount=("%1.2f" % ref_value_tax),
    )
    Reg.include_guest(payer)


# register step 2
@auth.requires_login()
def register_step2():
    if session.register:
        ids = [p["guesid"] for p in session.register.paying]
        if not ids:
            redirect(URL("register_step1"))
    else:
        redirect(URL("show", vars={"evenid": session.register.evenid}))
    guests = session.register.paying
    PAY = PAYMENT_TYPES
    GSC = {g.guesid: g.name for g in guests if g.credit}
    if not GSC:
        GSC = {}
        PAY.pop("GSC")
    if not (auth.has_membership("root") or auth.has_membership("admin")):
        PAY.pop("FRE")
    if session.register.gencredit:
        if PAY.get("GSC"):
            PAY.pop("GSC")
        if PAY.get("FRE"):
            PAY.pop("FRE")
    form = SQLFORM.factory(
        Field(
            "ptype", requires=IS_IN_SET(PAY), default="CSH", label=T("type")
        ),
        Field(
            "bflag",
            requires=IS_EMPTY_OR(IS_IN_DB(db, "bank_flag.id", "%(name)s")),
            label=T("bank/flag"),
        ),
        Field("ctrl", label=T("control")),
        Field(
            "gscred",
            requires=IS_EMPTY_OR(IS_IN_SET(GSC)),
            label=T("guest credit"),
        ),
        Field("value", "decimal(7,2)", label=T("$")),
        submit_button="next",
    )
    form.element(_id="no_table_ptype")["_onblur"] = "payType()"
    form.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if form.process().accepted:
        if not request.vars.value and request.vars.ptype != "FRE":
            response.flash = T("enter the value $")
        elif request.vars.ptype == "GSC" and not request.vars.gscred:
            response.flash = T("select a guest with credit")
        else:
            ptype = request.vars.ptype
            bflag = request.vars.bflag
            ctrl = request.vars.ctrl
            gscred = request.vars.gscred
            val_temp = request.vars.value.replace(",", ".")
            value = 0.0 if request.vars.ptype == "FRE" else float(val_temp)
            Reg.updt_payforms(ptype, bflag, ctrl, gscred, value)
            redirect(URL("register_step2"))
    return dict(
        evenid=session.register.evenid,
        centid=session.register.centid,
        guests=guests,
        form=form,
        payforms=session.register.payforms,
        gencredit=session.register.gencredit,
        GSC=GSC,
    )


def updt_amount():
    Reg.updt_amount(long(request.vars.guesid), float(request.vars.amount))


def del_guest():
    Reg.del_guest(request.vars.guesid)
    return "document.location.reload(true)"


def del_payform():
    Reg.del_payform(int(request.vars.pf))
    return "document.location.reload(true)"


def pay_by_cash():
    session.register.pay_by_cash = True
    redirect(URL("register", "conclude"))


def cancel_register():
    clear_session()
    return 'location.href="%s";' % URL(
        "events", "show", vars={"evenid": request.vars.evenid}
    )


# conclude
@auth.requires_login()
def conclude():
    conclude = session.register
    # clear old registers, payforms and credits
    if conclude.edit_registers or conclude.delete_registers:
        Reg.adj_oldies()
    event_type = Events[conclude.evenid].activity.activity_type
    guests = conclude.paying
    payforms = conclude.payforms
    payforms_ids, registers_ids = [], []
    if conclude.pay_by_cash:
        total_guests = sum([float(g.amount) for g in guests])
        total_payforms = sum([float(pf.value) for pf in payforms])
        if total_payforms < total_guests:
            cash_value = total_guests - total_payforms
            payforms.append(
                Storage(
                    ptype="CSH",
                    bflag=None,
                    bflagname="",
                    ctrl=None,
                    value=cash_value,
                )
            )
    # insert payforms
    for p in payforms:
        new_payform = Reg.dict_payform(conclude, p, guests)
        db.payment_form.insert(**new_payform)
        pf_qry = (
            (Payment_Form.created_by == auth.user.id)
            & (Payment_Form.guests == [g.guesid for g in guests])
            & (Payment_Form.pay_type == p.ptype)
        )
        last_pf = db(pf_qry).select(orderby=Payment_Form.id).last()
        payforms_ids.append(int(last_pf.id))
    # insert registers
    for gues in guests:
        guest_stay = (
            db(
                (Guest_Stay.guesid == gues.guesid)
                & (Guest_Stay.center == conclude.centid)
            )
            .select(orderby=Guest_Stay.id)
            .first()
        )
        # try to allocate
        if event_type == "SCF":
            is_scf = True
            if guest_stay.bedroom_alt:
                mapping = (
                    db(Bedrooms_mapping.evenid == conclude.evenid)
                    .select(orderby=Bedrooms_mapping.id)
                    .first()
                )
                bedroom = [
                    m
                    for m in mapping.bedrooms
                    if m[0] == guest_stay.bedroom_alt
                ][0]
                if gues.guesid not in (bedroom[1] + bedroom[2]):
                    attempt = bed_or_top(
                        gues.guesid, guest_stay.no_top_bunk, bedroom
                    )
                    if attempt:
                        mapping.update_record(bedrooms=mapping.bedrooms)
                    else:
                        guest_stay.update_record(bedroom_alt=None)
        else:
            is_scf = False
            if guest_stay.bedroom:
                mapping = (
                    db(Bedrooms_mapping.evenid == conclude.evenid)
                    .select(orderby=Bedrooms_mapping.id)
                    .first()
                )
                bedroom = [
                    m for m in mapping.bedrooms if m[0] == guest_stay.bedroom
                ][0]
                if gues.guesid not in (bedroom[1] + bedroom[2]):
                    attempt = bed_or_top(
                        gues.guesid, guest_stay.no_top_bunk, bedroom
                    )
                    if attempt:
                        mapping.update_record(bedrooms=mapping.bedrooms)
                    else:
                        guest_stay.update_record(bedroom=None)
        # prepare registers to insert
        new_register = Reg.dict_register(
            conclude, gues, guest_stay, guests, payforms_ids, is_scf
        )
        db.register.insert(**new_register)
        reg_qry = (
            (Register.created_by == auth.user.id)
            & (Register.guesid == gues.guesid)
            & (Register.amount == gues.amount)
        )
        last_reg = db(reg_qry).select(orderby=Register.id).last()
        registers_ids.append(int(last_reg.id))
    # record many to many
    adjust_register_payforms(registers_ids, payforms_ids, conclude.evenid)
    clear_session()
    if conclude.delete_registers or conclude.edit_registers:
        adjust_bedroom_mapp(conclude.evenid)
    redirect(URL("events", "show", vars={"evenid": conclude.evenid}))


###############################################################################
def bed_or_top(guesid, no_top_bunk, bedroom, attempt=False):
    if no_top_bunk:
        if 0 in bedroom[1]:
            bedroom[1].remove(0)
            bedroom[1].append(guesid)
            bedroom[1].sort(reverse=True)
            attempt = True
    else:
        if 0 in bedroom[2]:
            bedroom[2].remove(0)
            bedroom[2].append(guesid)
            bedroom[2].sort(reverse=True)
            attempt = True
        elif 0 in bedroom[1]:
            bedroom[1].remove(0)
            bedroom[1].append(guesid)
            bedroom[1].sort(reverse=True)
            attempt = True
    return attempt


###############################################################################


# edit stay
@auth.requires_login()
def edit_stay():
    register = Register[request.vars.regid]
    edit = SQLFORM.factory(
        Field(
            "lodge",
            requires=IS_IN_SET(LODGE_TYPES),
            default=register.lodge,
            label=T("lodge"),
        ),
        Field(
            "arrival_date",
            requires=IS_IN_SET(ARRIVAL_DATE),
            default=register.arrival_date,
            label=T("arrival date"),
        ),
        Field(
            "arrival_time",
            requires=IS_IN_SET(ARRIVAL_TIME),
            default=register.arrival_time,
            label=T("arrival time"),
        ),
        Field(
            "no_stairs",
            "boolean",
            default=register.no_stairs,
            label=T("no stairs"),
        ),
        Field(
            "no_top_bunk",
            "boolean",
            default=register.no_top_bunk,
            label=T("no top bunk"),
        ),
        Field(
            "staff",
            requires=IS_EMPTY_OR(IS_IN_SET(STAFFS)),
            default=register.staff,
            label=T("staff"),
        ),
        Field(
            "description",
            "text",
            default=register.description,
            label=T("description"),
        ),
        Field("ps", "text", default=register.ps, label=T("ps")),
        Field("up_date", "boolean", label=T("update stay")),
        submit_button="update",
    )
    edit.element(_name="description")["_rows"] = 1
    edit.element(_name="ps")["_rows"] = 1
    edit.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if edit.process().accepted:
        new_stay = dict(
            lodge=request.vars.lodge,
            arrival_date=request.vars.arrival_date,
            arrival_time=request.vars.arrival_time,
            no_stairs=request.vars.no_stairs,
            no_top_bunk=request.vars.no_top_bunk,
            staff=request.vars.staff,
            description=request.vars.description,
            ps=request.vars.ps,
        )
        register.update_record(**new_stay)
        if request.vars.up_date:
            guest_stay = (
                db(
                    (Guest_Stay.guesid == register.guesid)
                    & (Guest_Stay.center == register.evenid.center)
                )
                .select(orderby=Guest_Stay.id)
                .first()
            )
            guest_stay.update_record(**new_stay)
        adjust_bedroom_mapp(register.evenid)
        redirect(URL("events", "show", vars={"evenid": register.evenid}))
    return dict(form=edit, register=register)


# edit registers
@auth.requires_login()
def edit_registers():
    read = read_register(request.vars.regid)
    if not read:
        clear_session()
        redirect(URL("events", "list"))
    if not session.register or not session.register.edit_reg:
        Reg.init(
            evenid=read.registers[0].evenid,
            centid=read.registers[0].evenid.center,
            gencredit=read.registers[0].credit,
            late=read.registers[0].late,
            edit_registers=True,
        )
        Reg.reconstruct(read.registers, read.payforms)
    redirect(URL("register", "register_step2"))


# messages

gsc_choose_who_credit_msg = """
        Este registro múltiplo possui credito(s) do(s) hospede(s) em sua(s) forma(s) de
        pagamento(s), O sistema ira devolver o(s) credito(s) antigo(s) e gerar novo(s) crédito(s)
        (caso existam outras formas de pagamento) para o(s) hospede(s) escolhido(s).
        Escolha o(s) hospede(s) que recebera(ão) o credito restante.
        """
gsc_generate_credit_msg = """
        Este registro possui além do credito do hospede, outra(s) forma(s) de
        pagamento(s) que não pode(m) ser devolvida(s).  O sistema ira devolver o
        antigo credito do hospede e gerar novo crédito com o que não pode ser apagado.
        Proceder a operação?
        """
gsc_cancels_msg = """
        Este é um registro múltiplo onde foi usado crédito de um hospede.
        Por motivo de segurança de informações,
        optamos por cancelar todos os registros atrelados a este.
        Deseja realmente excluir?
        """
gsc_cancel_msg = """
        Neste registro foi usado crédito de um hospede.
        Ao cancelar este registro o crédito sera restituido à ele.
        Deseja realmente excluir?
        """
choose_who_credit_msg = """
        Este registro múltiplo possui forma(s) de pagamento(s) que não pode(m) ser devolvida(s).
        Ao cancelar este registro, o sistema cancelará todos os registros atrelados a este e
        gerará crédito(s) para o(s) hospede(s).  Temos duas opções para gerenciar isso:
        1) Gerar o crédito de acordo com os valores declarados nos registros;
        2) Remanejar os hospedes e a(s) forma(s) de pagamento para direcionar o crédito.
        Escolha uma das opções.
        """
generate_credit_msg = """
        Este registro possui forma(s) de pagamento(s) que não podem ser devolvida(s).
        (DEBTO / CREDITO / TRANSFERÊNCIA / DEPOSITO),
        Deseja gerar crédito para o hospede?
        """
cancel_msg = """
        Sem restrições para cancelamento do registro.
        Os valores serão devolvidos ao(s) hospede(s).
        Deseja realmente cancelar o registro?
        """
reenable_registration_msg = """
        Ao reativar o registro, os valores e as formas de pagamento precisam ser re-inseridos.
        Deseja realmente reativar o registro?
        """


def gen_button(b_label, b_link, b_class, regid):
    bt_class = "btn btn-%s" % b_class
    if not b_link:
        return A(
            T(b_label),
            _type="button",
            _class=bt_class,
            **{"_data-dismiss": "modal", "_aria-label": "Close"}
        )
    else:
        bt_link = "%s(%s)" % (b_link, regid)
    return A(T(b_label), _type="button", _class=bt_class, _onclick=bt_link)


# unregister ###
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def unenroll_verify():
    reg = Register[request.vars.regid]
    # inscrições encerradas
    if reg.evenid.reg_deadline < request.now:
        title = T("the subscriptions are closed")
        content = "O prazo de inscrição já está fechado e as arrecadações já \
                   foram enviadas para o centro de conferência"
        buttons = gen_button("close", None, "primary", None)
    elif reg.is_active == False:
        # reativar o registro no evento
        title = T("re-enable registration?")
        content = reenable_registration_msg
        buttons = gen_button(
            "re-enable registration?",
            "reEnableRegistration",
            "warning",
            reg.id,
        )
    # TO DO?
    # elif reg.credit == True:
    #     # tratando de lançamentos de créditos ######################################################
    #     print 'é credito'
    #     if reg.multiple:
    #         print '- faz parte de credito múltiplo'
    #         if len(reg.payforms) > 1:
    #             print '-- tem mais de uma forma de pagamento'
    #         else:
    #             print '-- tem apenas uma forma de pagamento'
    #     else:
    #         print '- é um credito simples'
    #         if len(reg.payforms) > 1:
    #             print '-- tem mais de uma forma de pagamento'
    #         else:
    #             print '-- tem apenas uma forma de pagamento'
    else:
        # tratando de pagamentos regulares #########################################################
        payforms = db(Payment_Form.id.belongs(reg.payforms)).select()
        dict_pf = {
            n: (p.pay_type, p.guesid, p.amount) for n, p in enumerate(payforms)
        }
        not_delete = [
            p.pay_type
            for p in payforms
            if p.pay_type in ["DBT", "CDT", "DPT", "TRF"]
        ]
        # verifica se tem credito do hóspede nas formas de pagamento
        if "GSC" in [v[0] for v in dict_pf.values()]:
            # verifica se existem DEB CDT DPT TRF nas formas de pagamento e gera créditos
            if not_delete:
                if reg.multiple:
                    # escolher pra quem devolver o credito restante unenroll_choose_who_credit
                    title = T("who will be credited?")
                    content = gsc_choose_who_credit_msg
                    buttons = gen_button(
                        "who will be credited?",
                        "unEnrollGenerateCreditGsc",
                        "danger",
                        reg.id,
                    )
                else:
                    # devolver pra mesma pessoa
                    title = T("return and generate credits?")
                    content = gsc_generate_credit_msg
                    buttons = gen_button(
                        "return and generate credits?",
                        "unEnrollGenerateCreditGsc",
                        "danger",
                        reg.id,
                    )
            else:
                if reg.multiple:
                    # ajustar o crédito e apagar o que pode ser apagado
                    title = T("cancel all entries?")
                    content = gsc_cancels_msg
                    buttons = gen_button(
                        "cancel all entries?",
                        "unEnrollCancelRegistersGsc",
                        "danger",
                        reg.id,
                    )
                else:
                    # devolver o crédito e apagar o que pode ser apagado
                    title = T("cancel register?")
                    content = gsc_cancel_msg
                    buttons = gen_button(
                        "cancel register?",
                        "unEnrollCancelRegisterGsc",
                        "danger",
                        reg.id,
                    )
        else:
            if not_delete:
                if reg.multiple:
                    # escolher pra quem vai ser gerado credito
                    title = T("who will be credited?")
                    content = choose_who_credit_msg
                    buttons = [
                        gen_button(
                            "1) like in register?",
                            "unEnrollGenCreditLikeRegister",
                            "danger",
                            reg.id,
                        ),
                        gen_button(
                            "2) rearranging credit entry?",
                            "unEnrollGenCreditRearranging",
                            "danger",
                            reg.id,
                        ),
                    ]
                else:
                    # gerar crédito para o hospede
                    title = T("generate credit?")
                    content = generate_credit_msg
                    buttons = gen_button(
                        "generate credit?",
                        "unEnrollGenerateCredit",
                        "danger",
                        reg.id,
                    )
            else:
                # cancelar e devolver o dinheiro / cheque / cheque pré
                title = T("cancel register?")
                content = cancel_msg
                buttons = gen_button(
                    "cancel register?",
                    "unEnrollCancelRegister",
                    "danger",
                    reg.id,
                )

    return DIV(
        DIV(
            DIV(
                A(
                    SPAN(XML("&times;"), **{"_aria-hidden": "true"}),
                    _type="button",
                    _class="close",
                    **{"_data-dismiss": "modal", "_aria-label": "Close"}
                ),
                H4(title, _class="modal-title"),
                _class="modal-header",
            ),
            DIV(content, _class="modal-body"),
            DIV(buttons, _class="modal-footer"),
            _class="modal-content",
        ),
        _class="modal-dialog",
        _role="document",
    )


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def unenroll_generate_credit_gsc():
    read = read_register(request.vars.regid)
    evenid = read.registers[0].evenid
    centid = read.registers[0].evenid.center
    to_devol, to_credit = [], []
    # ler as formas de pagamento
    for pf in read.payforms:
        if pf.pay_type == "GSC":
            # se tiver GSC marcar para devolver e restituir o crédito
            to_devol.append((pf.id, pf.amount))
            Reg.update_credit_and_log(pf.guesid, pf.evenid, pf.amount, "DEV")
        else:
            # se não, marcar pra creditar e atualizar a forma de pagamento para crédito
            to_credit.append((pf.id, pf.amount))
            pf.update_record(credit=True, created_by=auth.user.id)
    # filtrar os ids de devolção e crédito
    devol_ids = [i[0] for i in to_devol]
    credit_ids = [i[0] for i in to_credit]
    # deletar as formas de pagamento na tabela payment_form e register_payment_forms
    db(Payment_Form.id.belongs(devol_ids)).delete()
    db(Register_Payment_Form.payfid.belongs(devol_ids)).delete()
    # ajustar a nova quantia (do valor restante) por hóspede
    old_amount = sum([r.amount for r in read.registers])
    new_amount = (old_amount - sum([td[1] for td in to_devol])) / len(
        read.registers
    )
    # ajustar os registros
    # verificar se tem mais de um registro atrelado
    if len(read.registers) > 1:
        # se houver mais de um registro, preparar para editar manualmente as formas de pagamento
        for r in read.registers:
            r.update_record(
                amount=new_amount,
                payforms=credit_ids,
                credit=True,
                created_by=auth.user.id,
            )
        read2 = read_register(request.vars.regid)
        Reg.init(
            evenid=evenid,
            centid=centid,
            gencredit=True,
            edit_registers=True,
            late=read.registers[0].late,
        )
        session.register.creddevol = True
        Reg.reconstruct(read2.registers, read2.payforms)
        adjust_bedroom_mapp(evenid)
        return 'location.href="%s";' % URL("register", "register_step2")
    else:
        # caso contrário, ajustar o registro e sair da função
        for r in read.registers:
            r.update_record(
                amount=new_amount,
                payforms=credit_ids,
                credit=True,
                created_by=auth.user.id,
            )
            Reg.update_credit_and_log(r.guesid, r.evenid, new_amount, "GEN")
        return 'location.href="%s";' % URL(
            "events", "show", vars={"evenid": evenid}
        )


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def unenroll_cancel_registers_gsc():
    read = read_register(request.vars.regid)
    pf_to_kill, reg_to_kill = [], []
    for pf in read.payforms:
        pf_to_kill.append(pf.id)
        if pf.pay_type == "GSC":
            Reg.update_credit_and_log(pf.guesid, pf.evenid, pf.amount, "DEV")
    for reg in read.registers:
        reg_to_kill.append(reg.id)
    db(Payment_Form.id.belongs(pf_to_kill)).delete()
    db(Register_Payment_Form.payfid.belongs(pf_to_kill)).delete()
    db(Register.id.belongs(reg_to_kill)).delete()
    adjust_bedroom_mapp(read.registers[0].evenid)
    clear_session()
    return 'location.href="%s";' % URL(
        "events", "show", vars={"evenid": read.registers[0].evenid}
    )


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def unenroll_cancel_register_gsc():
    read = read_register(request.vars.regid)
    for r in read.registers:
        r.update_record(is_active=False, created_by=auth.user.id)
    for pf in read.payforms:
        if pf.pay_type == "GSC":
            Reg.update_credit_and_log(pf.guesid, pf.evenid, pf.amount, "DEV")
        pf.update_record(is_active=False, created_by=auth.user.id)
    adjust_bedroom_mapp(read.registers[0].evenid)
    clear_session()
    return 'location.href="%s";' % URL(
        "events", "show", vars={"evenid": read.registers[0].evenid}
    )


# daqui pra baixo não trata credito do hospede
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def unenroll_gen_credit_like_register():
    read = read_register(request.vars.regid)
    for r in read.registers:
        Reg.update_credit_and_log(r.guesid, r.evenid, r.amount, "DEV")
        r.update_record(credit=True, created_by=auth.user.id)
    for pf in read.payforms:
        pf.update_record(credit=True, created_by=auth.user.id)
    adjust_bedroom_mapp(read.registers[0].evenid)
    clear_session()
    return 'location.href="%s";' % URL(
        "events", "show", vars={"evenid": read.registers[0].evenid}
    )


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def unenroll_gen_credit_rearranging():
    read = read_register(request.vars.regid)
    if not session.register or not session.register.edit_reg:
        Reg.init(
            evenid=read.registers[0].evenid,
            centid=read.registers[0].evenid.center,
            gencredit=True,
            edit_registers=True,
            late=read.registers[0].late,
        )
        session.register.creddevol = True
        Reg.reconstruct(read.registers, read.payforms)
    adjust_bedroom_mapp(read.registers[0].evenid)
    return 'location.href="%s";' % URL("register", "register_step2")


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def unenroll_generate_credit():
    read = read_register(request.vars.regid)
    Reg.update_credit_and_log(
        read.registers[0].guesid,
        read.registers[0].evenid,
        sum([pf.amount for pf in read.payforms]),
        "DEV",
    )
    # turn regular registration in credit registration
    read.registers[0].update_record(credit=True, created_by=auth.user.id)
    for pf in read.payforms:
        pf.update_record(credit=True, created_by=auth.user.id)
    # adjust bedrooms_mapping
    adjust_bedroom_mapp(read.registers[0].evenid)
    return 'location.href="%s";' % URL(
        "events", "show", vars={"evenid": read.registers[0].evenid}
    )


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def unenroll_cancel_register():
    read = read_register(request.vars.regid)
    for r in read.registers:
        r.update_record(is_active=False, created_by=auth.user.id)
    for pf in read.payforms:
        pf.update_record(is_active=False, created_by=auth.user.id)
    adjust_bedroom_mapp(read.registers[0].evenid)
    clear_session()
    return 'location.href="%s";' % URL(
        "events", "show", vars={"evenid": read.registers[0].evenid}
    )


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def reenable_registration():
    read = read_register(request.vars.regid)
    for r in read.registers:
        r.update_record(is_active=True, created_by=auth.user.id)
    for pf in read.payforms:
        pf.update_record(is_active=True, created_by=auth.user.id)
    if not session.register or not session.register.edit_reg:
        Reg.init(
            evenid=read.registers[0].evenid,
            centid=read.registers[0].evenid.center,
            gencredit=False,
            edit_registers=True,
            late=read.registers[0].late,
        )
        Reg.reconstruct(read.registers, read.payforms)
    return 'location.href="%s";' % URL("register", "register_step2")
