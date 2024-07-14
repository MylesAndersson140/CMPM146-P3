import logging

# sample checks

def if_neutral_planet_available(state):
    return any(state.neutral_planets())


def have_largest_fleet(state):
    return sum(planet.num_ships for planet in state.my_planets()) \
             + sum(fleet.num_ships for fleet in state.my_fleets()) \
           > sum(planet.num_ships for planet in state.enemy_planets()) \
             + sum(fleet.num_ships for fleet in state.enemy_fleets())

# custom checks

enemy_ships = []
new_enemy_ships = []

def enemy_just_sent_ships(state):
    for fleet in state.enemy_fleets():
        if fleet not in enemy_ships:
            new_enemy_ships.append(fleet)

    if len(new_enemy_ships) > 0:
        return True
    else:
        return False

# used for the ambush behavior

neutral_planets = []
just_taken_planets = []

def enemy_just_took_neutral(state):
    state_neutrals = state.neutral_planets()

    # track any neutral planets we weren't tracking before (this only really does anything the first time its ran)
    for planet in state_neutrals:
        if planet not in neutral_planets:
            neutral_planets.append(planet)

    enemy_planets = state.enemy_planets()
    
    # find any planets that were neutral but are no longer neutral and now owned by the enemy
    for planet in neutral_planets:
        if planet not in state_neutrals: # planet no longer neutral
            # search enemy list, and add planet ID if found
            for enemy_planet in enemy_planets:
                if enemy_planet.ID == planet.ID:
                    just_taken_planets.append(planet.ID)

            # remove it from our neutral list
            neutral_planets.remove(planet)

    if len(just_taken_planets) > 0:
        return True
    else:
        return False
