def hunt_category(threat_level):

    if threat_level < 7:
        return 'Neutral/Elemental'
    elif threat_level < 13:
        return 'Dire'
    elif threat_level < 16:
        return 'Heroic'
    elif threat_level < 22:
        return 'Heroic+'