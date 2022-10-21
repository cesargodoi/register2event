#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gluon import *

# kill bedroom mapping
def kill_mapping(evenid):
    current.db(current.db.bedrooms_mapping.evenid == evenid).delete()


# creating and updating bedroom mapping
def update_mapping(evenid):
    event = current.db(current.db.events.id == evenid).select().first()
    buildings = current.db(
        (current.db.building.center == event.center)
        & (current.db.building.is_active == True)
    ).select()
    mapping = (
        current.db(current.db.bedrooms_mapping.evenid == evenid)
        .select()
        .first()
    )
    if mapping:
        # bedrooms in mapp
        mapp_ids = [int(b[0]) for b in mapping["bedrooms"]]
        # bedrooms in building
        bedrooms_in_building_ids = []
        for building in buildings:
            _ids = [
                int(b.id) for b in building.bedroom.select() if b.is_active
            ]
            bedrooms_in_building_ids += _ids
        # add or remove from mapping
        to_add = [b for b in bedrooms_in_building_ids if b not in mapp_ids]
        to_remove = [b for b in mapp_ids if b not in bedrooms_in_building_ids]
        new_mapping = mapping["bedrooms"][:]
        if to_add:
            bedrooms = current.db(
                current.db.bedroom.id.belongs(to_add)
            ).select()
            bedrooms_to_add = []
            for b in bedrooms:
                if b.is_active:
                    _bedroom = [
                        int(b.id),
                        [0 for i in range(b.beds)],
                        [0 for i in range(b.top_bunks)],
                        b.gender,
                        int(b.floor_room),
                        b.bedroom,
                    ]
                    bedrooms_to_add.append(_bedroom)
            new_mapping += bedrooms_to_add
        if to_remove:
            for b in to_remove:
                attempt_deallocation(b, mapping["bedrooms"], event)
            new_mapping = [
                b for b in new_mapping if int(b[0]) not in to_remove
            ]
        # update bedrooms_mapping
        if new_mapping != mapping["bedrooms"]:
            mapping.update_record(bedrooms=(new_mapping))
    else:
        bedrooms = []
        for building in buildings:
            for bedroom in building.bedroom.select():
                if bedroom.is_active:
                    _bedroom = [
                        int(bedroom.id),
                        [0 for i in range(bedroom.beds)],
                        [0 for i in range(bedroom.top_bunks)],
                        bedroom.gender,
                        int(bedroom.floor_room),
                        bedroom.bedroom,
                    ]
                    bedrooms.append(_bedroom)
        # insert bedrooms_mapping
        current.db.bedrooms_mapping.insert(
            centid=event.center, evenid=event.id, bedrooms=bedrooms
        )


def attempt_deallocation(b, mapping, event):
    bedroom = [m for m in mapping if m[0] == b][0]
    to_deallocation = [x for x in bedroom[1] + bedroom[2] if x != 0]
    if to_deallocation:
        for g in to_deallocation:
            register = (
                current.db(
                    (current.db.register.guesid == g)
                    & (current.db.register.evenid == event.id)
                )
                .select()
                .first()
            )
            register.update_record(bedroom=None)
            guest_stay = (
                current.db(
                    (current.db.guest_stay.guesid == g)
                    & (current.db.guest_stay.center == event.center)
                )
                .select()
                .first()
            )
            guest_stay.update_record(bedroom=None)


# working with session.mapp
def init_mapp(evenid, centid, cent_repr):
    from gluon.storage import Storage

    current.session.mapp = Storage()
    current.session.mapp.evenid = evenid
    current.session.mapp.centid = centid
    current.session.mapp.cent_repr = cent_repr
    current.session.mapp.unallocateds = unallocateds(evenid)
    mapping = (
        current.db(current.db.bedrooms_mapping.evenid == evenid)
        .select()
        .first()
        .bedrooms
    )  # ['bedrooms']
    current.session.mapp.mapping = mapping
    current.session.mapp.ids_in_mapping = [b[0] for b in mapping]
    current.session.mapp.difference = False


def unallocateds(evenid):
    from datetime import date

    query = (
        (current.db.register.evenid == evenid)
        & (current.db.register.lodge == "LDG")
        & (current.db.register.is_active == True)
    )

    regs = [
        g for g in current.db(query).select() if not g.credit and not g.bedroom
    ]
    guests_unallocated = []
    for reg in regs:
        _guest = dict(
            id=int(reg.guesid),
            name=reg.guesid.name,
            gender=reg.guesid.gender,
            no_stairs=reg.no_stairs,
            no_top_bunk=reg.no_top_bunk,
            age=(date.today() - reg.guesid.birthday).days // 365
            if reg.guesid.birthday
            else "",
            regid=int(reg.id),
        )
        guests_unallocated.append(_guest)
    return guests_unallocated


def unallocateds_by_gender(gender):
    if gender == "X":
        _unallocateds = [un for un in current.session.mapp.unallocateds]
    else:
        _unallocateds = [
            un
            for un in current.session.mapp.unallocateds
            if un["gender"] == gender
        ]
    return _unallocateds


def compare_mapping_and_bedrooms(mapp):
    mapping = [int(m.id) for m in mapp]
    bedrooms = [
        int(b.id)
        for b in current.db(
            (current.db.bedroom.id > 0)
            & (current.db.bedroom.is_active == True)
        ).select()
    ]
    mapping.sort()
    bedrooms.sort()
    if mapping != bedrooms:
        current.session.mapp.difference = True


def add_mapp(_id):
    return [[m[1], m[2]] for m in current.session.mapp.mapping if m[0] == _id][
        0
    ]


def get_bedrooms(rows, gender):
    return [[row.id] for row in rows if row.gender == gender and row.is_active]


def gen_mapp_buildings(rows):
    total, in_use = 0, 0
    for row in rows:
        total += int(row.beds + row.top_bunks)
        in_use += int(
            len([x for x in row.mapp[0] if x != 0])
            + len([x for x in row.mapp[1] if x != 0])
        )
    return (total, in_use, (total - in_use))


def gen_mapp_building(rows):
    bedrooms, total_beds, total_tops, beds_in_use, tops_in_use = 0, 0, 0, 0, 0
    for row in rows:
        bedrooms += 1
        total_beds += int(row.beds)
        total_tops += int(row.top_bunks)
        beds_in_use += len([x for x in row.mapp[0] if x != 0])
        tops_in_use += len([x for x in row.mapp[1] if x != 0])
    return (
        bedrooms,
        total_beds,
        beds_in_use,
        (total_beds - beds_in_use),
        total_tops,
        tops_in_use,
        (total_tops - tops_in_use),
    )


def gen_mapp_gender(row, mapp):
    return (
        len([x for x in mapp[0] if x != 0]),
        len([x for x in mapp[1] if x != 0]),
    )


def icons_mapp(row):
    bedroom = dict(id=row.id, name=row.bedroom, floor=row.floor_room)
    beds, tops, bedroom_list = [], [], []
    for n in range(row.beds):
        _beds = "N" if n in range(row.in_use[0]) else "Y"
        beds.append(_beds)
    for n in range(row.top_bunks):
        _tops = "N" if n in range(row.in_use[1]) else "Y"
        tops.append(_tops)
    for n in range(row.beds):
        if row.top_bunks > 0:
            if n in range(row.top_bunks):
                bed_type = "%s%s" % (beds[n], tops[n])
            else:
                bed_type = "%s" % beds[n]
            bedroom_list.append(bed_type)
        else:
            bed_type = "%s" % beds[n]
            bedroom_list.append(bed_type)
    bedroom["mapp"] = bedroom_list
    return bedroom


def choose_a_bed(evenid, guesid, bedroomid, regid, event_type, from_mapp=True):
    # select event
    event = current.db(current.db.events.id == evenid).select().first()
    # select guest stay
    guest_stay = (
        current.db(
            (current.db.guest_stay.guesid == guesid)
            & (current.db.guest_stay.center == event.center)
        )
        .select()
        .first()
    )
    # select register
    register = current.db.register[regid]
    # select mapping
    mapping = (
        current.db(current.db.bedrooms_mapping.evenid == evenid)
        .select()
        .first()
    )
    # select bedroom
    bedroom = [m for m in mapping.bedrooms if m[0] == bedroomid][0]
    # attempt
    attempt = False
    if register.no_top_bunk:
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
    if attempt:
        mapping.update_record(bedrooms=mapping.bedrooms)
        register.update_record(bedroom=bedroomid)
        if event_type == "SCF":
            guest_stay.update_record(bedroom_alt=bedroomid)
        else:
            guest_stay.update_record(bedroom=bedroomid)
        if from_mapp:  # ????????????????????????????????????????????????????
            init_mapp(
                evenid=evenid,
                centid=current.session.mapp.centid,
                cent_repr=current.session.mapp.cent_repr,
            )
    return attempt


def put_on_a_bedroom(guest, bedrooms):
    summary = []
    for bedroom in bedrooms:
        if guest["no_top_bunk"]:
            if 0 in bedroom[1]:
                bedroom[1].remove(0)
                bedroom[1].append(guest["id"])
                bedroom[1].sort(reverse=True)
                summary = [
                    guest["id"],
                    guest["name"],
                    bedroom[0],
                    bedroom[5],
                    "bed",
                ]
                break
        else:
            if 0 in bedroom[2]:
                bedroom[2].remove(0)
                bedroom[2].append(guest["id"])
                bedroom[2].sort(reverse=True)
                summary = [
                    guest["id"],
                    guest["name"],
                    bedroom[0],
                    bedroom[5],
                    "top",
                ]
                break
            elif 0 in bedroom[1]:
                bedroom[1].remove(0)
                bedroom[1].append(guest["id"])
                bedroom[1].sort(reverse=True)
                summary = [
                    guest["id"],
                    guest["name"],
                    bedroom[0],
                    bedroom[5],
                    "bed",
                ]
                break
    return summary
