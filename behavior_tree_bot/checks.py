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

def check_if_enemy_sent_ships(state):
    # TODO
    return False

def check_if_enemy_took_neutral(state):
    # TODO
    return False
