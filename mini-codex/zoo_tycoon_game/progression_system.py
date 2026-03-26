UNLOCKS = [('petting_zoo', 100), ('aquarium_wing', 250), ('night_safari', 400), ('vip_ride', 600)]

def calc_prestige(stars):
    return stars * 10

def unlock_check(feature, pts):
    req = dict(UNLOCKS).get(feature, 9999)
    return {'unlocked': pts >= req, 'required': req, 'gap': max(0, req - pts)}