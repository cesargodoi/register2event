#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gluon import *
from gluon.storage import Storage


# working with session.register
def init(evenid,
         centid,
         gencredit=False,
         late=False,
         edit_registers=False,
         delete_registers=False,
         pay_by_cash=False):
    current.session.register = Storage()
    current.session.register.evenid = evenid
    current.session.register.centid = centid
    current.session.register.gencredit = gencredit
    current.session.register.late = late
    current.session.register.paying = []
    current.session.register.payforms = []
    current.session.register.edit_registers = edit_registers
    current.session.register.delete_registers = delete_registers
    current.session.register.adjust_gscredit = []
    current.session.register.old_regs = []
    current.session.register.old_payforms = []
    current.session.register.pay_by_cash = pay_by_cash


def include_guest(payer):
    ids = [pyr.guesid for pyr in current.session.register.paying]
    if ids:
        if payer.guesid not in ids:
            current.session.register.paying.append(payer)
    else:
        current.session.register.paying.append(payer)


def updt_amount(guesid, amount):
    for pay in current.session.register.paying:
        if pay.guesid == guesid:
            pay.amount = '%1.2f' % amount


def del_guest(guesid):
    payforms = []
    for pay in current.session.register.payforms:
        if pay.ptype == 'GSC':
            if pay.gscred != guesid:
                payforms.append(pay)
        else:
            payforms.append(pay)
    current.session.register.payforms = payforms
    load = current.session.register.paying
    guests = [g for g in load if g.guesid != int(guesid)]
    current.session.register.paying = guests


def updt_payforms(ptype, bflag, ctrl, gscred, value, payfid=None):
    value = float(value)
    total = sum([float(g.amount) for g in current.session.register.paying])
    previous = sum([float(pf.value) for pf in
                    current.session.register.payforms])
    lacking = total - previous
    if (ptype in ('GSC', 'CSH')) and value > lacking:
        value = lacking
    if ptype == 'GSC':
        guest = [gs for gs in current.session.register.paying
                 if gs.guesid == int(gscred)][0]
        gsc_prev = sum([float(pp.value) for pp in
                        current.session.register.payforms if pp.ptype == 'GSC'
                        and pp.gscred == guest.guesid])
        lacking_credit = float(guest.credit) - gsc_prev
        if (value > lacking_credit) and (lacking_credit > 0):
            value = lacking_credit
        current.session.register.payforms.append(
            Storage(ptype=ptype, gscred=long(gscred), value=value))
    else:
        bflagname = '%(name)s' % current.db.bank_flag[bflag] if bflag else ''
        current.session.register.payforms.append(
            Storage(ptype=ptype,
                    bflag=bflag,
                    bflagname=bflagname,
                    ctrl=ctrl,
                    value=value,
                    payfid=payfid))


def del_payform(pf):
    current.session.register.payforms.pop(pf)


def dict_payform(register, payform, guests):
    new_payform = dict(
        evenid=register.evenid,
        centid=current.auth.user.center,
        pay_type=payform.ptype,
        bank_flag=payform.bflag if payform.ptype not in ['GSC', 'CSH', 'FRE'] else None,
        num_ctrl=payform.ctrl if payform.ptype not in ['GSC', 'CSH', 'FRE'] else None,
        amount=payform.value,
        guesid=payform.gscred if payform.ptype == 'GSC' else None,
        guests=[g.guesid for g in guests],
        credit=True if register.gencredit else False,
        created_by=current.auth.user.id,
        created_on=current.request.now,
        late=True if register.late else False
    )
    if payform.ptype == 'GSC':
        update_credit_and_log(payform.gscred, register.evenid, payform.value, 'USE')
    return new_payform


def dict_register(register, guest, guest_stay, guests, pf_ids, is_scf):
    new_register = dict(
        evenid=register.evenid,
        guesid=guest.guesid,
        lodge=guest_stay.lodge,
        no_stairs=guest_stay.no_stairs,
        no_top_bunk=guest_stay.no_top_bunk,
        arrival_date=guest_stay.arrival_date,
        arrival_time=guest_stay.arrival_time,
        bedroom=guest_stay.bedroom_alt if is_scf else guest_stay.bedroom,
        staff=guest_stay.staff,
        description=guest_stay.description,
        ps=guest_stay.ps,
        amount=float(guest.amount),
        multiple=True if len(guests) > 1 else False,
        credit=True if register.gencredit else False,
        late=True if register.late else False,
        payforms=pf_ids
    )
    if register.gencredit:
        update_credit_and_log(guest.guesid, register.evenid, guest.amount, 'GEN')
    return new_register


def update_credit_and_log(guesid, evenid, value, oper):
    guest = current.db.guest[guesid]
    event = current.db.events[evenid]
    value = float(value)
    guest_credit = float(guest.credit)
    activity = event.activity.activity_type
    center_name = event.center.shortname
    event_date = event.start_date.strftime('%d/%m/%y')

    # choose one way
    if oper == 'GEN':
        result = guest_credit + value
        _log = '[%.2f] = %.2f + %.2f (%s  in %s  on %s)'
    elif oper == 'CAN':  # cancel some credit launch - not used yet
        result = guest_credit - value
        _log = '[%.2f] = %.2f - %.2f (%s  in %s  on %s)'
    elif oper == 'DEV':  # devolution of some value
        result = guest_credit + value
        _log = '[%.2f] = %.2f + %.2f (%s  in %s  on %s)'
    elif oper == 'USE':
        result = guest_credit - value
        _log = '[%.2f] = %.2f - %.2f (%s  in %s  on %s)'
    elif oper == 'CML':  # cancel multiple launch
        result = guest_credit + value
        _log = '[%.2f] = %.2f + %.2f (%s  in %s  on %s)'
    elif oper == 'RPY':  # repayment of payment
        result = guest_credit + value
        _log = '[%.2f] = %.2f + %.2f (%s  in %s  on %s)'

    credit_log = _log % (result, guest_credit, value, activity, center_name, event_date)

    # update guest.credit and insert credit_log
    guest.update_record(credit=result)
    current.db.credit_log.insert(guesid=guesid,
                                 credit=value,
                                 oper=oper,
                                 credit_log=credit_log)


def adj_oldies():
    if current.session.register.old_regs:
        current.db(current.db.register.id.belongs(
            current.session.register.old_regs)).delete()
    if current.session.register.old_payforms:
        current.db(current.db.payment_form.id.belongs(
            current.session.register.old_payforms)).delete()
    if not current.session.register.delete_registers:
        if current.session.register.adjust_gscredit:
            for adj_gsc in current.session.register.adjust_gscredit:
                gsc = current.db.guest[adj_gsc.guesid]
                gsc.update_record(credit=adj_gsc.credit)
                credit_log = 'ADJUST TO PREVIOUS VALUE-> $%s  by %s %s' % \
                    (adj_gsc.credit,
                     current.auth.user.first_name,
                     current.auth.user.last_name)
                current.db.credit_log.insert(
                    guesid=adj_gsc.guesid,
                    credit=adj_gsc.credit,
                    credit_log=credit_log
                )
                current.db.commit()


def reconstruct(registers, payforms):
    for r in registers:
        current.session.register.old_regs.append(r.id)
        gsc_in_payforms = [Storage(credit=pf.amount) for pf in payforms if pf.guesid == r.guesid]
        gsc = current.db.guest[r.guesid]
        for gsc_pf in gsc_in_payforms:
            gsc.credit += gsc_pf.credit
            current.session.register.adjust_gscredit.append(
                Storage(credit=gsc.credit,
                        guesid=r.guesid)
            )
        payer = Storage(guesid=long(r.guesid),
                        name=r.guesid.name,
                        center=r.guesid.center,
                        credit=gsc.credit,
                        amount=('%1.2f' % r.amount),
                        regid=r.id)
        include_guest(payer)
    for pf in payforms:
        current.session.register.old_payforms.append(pf.id)
        updt_payforms(ptype=pf.pay_type,
                      bflag=pf.bank_flag,
                      ctrl=pf.num_ctrl,
                      gscred=pf.guesid,
                      value=pf.amount,
                      payfid=pf.id)


def copy_register():
    current.session.copy_register = Storage(current.session.register.copy())
