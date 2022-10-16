# -*- coding: utf-8 -*-


# List (by gender)
@auth.requires_login()
def list_bedrooms_by_gender():
    builid = request.vars.builid
    gender = request.vars.gender
    bedrooms = db((Bedroom.builid == builid) & (Bedroom.gender == gender)).\
        select(orderby=[~Bedroom.floor_room, Bedroom.bedroom])
    return dict(rows=bedrooms,
                gender=gender)


# Create
@auth.requires_login()
@auth.requires(auth.has_membership('root') or
               auth.has_membership('admin'))
def new_bedroom():
    builid = int(request.vars.builid[0]) if isinstance(
        request.vars.builid, list) else int(request.vars.builid)
    gender = request.vars.gender[0] if isinstance(
        request.vars.gender, list) else request.vars.gender
    new = SQLFORM(Bedroom, submit_button="add")
    new.element(_id="bedroom_builid__row")["_style"] = "display:none;"
    new.element("option", _value=builid)['_selected'] = "selected"
    if request.vars.gender:
        new.element("option", _value=gender)['_selected'] = "selected"
    new.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if new.process().accepted:
        bid = int(new.process().vars.builid)
        building = Building[bid]
        if not building.is_active:
            building.update_record(is_active=True)
            db.commit()
        redirect(URL('building', 'show_building', vars={'builid': bid}))
    return dict(form=new)


# Read
@auth.requires_login()
def show_bedroom():
    bedroomid = request.vars.bedroomid
    bedroom = Bedroom[bedroomid] or redirect(URL('list_buildings'))
    return dict(bedroom=bedroom)


# Update
@auth.requires_login()
@auth.requires(auth.has_membership('root') or
               auth.has_membership('admin'))
def edit_bedroom():
    bedroomid = int(request.vars.bedroomid[0]) if isinstance(
        request.vars.bedroomid, list) else int(request.vars.bedroomid)
    edit = SQLFORM(Bedroom, bedroomid, submit_button="update")
    edit.element(_id="bedroom_id__row")["_style"] = "display:none;"
    edit.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if edit.process().accepted:
        redirect(URL('show_bedroom', vars={'bedroomid': bedroomid}))
    return dict(form=edit)


# Delete
@auth.requires_login()
@auth.requires(auth.has_membership('root') or
               auth.has_membership('admin'))
def delete_bedroom():
    # receiving the variables
    bedroomid = int(request.vars.bedroomid)
    builid = request.vars.builid
    # selecting building
    bedroom = Bedroom[bedroomid]
    building = Building[builid]
    # selecting mappings for this center
    mappings = db(Bedrooms_mapping.centid == building.center).select()
    bedrooms_in_mapp = []
    for mapps in mappings:
        _id = [int(m.keys()[0]) for m in mapps['bedrooms']]
        bedrooms_in_mapp += _id
    # verifying if bedroom is on mapping
    if bedroomid in bedrooms_in_mapp:
        # making this bedroom inactive
        bedroom.update_record(is_active=False)
        db.commit()
        return 'window.location = document.referrer;'
    else:
        # delete this bedroom
        bedroom.delete_record()
        db.commit()
        # verifying if building is on mapping
        if len(building.bedroom.select()) == 0:
            building.update_record(is_active=False)
        return 'location.href="%s";' % URL('building', 'list_buildings')


# bedroom is_active (on / off)
@auth.requires_login()
@auth.requires(auth.has_membership('root') or
               auth.has_membership('admin'))
def bedroom_on_off():
    bedroom = Bedroom[request.vars.bedroomid]
    bedroom.update_record(is_active=not bedroom.is_active)
    return 'window.location = document.referrer;'
