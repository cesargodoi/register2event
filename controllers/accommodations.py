# -*- coding: utf-8 -*-

from gluon.custom_import import track_changes
import Mapp_Utils as Mapp

track_changes(True)


# buildings on event
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def buildings_on_event():
    # if exists session.mapping delete it
    if session.mapping:
        clear_session()
    # geting event to render details
    event = Events[request.vars.evenid]
    # init a new mapping
    Mapp.init_mapp(
        evenid=int(event.id),
        centid=int(event.center),
        cent_repr=(center_repr % event.center),
    )
    # get bedrooms
    bedrooms = db(Bedroom.id.belongs(session.mapp.ids_in_mapping)).select(
        orderby=Bedroom.builid
    )
    Mapp.compare_mapping_and_bedrooms(bedrooms)
    for bedroom in bedrooms:
        bedroom.mapp = Mapp.add_mapp(bedroom.id)
    # making buildings
    buildings = db(
        Building.id.belongs(set([b.builid for b in bedrooms]))
    ).select()

    for building in buildings:
        building.male = Mapp.gen_mapp_buildings(
            [
                b
                for b in bedrooms
                if b.gender == "M" and b.builid == building.id
            ]
        )

        building.female = Mapp.gen_mapp_buildings(
            [
                b
                for b in bedrooms
                if b.gender == "F" and b.builid == building.id
            ]
        )

        building.mixed = Mapp.gen_mapp_buildings(
            [
                b
                for b in bedrooms
                if b.gender == "X" and b.builid == building.id
            ]
        )
        building.total = Mapp.get_total_per_building(
            [building.male, building.female, building.mixed]
        )

    _unallocated = session.mapp.unallocateds
    _unallocated.sort(key=lambda r: r["name"])
    return dict(rows=buildings, guests_unallocated=_unallocated, event=event)


# building on event
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def building_on_event():
    # verifying if session.mapp exists
    if not session.mapp:
        redirect(URL("events", "show", vars={"evenid": request.vars.evenid}))

    # geting event to render details
    event = Events[request.vars.evenid]
    # get bedrooms
    bedrooms = db(
        (Bedroom.id.belongs(session.mapp.ids_in_mapping))
        & (Bedroom.builid == request.vars.builid)
    ).select(orderby=Bedroom.builid)

    for bedroom in bedrooms:
        bedroom.mapp = Mapp.add_mapp(bedroom.id)

    # geting the building
    building = Building[request.vars.builid]
    building.male = Mapp.gen_mapp_building(
        [b for b in bedrooms if b.gender == "M"]
    )
    building.female = Mapp.gen_mapp_building(
        [b for b in bedrooms if b.gender == "F"]
    )
    building.mixed = Mapp.gen_mapp_building(
        [b for b in bedrooms if b.gender == "X"]
    )
    return dict(
        building=building,
        guests_unallocated=session.mapp.unallocateds,
        event=event,
    )


# List (by gender)
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def bedrooms_by_gender_on_event():
    # verifying if session.mapp exists
    if not session.mapp:
        redirect(URL("events", "show", vars={"evenid": request.vars.evenid}))
    # geting event to render details
    event = Events[request.vars.evenid]
    # makying a list of guests unallocated by gender
    _unallocateds = Mapp.unallocateds_by_gender(request.vars.gender)
    # get bedrooms
    _bedrooms = db(
        (Bedroom.id.belongs(session.mapp.ids_in_mapping))
        & (Bedroom.builid == request.vars.builid)
        & (Bedroom.gender == request.vars.gender)
    ).select(orderby=~Bedroom.floor_room)
    # create a dict of bedrooms with mapp
    bedrooms = []
    for bedroom in _bedrooms:
        bedroom.in_use = Mapp.gen_mapp_gender(
            bedroom, Mapp.add_mapp(bedroom.id)
        )
        bedrooms.append(Mapp.icons_mapp(bedroom))
    return dict(
        rows=bedrooms,
        guests_unallocated=_unallocateds,
        event=event,
        gender=request.vars.gender,
        builid=_bedrooms[0].builid,
    )


# Read
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def bedroom_on_event():
    from datetime import date

    # verifying if session.mapp exists
    if not session.mapp:
        redirect(URL("events", "show", vars={"evenid": request.vars.evenid}))
    # geting event to render details
    event = Events[request.vars.evenid]
    # makying a list of guests unallocated by gender
    _unallocateds = Mapp.unallocateds_by_gender(request.vars.gender)
    # get mapp
    mapp = [
        m for m in session.mapp.mapping if m[0] == int(request.vars.bedroomid)
    ][0]
    # update bedroom with mapp
    bedroom = Bedroom[int(request.vars.bedroomid)]
    bedroom.beds = mapp[1]
    bedroom.tops = mapp[2]
    # creating a dict of name
    _ids = [x for x in bedroom.beds + bedroom.tops if x != 0]
    guests = {
        r.guesid: dict(
            name=shortname(r.guesid.name),
            no_stairs=r.no_stairs,
            no_top_bunk=r.no_top_bunk,
            age=get_age(r.guesid.birthday) if r.guesid.birthday else "",
        )
        for r in db(Register.guesid.belongs(_ids)).select()
    }
    return dict(
        bedroom=bedroom,
        guests=guests,
        guests_unallocated=_unallocateds,
        event=event,
        building=[bedroom.builid, bedroom.builid.building],
    )


# add or remove from accommodations ###########################################
@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def add_to_bedroom():
    # receiving the variables
    evenid = int(request.vars.evenid)
    event_type = Events[evenid].activity.activity_type
    guesid = int(request.vars.guesid)
    gender = request.vars.gender
    bedroomid = int(request.vars.bedroomid)
    regid = int(request.vars.regid)

    if request.vars.fromguest:
        try_to_allocate = Mapp.choose_a_bed(
            evenid, guesid, bedroomid, regid, event_type, from_mapp=False
        )
    else:
        try_to_allocate = Mapp.choose_a_bed(
            evenid, guesid, bedroomid, regid, event_type
        )
    if try_to_allocate:
        if request.vars.fromguest:
            redirect(
                URL(
                    "events",
                    "show",
                    vars={"evenid": evenid, "admin_view": "T"},
                )
            )
        else:
            return 'location.href="%s";' % URL(
                "bedroom_on_event",
                vars={
                    "bedroomid": bedroomid,
                    "evenid": evenid,
                    "gender": gender,
                },
            )
    else:
        return 'window.alert("crowded bedroom");'


@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def allocate_all():
    # receiving the variables
    evenid = session.mapp.evenid
    event_type = Events[evenid].activity.activity_type
    mapping = db(Bedrooms_mapping.evenid == evenid).select().first()
    bedrooms = [b for b in session.mapp.mapping if 0 in (b[1] + b[2])]
    # sub-lists
    _no_stairs = [b for b in bedrooms if b[4] == 0 and 0 in b[1]]
    _no_top_bunk = sorted(
        [b for b in bedrooms if 0 in b[1]], key=lambda x: x[4], reverse=True
    )
    _no_problems = sorted(bedrooms, key=lambda x: x[4], reverse=True)
    # unallocateds
    guests = session.mapp.unallocateds
    # put each guest on a bedroom
    allocateds, unallocateds = [], []
    for guest in guests:
        if guest["gender"] == "M":
            if guest["no_stairs"]:
                _bedrooms = [b for b in _no_stairs if b[3] == "M"]
            elif guest["no_top_bunk"]:
                _bedrooms = [b for b in _no_top_bunk if b[3] == "M"]
            else:
                _bedrooms = [b for b in _no_problems if b[3] == "M"]
        elif guest["gender"] == "F":
            if guest["no_stairs"]:
                _bedrooms = [b for b in _no_stairs if b[3] == "F"]
            elif guest["no_top_bunk"]:
                _bedrooms = [b for b in _no_top_bunk if b[3] == "F"]
            else:
                _bedrooms = [b for b in _no_problems if b[3] == "F"]
        allocate = Mapp.put_on_a_bedroom(guest, _bedrooms)
        if allocate:
            allocateds.append(allocate)
            register = Register[guest["regid"]]
            register.update_record(bedroom=allocate[2])
            guest_stay = (
                db(
                    (Guest_Stay.guesid == guest["id"])
                    & (Guest_Stay.center == session.mapp.centid)
                )
                .select()
                .first()
            )
            if event_type == "SCF":
                guest_stay.update_record(bedroom_alt=allocate[2])
            else:
                guest_stay.update_record(bedroom=allocate[2])
        else:
            unallocateds.append([guest["id"], guest["name"]])
    mapping.update_record(bedrooms=session.mapp.mapping)
    return dict(
        evenid=evenid,
        allocateds=sorted(allocateds, key=lambda x: x[1]),
        unallocateds=sorted(unallocateds, key=lambda x: x[1]),
    )


@auth.requires_login()
@auth.requires(
    auth.has_membership("root")
    or auth.has_membership("admin")
    or auth.has_membership("office")
)
def remove_from_bedroom():
    # receiving the variables
    evenid = int(request.vars.evenid)
    guesid = int(request.vars.guesid)
    bedroomid = int(request.vars.bedroomid)
    # select event and type
    event = Events[evenid]
    event_type = event.activity.activity_type
    # select guest stay
    guest_stay = (
        db((Guest_Stay.guesid == guesid) & (Guest_Stay.center == event.center))
        .select()
        .first()
    )
    # select register
    register = (
        db(
            (Register.guesid == guesid)
            & (Register.evenid == evenid)
            & (Register.is_active == True)
            & (Register.credit == False)
        )
        .select()
        .first()
    )
    # select mapping in DB
    mapping = db(Bedrooms_mapping.evenid == evenid).select().first()
    bedroom = [mapp for mapp in mapping["bedrooms"] if mapp[0] == bedroomid][0]
    # remove guest from bedroom
    if guesid in bedroom[1]:
        bedroom[1].remove(guesid)
        bedroom[1].append(0)
    elif guesid in bedroom[2]:
        bedroom[2].remove(guesid)
        bedroom[2].append(0)
    # update DB(s)
    mapping.update_record(bedrooms=mapping["bedrooms"])
    if register:
        register.update_record(bedroom=None)
    if event_type == "SCF":
        guest_stay.update_record(bedroom_alt=None)
    else:
        guest_stay.update_record(bedroom=None)
    if request.vars.fromguest:
        return 'location.href="%s";' % URL(
            "events", "show", vars={"evenid": evenid, "admin_view": "T"}
        )
    else:
        # re-init the Mapp
        Mapp.init_mapp(
            evenid=int(event.id),
            centid=session.mapp.centid,
            cent_repr=session.mapp.cent_repr,
        )
        return 'location.href="%s";' % URL(
            "bedroom_on_event",
            vars={
                "bedroomid": bedroomid,
                "evenid": evenid,
                "gender": register.guesid.gender,
            },
        )


#  guest bedroom  #############################################################
@auth.requires_login()
@auth.requires(auth.has_membership("root") or auth.has_membership("admin"))
def guest_bedroom():
    from datetime import date

    bedroom = get_bedroom(request.vars.evenid, request.vars.guesid)
    if bedroom:
        _ids = [x for x in bedroom[1] + bedroom[2] if x != 0]
        guests = {
            int(r.guesid): dict(
                name=shortname(r.guesid.name),
                no_stairs=r.no_stairs,
                no_top_bunk=r.no_top_bunk,
                age=get_age(r.guesid.birthday) if r.guesid.birthday else "",
            )
            for r in db(Register.guesid.belongs(_ids)).select()
        }
        _building = Bedroom[bedroom[0]].builid.building
        title = f"{_building} - {bedroom[5]}"
        beds, tops = [], []
        for b in bedroom[1]:
            if b == 0:
                bed = [
                    IMG(
                        _src=URL(
                            "static", "images/bedicons", args="bed_BY.png"
                        ),
                        _alt="cama de baixo",
                        _width="22px",
                    ),
                    "livre",
                    "",
                    "",
                ]
            else:
                if guests[b]["age"] > 35 and guests[b]["age"] < 60:
                    label = "label label-warning"
                elif guests[b]["age"] >= 60:
                    label = "label label-danger"
                else:
                    label = "label label-success"
                bed = [
                    IMG(
                        _src=URL(
                            "static", "images/bedicons", args="bed_BN.png"
                        ),
                        _alt="cama de baixo",
                        _width="22px",
                    ),
                    DIV(
                        guests[b]["name"],
                        XML("&nbsp;&nbsp;"),
                        A(
                            "remover",
                            _type="button",
                            _class="btn btn-danger btn-xs",
                            _href="#",
                            _onclick="removeFromBedroom(%s, %s, %s)"
                            % (
                                request.vars.evenid,
                                request.vars.guesid,
                                bedroom[0],
                            ),
                            **{"_data-dismiss": "modal"},
                        )
                        if b == int(request.vars.guesid)
                        else "",
                    ),
                    SPAN(guests[b]["age"], _class=label),
                ]
            beds.append(bed)
        for t in bedroom[2]:
            if t == 0:
                top = [
                    IMG(
                        _src=URL(
                            "static", "images/bedicons", args="bed_TY.png"
                        ),
                        _alt="cama de cima",
                        _width="22px",
                    ),
                    "livre",
                    "",
                ]
            else:
                if guests[t]["age"] > 35 and guests[t]["age"] < 60:
                    label = "label label-warning"
                elif guests[t]["age"] >= 60:
                    label = "label label-danger"
                else:
                    label = "label label-success"
                top = [
                    IMG(
                        _src=URL(
                            "static", "images/bedicons", args="bed_TN.png"
                        ),
                        _alt="cama de cima",
                        _width="22px",
                    ),
                    DIV(
                        guests[t]["name"],
                        XML("&nbsp;&nbsp;"),
                        A(
                            "remover",
                            _type="button",
                            _class="btn btn-danger btn-xs",
                            _href="#",
                            _onclick="removeFromBedroom(%s, %s, %s)"
                            % (
                                request.vars.evenid,
                                request.vars.guesid,
                                bedroom[0],
                            ),
                            **{"_data-dismiss": "modal"},
                        )
                        if t == int(request.vars.guesid)
                        else "",
                    ),
                    SPAN(guests[t]["age"], _class=label),
                ]
            tops.append(top)
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
                    TABLE(
                        TR(TH("camas de baixo", _colspan="4")),
                        *[TR(*bed) for bed in beds],
                        _class="table table-condenced",
                    ),
                    TABLE(
                        TR(TH("camas de cima", _colspan="3")),
                        *[TR(*top) for top in tops],
                        _class="table table-condenced",
                    ),
                    _class="modal-body",
                ),
                _class="modal-content",
            ),
            _class="modal-dialog",
            _role="document",
        )
    else:
        mapping = (
            db(Bedrooms_mapping.evenid == int(request.vars.evenid))
            .select()
            .first()
        )
        register = (
            db(
                (Register.guesid == int(request.vars.guesid))
                & (Register.evenid == int(request.vars.evenid))
                & (Register.is_active == True)
                & (Register.credit == False)
            )
            .select()
            .first()
        )
        if register.guesid.gender == "M":
            get_gender = [
                m
                for m in mapping["bedrooms"]
                if m[3] in ("M", "X") and 0 in (m[1] + m[2])
            ]
        else:
            get_gender = [
                m
                for m in mapping["bedrooms"]
                if m[3] in ("F", "X") and 0 in (m[1] + m[2])
            ]
        if register.no_top_bunk and register.no_stairs:
            restricts = [m for m in get_gender if m[4] == 0 and 0 in m[1]]
        elif register.no_top_bunk:
            restricts = [m for m in get_gender if 0 in m[1]]
        else:
            restricts = get_gender
        ids = [r[0] for r in restricts]
        _vacancies = db(Bedroom.id.belongs(ids)).select()
        VACANCIES = dict()
        for vac in _vacancies:
            VACANCIES[int(vac.id)] = "%s(%s) - %s(%s) [%dB %dT]" % (
                vac.builid.building,
                vac.builid.center.shortname,
                vac.bedroom,
                GENDER_BEDROOM[vac.gender],
                vac.beds,
                vac.top_bunks,
            )

        form = SQLFORM.factory(
            Field(
                "bedroomid", requires=IS_IN_SET(VACANCIES), label=T("bedroom")
            ),
            hidden=dict(
                evenid=request.vars.evenid,
                guesid=request.vars.guesid,
                gender=register.guesid.gender,
                regid=register.id,
                fromguest=True,  # ???????????????????????????????????????????
            ),
            submit_button="select",
        )
        form.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
        form.element("form")["_action"] = URL(
            "accommodations", "add_to_bedroom"
        )
        return DIV(
            DIV(
                DIV(
                    A(
                        SPAN(XML("&times;"), **{"_aria-hidden": "true"}),
                        _type="button",
                        _class="close",
                        **{"_data-dismiss": "modal", "_aria-label": "Close"},
                    ),
                    H4("Quartos disponíveis", _class="modal-title"),
                    _class="modal-header",
                ),
                DIV(form, _class="modal-body"),
                _class="modal-content",
            ),
            _class="modal-dialog",
            _role="document",
        )
