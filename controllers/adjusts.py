# -*- coding: utf-8 -*-

# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_bedroom_alt():
#     print '------------------- adjust_bedroom_alt -------------------------'
#     reg_beds = [r.guesid for r in db(Register.evenid == 2).select() if r.bedroom]
#     problems = [s.guesid for s in db(Guest_Stay).select() if s.guesid in reg_beds and not s.bedroom_alt]
#     for p in problems:
#         print p



# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_payforms_by_registers():
#     print '-------------- adjust_payforms_by_registers ---------------'
#     for user in db(db.auth_user).select():
#         print 'USER:', user.first_name
#         print 'ID:', user.id
#         registers = db(Register.created_by==user.id).select(orderby=Register.id)
#         print 'REGISTROS:', len(registers)
#         print '-----------------------------------------------------------'
#         for r in registers:
#             payforms = db((Payment_Form.id.belongs(r.payforms))).select()
#             for p in payforms:
#                 m2m = db((Register_Payment_Form.regid==r.id)&(Register_Payment_Form.payfid==p.id)).select()
#                 if not m2m:
#                     m2m2 = db(Register_Payment_Form.payfid==p.id).select()
#                     print 'hospede:', r.guesid.name
#                     print 'registro:', r.id, ' payforms:', r.payforms, ' multiplo?:', r.multiple
#                     print 'não achamos ligação para:', r.id, ' e', p.id
#                     if m2m2:
#                         print 'no entanto achamos a(s) seguintes ligações:'
#                         for m2 in m2m2:
#                             print 'id:', m2.id, 'reg:', m2.regid, 'pf:', m2.payfid
#                             if not r.multiple:
#                                 print 'vamos apagar esta ligação incorreta'
#                         db(Register_Payment_Form.payfid == p.id).delete()
#                         print 'vamos criar uma ligação nova para:'
#                         print 'reg:', r.id, 'pf:', p.id, 'evenid:', r.evenid
#                         print '-----------------------------------------------------------'
#                         db.register_payment_form.insert(regid=r.id, payfid=p.id, evenid=r.evenid)
#                     else:
#                         print 'vamos criar uma ligação nova para:'
#                         print 'reg:', r.id, 'pf:', p.id, 'evenid:', r.evenid
#                         print '-----------------------------------------------------------'
#                         db.register_payment_form.insert(regid=r.id, payfid=p.id, evenid=r.evenid)
#
#     print '----------------------- hard_adjust -----------------------'
#     hard_reg = db(Register.id.belongs([358, 359,360])).select(orderby=Register.id)
#     n = 292
#     for h in hard_reg:
#         h.update_record(payforms=[long(n)])
#         n += 1
#     hard_pf = db(Payment_Form.id.belongs([313, 445, 446, 450, 451])).delete()
#     print hard_pf
#     hard_reg_pf = db(Register_Payment_Form.id.belongs([365,366,367])).select(orderby=Register_Payment_Form.id)
#     n2 = 292
#     for hrpf in hard_reg_pf:
#         print hrpf.id, n2
#         hrpf.update_record(payfid=long(n2))
#         n2 += 1
#     print '---------------------- thats right ------------------------'



# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_bedroom_alt():
#     read = db(Guest_Stay).select()
#     excepts = [r.guesid for r in db(Register.evenid==2).select() if r.guesid.center==1]
#     for r in read:
#         if r.guesid.center == 1:
#             if r.guesid in excepts and r.bedroom:
#                 bedroom = r.bedroom
#                 r.update_record(bedroom_alt=bedroom, bedroom=None)
#         else:
#             if not r.bedroom_alt:
#                 bedroom = r.bedroom
#                 r.update_record(bedroom_alt=bedroom, bedroom=None)


# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_kill_register():
#     print '-------------- adjust_kill_register ---------------'
#     read = read_register(301) # TO DO --> request.vars.regid
#     rids = [r.id for r in read.registers]
#     pfids = [pf.id for pf in read.payforms]
#     db(Register.id.belongs(rids)).delete()
#     db(Payment_Form.id.belongs(pfids)).delete()


# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_registers_ps():
#     print '-------------- adjust_registers_ps ---------------'
#     registers = db(Register).select()
#     for r in registers:
#         gst = db((Guest_Stay.guesid==r.guesid) & (Guest_Stay.center==r.evenid.center)).select().first()
#         if gst.ps or gst.description:
#             r.update_record(ps=gst.ps, description=gst.description)
#             print r.guesid, r.ps, r.description
#             print '-->', gst.ps, gst.description


# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_m2m():
#     print '-------------- adjust_m2m ---------------'
#     m2m = db(Register_Payment_Form).select()
#     for m in m2m:
#         if Register[m.regid] and Payment_Form[m.payfid]:
#             print 'm2m %s: certo' % m.id
#         else:
#             print 'm2m %s: errado <<<<' % m.id
#     print 'temos %s m2m(s)' % len(m2m)


# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_summary():
#     import json
#     evenid = request.args(0)
#     events = db(Register.evenid==evenid).select()
#     for ev in events:
#         stay = {'lodge':ev.guesid.lodge,
#                 'no_stairs':ev.guesid.no_stairs,
#                 'no_top_bunk':ev.guesid.no_top_bunk,
#                 'arrival_date':ev.guesid.arrival_date,
#                 'arrival_time':ev.guesid.arrival_time,
#                 'staff':ev.guesid.staff,
#                 'ps':ev.guesid.ps}
#         summary = json.dumps(stay)
#         ev.update_record(summary=summary)

# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_id_ccpa():
#     file_name = 'applications/reg2conf/static/docs/ids_ccpa.csv'
#     content = open(file_name, 'rb')
#     lines = content.readlines()
#     content.close()
#     IDS_CCPA = []
#     for line in lines:
#         l = line.strip('\n').split(',')
#         tupl = (des(l[0].lower()), l[1])
#         IDS_CCPA.append(tupl)
#     guests = db(Guest.id>0).select()
#     for g in guests:
#         for idccpa in IDS_CCPA:
#             if g.name_sa.lower() == idccpa[0]:
#                 g.update_record(id_ccpa=idccpa[1])
#     return dict()

# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_new_ids_ccpa():
#     file_name = 'applications/reg2conf/static/docs/new_ids_ccpa.csv'
#     content = open(file_name, 'rb')
#     lines = content.readlines()
#     content.close()
#     IDS_CCPA = []
#     for line in lines:
#         l = line.strip('\n').split(',')
#         tupl = (int(l[0]), int(l[2]))
#         IDS_CCPA.append(tupl)
#     guests = db(Guest.id>0).select()
#     for g in guests:
#         for idccpa in IDS_CCPA:
#             if g.id == idccpa[0]:
#                 g.update_record(id_ccpa=idccpa[1])
#     return dict()

# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_lodge():
#     guests = db(Guest).select()
#     for g in guests:
#         if g.no_stay:
#             g.update_record(lodge='HSE')
#         else:
#             g.update_record(lodge='LDG')
#     return dict()

# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_guests_in_payment_forms():
#     payforms = db(Payment_Form).select()
#     for pf in payforms:
#         pfps = pf.ps.split(':')[2].strip('}')
#         pfps = pfps.strip('[')
#         pfps = pfps.strip(']')
#         guests = pfps.split(',')
#         pf.update_record(guests=guests)
#     return dict()

# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adjust_ccpa_ps():
#     file_name = 'applications/reg2event/static/docs/ccpa_ps.csv'
#     content = open(file_name, 'rb')
#     lines = content.readlines()
#     content.close()
#     for line in lines:
#         lline = line.split(',')
#         id_ccpa = int(lline[-1])
#         ps = lline[-3]
#         lodge = 'LDG'
#         if lline[1] == 'VERDADEIRO':
#             lodge = 'LDG'
#         elif lline[2] == 'VERDADEIRO':
#             lodge = 'HSE'
#         elif lline[3] == 'VERDADEIRO':
#             lodge = 'HTL'
#         guest = db(Guest.id_ccpa==id_ccpa).select().first()
#         if guest:
#             guest.update_record(lodge=lodge)
#             guest.update_record(ps=ps)
#     return dict()

# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adj_deadline():
#     from datetime import date, datetime, timedelta, time
#     arquivo = open('adj_deadline.txt', 'w')
#     arquivo.write('Ajuste de deadline - %s\n\n' % request.now)
#     arquivo.write('-'*80)
#     events = [(ev.id, ev.end_date, ev.activity.activity) for ev in
#               db(Events).select()]
#     for ev in events:
#         last_deadline = datetime.combine(ev[1] + timedelta(days=1),
#                                          datetime.min.time()) + \
#                                           timedelta(hours=18)
#         registers = db(Register.evenid==ev[0]).select()
#         pay_form = db(Payment_Form.evenid==ev[0]).select()
#         arquivo.write('\nevent: %s (%s)  regs: %s  pay_forms: %s
#                       deadline: %s' % \
#              (ev[2],ev[0],len(registers),len(pay_form),last_deadline))
#         regs, pforms = 0, 0
#         for reg in registers:
#             if reg.created_on > last_deadline:
#                 regs += 1
#         for pf in pay_form:
#             if pf.created_on > last_deadline:
#                 pforms += 1
#         if regs > 0:
#             arquivo.write('\n - %s registers needs update' % regs)
#         if pforms > 0:
#             arquivo.write('\n - %s pay_forms needs update' % pforms)
#     arquivo.close()
#     return dict()

# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adj_deadline_fix():
#     from datetime import date, datetime, timedelta, time
#     evenid = 3 # this is the envent id
#     arquivo = open('adj_deadline_fix.txt', 'w')
#     arquivo.write('Ajuste de deadline - FIX - %s\n\n' % request.now)
#     arquivo.write('-'*80)
#     event = Events[evenid]
#     deadline = datetime.combine(event.end_date+timedelta(days=1), \
#                                 datetime.min.time())+timedelta(hours=18)
#     new_date = deadline-timedelta(hours=1)
#     registers = db(Register.evenid==evenid).select()
#     pay_form = db(Payment_Form.evenid==evenid).select()
#     arquivo.write('\nevent: %s  id: %s  regs: %s
#                   pay_forms: %s  deadline: %s' \
#        % (event.activity.activity,
#           evenid,
#           len(registers),
#           len(pay_form),deadline))
#     regs, pforms = 0, 0
#     for reg in registers:
#         if reg.created_on > deadline:
#             reg.update_record(created_on=new_date)
#             reg.update_record(modified_on=new_date)
#             regs += 1
#     for pf in pay_form:
#         if pf.created_on > deadline:
#             pf.update_record(created_on=new_date)
#             pf.update_record(modified_on=new_date)
#             pforms += 1
#     if regs > 0:
#         arquivo.write('\n - %s registers updated' % regs)
#     if pforms > 0:
#         arquivo.write('\n - %s pay_forms updated' % pforms)
#     arquivo.close()
#     return dict()


# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adj_staffs():
#     arquivo = open('adj_staff.txt', 'w')
#     arquivo.write('Ajuste de staff - %s\n\n' % request.now)
#     arquivo.write('-'*80)
#     guests = db(Guest).select()
#     for g in guests:
#         if len(g.staff)>1:
#             arquivo.write('\n nome: %(name)s staffs: %(staff)s' % g)
#             if g.staff[0] != 'AFT':
#                 g.update_record(staff=g.staff[0])
#             else:
#                 g.update_record(staff=g.staff[1])
#             arquivo.write('\n - novo staff: %(staff)s' % g)
#     arquivo.close()


# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adj_staffs_fix():
#     guests = db(Guest).select()
#     for g in guests:
#         if g.staff:
#             g.update_record(staffs=g.staff[0])


# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adj_staff_summary():
#     import json
#     registers = db(Register).select()
#     for r in registers:
#         old_summary = json.loads(r.summary)
#         if isinstance(old_summary['staff'], list):
#             staff = old_summary['staff'][0] if old_summary['staff'] else None
#         else:
#             staff = old_summary['staff'] if old_summary['staff'] else None
#         stay = {'lodge':old_summary['lodge'],
#                 'no_stairs':old_summary['no_stairs'],
#                 'no_top_bunk':old_summary['no_top_bunk'],
#                 'arrival_date':old_summary['arrival_date'],
#                 'arrival_time':old_summary['arrival_time'],
#                 'staff':staff,
#                 'ps':old_summary['ps']}
#         summary = json.dumps(stay)
#         r.update_record(summary=summary)


# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def adj_late():
#     from datetime import datetime, timedelta
#     events = db(Events).select()
#     for ev in events:
#         limit_date = datetime.combine(ev.end_date + timedelta(days=1),
#                                       datetime.min.time()) +
#                                       timedelta(hours=18)
#         registers = db(Register.evenid==ev.id).select()
#         for reg in registers:
#             if reg.created_on>limit_date:
#                 reg.update_record(late=True)
#             else:
#                 reg.update_record(late=False)
#         pay_forms = db(Payment_Form.evenid==ev.id).select()
#         for pay in pay_forms:
#             if pay.created_on>limit_date:
#                 pay.update_record(late=True)
#             else:
#                 pay.update_record(late=False)


# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def import_guests():
#     print 'IMPORT GUESTS'
#     print '-' * 80
#     print '1 - reading the file...'
#     import_file = open('applications/register2event/import_guests.csv','r')
#     lines = import_file.readlines()
#     import_file.close()
#     error_file = open('applications/register2event/import_errors.csv','w')
#     print '2 - try to insert in db'
#     for line in lines:
#         cur_line = line.split(',')
#         new_guest = dict(
#             center=cur_line[0],
#             enrollment=cur_line[1],
#             name=cur_line[2],
#             name_sa=cur_line[3],
#             id_card=cur_line[4],
#             gender=cur_line[5],
#             birthday=cur_line[6],
#             city=cur_line[7],
#             state_prov=cur_line[8],
#             country=cur_line[9],
#             aspect=cur_line[10],
#             email=cur_line[11],
#             cell_phone=cur_line[12],
#             sos_contact=cur_line[13],
#             sos_phone=cur_line[14],
#             credit=cur_line[15],
#             ps=cur_line[16],
#             is_active=cur_line[17]
#         )
#         guest_in_db = db(Guest.name_sa==cur_line[3]).select().first()
#         if not guest_in_db:
#             try:
#                 db.guest.insert(**new_guest)
#             except:
#                 error_file.write(line)
#                 print 'error - %s' % cur_line[2]
#         else:
#             print cur_line[3], 'ja inserido'
#     error_file.close()
#     print 'well done!'



# @auth.requires_login()
# @auth.requires(auth.has_membership('root'))
# def import_bedrooms():
#     print 'IMPORT BEDROOMS'
#     print '-' * 80
#     print '1 - reading the file...'
#     import_file = open('applications/register2event/ccpa-aloj.csv','r')
#     lines = import_file.readlines()
#     import_file.close()
#     error_file = open('applications/register2event/import_errors.csv','w')
#     print '2 - try to insert in db'
#     for line in lines:
#         cur_line = line.split(',')
#         new_bedroom = dict(
#             builid=cur_line[0],
#             bedroom=cur_line[1],
#             gender=cur_line[2],
#             floor_room=cur_line[3],
#             beds=cur_line[4],
#             top_bunks=cur_line[5],
#             is_active='T'
#         )
#         try:
#             db.bedroom.insert(**new_bedroom)
#         except:
#             error_file.write(line)
#             print 'error - %s' % cur_line[2]
#     print 'well done!'
