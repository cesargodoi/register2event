# -*- coding: utf-8 -*-


# List
@auth.requires_login()
def list_buildings():
    # if exists session.mapp or session.register delete it
    if session.mapp or session.register:
        clear_session()
    # choosing a query
    if auth.has_membership('root'):
        query = (Building.id > 0)
    elif auth.has_membership('admin'):
        query = (Building.id > 0) & (Building.center == auth.user.center)
    else:
        query = (Building.id > 0) & (Building.center == auth.user.center) &\
                (Building.is_active == True)
    # searching on database
    buildings = db(query).select(orderby=Building.center)
    for building in buildings:
        # counting and separating by gender (beds + topbunks)
        building.male = (sum([b.beds for b in building.bedroom.select()
                              if b.gender == 'M']) +
                         sum([b.top_bunks for b in building.bedroom.select()
                              if b.gender == 'M']))
        building.fema = (sum([b.beds for b in building.bedroom.select()
                              if b.gender == 'F']) +
                         sum([b.top_bunks for b in building.bedroom.select()
                              if b.gender == 'F']))
        building.mixd = (sum([b.beds for b in building.bedroom.select()
                              if b.gender == 'X']) +
                         sum([b.top_bunks for b in building.bedroom.select()
                              if b.gender == 'X']))
    return dict(rows=buildings)


# Create
@auth.requires_login()
@auth.requires(auth.has_membership('root') or
               auth.has_membership('admin'))
def new_building():
    # creating a form
    new = SQLFORM(Building, submit_button="add")
    # adjusting the form (by permission types)
    if auth.has_membership('root'):
        new.element("option",
                    _value=int(auth.user.center))['_selected'] = "selected"
    elif auth.user.center:
        new.element(_id="building_center__row")["_style"] = "display:none;"
        new.element("option",
                    _value=int(auth.user.center))['_selected'] = "selected"
        new.element(_id="building_is_active__row")["_style"] = "display:none;"
    new.element(_name="description")["_rows"] = 1
    new.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if new.process().accepted:
        # select the new builid and redirect to show new building
        builid = int(new.process().vars.id)
        redirect(URL('show_building', vars={'builid': builid}))
    return dict(form=new)


# Read
@auth.requires_login()
def show_building():
    # select building
    building = Building[request.vars.builid] or redirect(URL('list_buildings'))
    # making a list of bedrooms by gender
    list_of_bedrooms = {'male': [b for b in building.bedroom.select()
                                 if b.gender == 'M'],
                        'fema': [b for b in building.bedroom.select()
                                 if b.gender == 'F'],
                        'mixd': [b for b in building.bedroom.select()
                                 if b.gender == 'X']}
    return dict(building=building,
                list_of_bedrooms=list_of_bedrooms)


# Update
@auth.requires_login()
@auth.requires(auth.has_membership('root') or
               auth.has_membership('admin'))
def edit_building():
    # creating a form
    edit = SQLFORM(Building, request.vars.builid, submit_button="update")
    # adjusting the form (by permission types)
    if auth.has_membership('root'):
        edit.element(_id="building_id__row")["_style"] = "display:none;"
        edit.element("option",
                     _value=int(auth.user.center))['_selected'] = "selected"
    elif auth.user.center:
        edit.element(_id="building_id__row")["_style"] = "display:none;"
        edit.element(_id="building_center__row")["_style"] = "display:none;"
        edit.element("option",
                     _value=int(auth.user.center))['_selected'] = "selected"
    edit.element(_name="description")["_rows"] = 1
    edit.element(_type="submit")["_class"] = "btn btn-primary btn-lg"
    if edit.process().accepted:
        # redirect to show this building
        redirect(URL('show_building',
                     vars={'builid': int(edit.process().vars.id)}))
    return dict(form=edit,
                builid=request.vars.builid)


# Delete
@auth.requires_login()
@auth.requires(auth.has_membership('root') or
               auth.has_membership('admin'))
def delete_building():
    # receiving the variables
    builid = request.vars.builid
    centid = request.vars.centid
    # selecting building
    building = Building[builid]
    # ... and bedrooms ids
    _ids = [b.id for b in building.bedroom.select()]
    # selecting mappings for this center
    mappings = db(Bedrooms_mapping.centid == centid).select()
    bedrooms_list_on_mapp = []
    for mapps in mappings:
        for mapp in mapps['bedrooms']:
            if long(mapp.keys()[0]) in _ids:
                bedrooms_list_on_mapp.append(long(mapp.keys()[0]))
    # verifying if building is on mapping
    if bedrooms_list_on_mapp:
        # making this building inactive
        building.update_record(is_active=False)
        db.commit()
        return 'window.location = document.referrer;'
    else:
        # delete this building
        building.delete_record()
        db.commit()
        return 'location.href="%s";' % URL('list_buildings')
