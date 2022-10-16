# -*- coding: utf-8 -*-

from gluon.custom_import import track_changes
import Mapp_Utils as Mapp

track_changes(True)


# Create
@auth.requires_login()
@auth.requires(auth.has_membership('root') or
               auth.has_membership('admin'))
def new_mapping():
    query = (Events.id > 0) if auth.has_membership('root') else \
            (Events.id > 0) & (Events.center == auth.user.center)
    events = db(query).select()
    EVENTS_LIST = dict()
    for ev in events:
        ev_repr = '%s(%s) - [%s-%s]'
        EVENTS_LIST[ev.id] = ev_repr % \
            (ev.activity.activity,
             (center_abbr % ev.center),
             ev.start_date.strftime('%d/%m/%y'),
             ev.end_date.strftime('%d/%m/%y'))
    new = SQLFORM.factory(Field('evenid', requires=IS_IN_SET(
        EVENTS_LIST), label=T('event')), submit_button='adjust')
    new.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if new.process().accepted:
        evenid = int(request.vars.evenid[0]) if isinstance(
            request.vars.evenid, list) else int(request.vars.evenid)
        Mapp.kill_mapping(evenid)
        Mapp.update_mapping(evenid)
        redirect(URL('accommodations', 'buildings_on_event',
                     vars={'evenid': evenid}))
    return dict(form=new)


def ajax_update_mapping():
    Mapp.update_mapping(request.vars.evenid)
    return 'window.location.reload();'
