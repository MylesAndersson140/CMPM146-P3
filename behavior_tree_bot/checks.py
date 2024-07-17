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

# ambush take back ally planets

ally_planets = []
just_taken_allies = []

def enemy_just_took_ally(state):
    state_allies = state.my_planets()

    # track any ally planets we weren't tracking before
    for planet in state_allies:
        if planet not in ally_planets:
            ally_planets.append(planet)

    enemy_planets = state.enemy_planets()
    
    # find any planets that were neutral but are no longer neutral and now owned by the enemy
    for planet in ally_planets:
        if planet not in state_allies: # planet no longer neutral
            # search enemy list, and add planet ID if found
            for enemy_planet in enemy_planets:
                if enemy_planet.ID == planet.ID:
                    just_taken_allies.append(planet.ID)

            # remove it from our neutral list
            ally_planets.remove(planet)

    if len(just_taken_allies) > 0:
        return True
    else:
        return False
        
#Used to defend an allied planet if enemy launches an attack

def enemy_attacking(state):
    logging.info("Checking for enemy attacks...")
    logging.info(f"Number of enemy fleets: {len(state.enemy_fleets())}")
    
    for fleet in state.enemy_fleets():
        logging.info(f"Enemy fleet: ships={fleet.num_ships}, " +
                     f"destination={fleet.destination_planet}, " +
                     f"turns_remaining={fleet.turns_remaining}, " +
                     f"total_trip_length={fleet.total_trip_length}")
        
        if fleet.turns_remaining >= fleet.total_trip_length - 2:
            logging.info(f"Enemy attack detected! Fleet of {fleet.num_ships} " +
                         f"ships heading to planet {fleet.destination_planet}")
            return True
    
    logging.info("No enemy attacks detected.")
    return False

# always returns true

def should_distribute_ships(state):
    return True
