import sys
sys.path.insert(0, '../')
from planet_wars import issue_order
import logging
from math import ceil

# sample behaviors


def attack_weakest_enemy_planet(state):
    # (1) If we currently have a fleet in flight, abort plan.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda t: t.num_ships, default=None)

    # (3) Find the weakest enemy planet.
    weakest_planet = min(state.enemy_planets(), key=lambda t: t.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)


def spread_to_weakest_neutral_planet(state):
    # (1) If we currently have a fleet in flight, just do nothing.
    if len(state.my_fleets()) >= 1:
        return False

    # (2) Find my strongest planet.
    strongest_planet = max(state.my_planets(), key=lambda p: p.num_ships, default=None)

    # (3) Find the weakest neutral planet.
    weakest_planet = min(state.neutral_planets(), key=lambda p: p.num_ships, default=None)

    if not strongest_planet or not weakest_planet:
        # No legal source or destination
        return False
    else:
        # (4) Send half the ships from my strongest planet to the weakest enemy planet.
        return issue_order(state, strongest_planet.ID, weakest_planet.ID, strongest_planet.num_ships / 2)


# custom behavior

from behavior_tree_bot.checks import just_taken_planets, just_taken_allies

# modified spread (favor close by neutrals)
# using a scoring system to find the most favorable move

def spread_to_weakest_neutral_planet(state):
    offense = state.my_planets()
    offense.sort(key=lambda p: (p.num_ships, p.growth_rate), reverse=True)

    neutrals = state.neutral_planets()

    scores = []

    for planet in offense:
        # make sure the offensive planet isnt currently under attack
        under_attack = False
        for fleet in state.enemy_fleets():
            if fleet.destination_planet == planet:
                under_attack = True
                break

        if under_attack:
            continue

        neutrals.sort(key=lambda p: (p.num_ships, state.distance(p.ID, planet.ID)))

        for neutral in neutrals:
            already_ship = False
            for fleet in state.my_fleets():
                if fleet.destination_planet == neutral.ID:
                    already_ship = True
                    break

            if already_ship:
                continue
            
            dist = state.distance(planet.ID, neutral.ID)

            # cap the furthest an attack can be made
            if dist > 7:
                continue
            
            num_ships = neutral.num_ships + (neutral.num_ships * 0.50)

            # make sure the planet doesnt send more than 35% of its ships
            if planet.num_ships - num_ships <= planet.num_ships * 0.65:
                continue

            score = 1 / (planet.num_ships - num_ships) + dist

            scores.append((score, planet.ID, neutral.ID, ceil(num_ships)))

    scores.sort()

    if len(scores) == 0:
        return False

    (_, offense, target, ships) = scores[0];

    return issue_order(state, offense, target, ships)

# we may also want to use this functionality for ally planets too, so
# if the enemy takes an allied planet, we can ambush them immediately afterwards
def ambush_enemy_on_take_neutral(state):
    # take next taken planet off queue to process
    # note that we may want to push this planet back onto the just_taken queue if we choose
    # not to ambush it, as it could be that in a few turns we have a large enough arsenal to launch
    # a delayed ambush, but for now we can just stick with this
    just_taken_id = just_taken_planets.pop()

    # find planet in enemy planets
    taken_planet = None
    
    for planet in state.enemy_planets():
        if planet.ID == just_taken_id:
            taken_planet = planet
            break

    # just taken planet not found?
    # havent ecountered this yet, but if it happens something catastrophic happened
    if taken_planet == None:
        logging.info('taken planet not found with ID ' + str(just_taken_id))
        return False

    # now we need to sort our planets by ship count and distance to the taken planet
    planets = state.my_planets()
    planets.sort(key=lambda p: (state.distance(p.ID, taken_planet.ID), 1 / (p.num_ships if p.num_ships > 0 else 1)))

    for offense_planet in planets:
        distance_to_target = state.distance(offense_planet.ID, taken_planet.ID)

        if distance_to_target > 10:
            return False

        # tunable numbers
        ambush_safety_buffer = 0.20 # extra ships to help secure defense after taking a planet
        offense_planet_safety = 0.50 # we should never send more than this amount of offensive planet's ship count

        # for now, ill assume we need target-planet ship count + 20% to take it over effectively
        # this also accounts for how long it will take our ships to reach the destination, and the growth
        # rate of the target planet
        taken_planet_ships = taken_planet.num_ships + (taken_planet.growth_rate * distance_to_target)
        needed_ships = taken_planet_ships + (taken_planet_ships * ambush_safety_buffer)

        # next, we can decide if the number of ships difference < 50%
        if (offense_planet.num_ships - needed_ships) > (offense_planet.num_ships * offense_planet_safety):
            logging.info('AMBUSHING PLANET: ' + str(distance_to_target) + 'd away with ' + str(needed_ships) + ' ships (' + str(offense_planet.num_ships) + ' arsenal)')
            return issue_order(state, offense_planet.ID, taken_planet.ID, needed_ships)
        else:
            logging.info('not ambushing planet: ' + str(distance_to_target) + 'd away with ' + str(needed_ships) + ' ships (' + str(offense_planet.num_ships) + ' arsenal)')

    return False


def ambush_enemy_on_take_ally(state):
    just_taken_id = just_taken_allies.pop()

    taken_planet = None
    
    for planet in state.enemy_planets():
        if planet.ID == just_taken_id:
            taken_planet = planet
            break

    if taken_planet == None:
        logging.info('taken planet not found with ID ' + str(just_taken_id))
        return False

    planets = state.my_planets()
    planets.sort(key=lambda p: (state.distance(p.ID, taken_planet.ID), 1 / (p.num_ships if p.num_ships > 0 else 1)))

    for offense_planet in planets:
        distance_to_target = state.distance(offense_planet.ID, taken_planet.ID)

        # tunable numbers
        ambush_safety_buffer = 0.20 # extra ships to help secure defense after taking a planet
        offense_planet_safety = 0.50 # we should never send more than this amount of offensive planet's ship count

        taken_planet_ships = taken_planet.num_ships + (taken_planet.growth_rate * distance_to_target)
        needed_ships = taken_planet_ships + (taken_planet_ships * ambush_safety_buffer)

        if (offense_planet.num_ships - needed_ships) > (offense_planet.num_ships * offense_planet_safety):
            logging.info('AMBUSHING PLANET: ' + str(distance_to_target) + 'd away with ' + str(needed_ships) + ' ships (' + str(offense_planet.num_ships) + ' arsenal)')
            return issue_order(state, offense_planet.ID, taken_planet.ID, needed_ships)
        else:
            logging.info('not ambushing planet: ' + str(distance_to_target) + 'd away with ' + str(needed_ships) + ' ships (' + str(offense_planet.num_ships) + ' arsenal)')

    return False

# Custom behavior to defend planets

def defend_planets(state):
    for fleet in state.enemy_fleets():
        # Check if this fleet was launched recently
        if fleet.turns_remaining == fleet.total_trip_length:
            logging.info(f"Potential attack detected: Fleet of {fleet.num_ships} ships heading to planet {fleet.destination_planet}")
            
            target_planet = next((p for p in state.planets if p.ID == fleet.destination_planet), None)
            
            if not target_planet:
                logging.info(f"Target planet {fleet.destination_planet} not found")
                continue
            
            logging.info(f"Target planet {target_planet.ID} owner: {target_planet.owner}")
            
            # Check if the target planet is ours
            if target_planet.owner == 1:
                # Calculate how many ships we need to defend
                ships_needed = fleet.num_ships + 1
                logging.info(f"Ships needed to defend: {ships_needed}")
                
                # Find the closest planet that can send enough ships
                potential_defenders = sorted(state.my_planets(), 
                                             key=lambda p: state.distance(p.ID, target_planet.ID))
                
                logging.info(f"Number of potential defender planets: {len(potential_defenders)}")
                
                for defender in potential_defenders:
                    logging.info(f"Potential defender planet {defender.ID} has {defender.num_ships} ships")
                    if defender.num_ships > ships_needed:
                        # Send ships to defend
                        logging.info(f'Defending planet {target_planet.ID} from attack. Sending {ships_needed} ships from planet {defender.ID}')
                        return issue_order(state, defender.ID, target_planet.ID, ships_needed)
                
                logging.info("No suitable defender planet found")
            else:
                logging.info(f"Planet {target_planet.ID} is not ours, not defending")
    
    logging.info("No planets to defend")
    return False

# ship distribution

def distribute_ships(state):
    planets = state.my_planets()
    planets.sort(key=lambda p: (p.num_ships, p.growth_rate))

    logging.info('checking for distribution')

    if len(planets) < 2:
        return False

    logging.info('at least 2 planets')

    for weakest_planet in planets:
        planets.remove(weakest_planet)

        already_dist = False
        for fleet in state.my_fleets():
            if fleet.destination_planet == weakest_planet.ID:
                already_dist = True
                break

        if already_dist:
            continue

        logging.info('weakest planet has ' + str(weakest_planet.num_ships) + ' ships')

        planets.sort(key=lambda p: state.distance(weakest_planet.ID, p.ID))

        for planet in planets:
            dist = state.distance(planet.ID, weakest_planet.ID)
            ships_to_send = planet.num_ships / 2 - (weakest_planet.num_ships + weakest_planet.growth_rate * dist)

            logging.info('need to send ' + str(ships_to_send) + '/' + str(planet.num_ships) + ' ships (' + str(dist) + ') with ' + str(weakest_planet.num_ships) + ' ships')


            if ships_to_send >= 1:
                logging.info('distributing')

                return issue_order(state, planet.ID, weakest_planet.ID, ships_to_send)

    return False

#Custom behavior to attack smallest enemy planet

# Helper function to find the strength of a planet upon attack arrival.
def effective_strength(state, my_planet, enemy_planet):
    distance = state.distance(my_planet.ID, enemy_planet.ID)
    growth_during_travel = enemy_planet.growth_rate * distance
    return enemy_planet.num_ships + growth_during_travel

# Function to attack the weakest enemy/neutral planet, accounts for distance, enemy growth rate, and defense.
def attack_weakest_planet_in_proximity(state):
    my_planets = state.my_planets()
    enemy_planets = state.enemy_planets()
    neutral_planets = state.neutral_planets()
    
    if not my_planets:
        return False
    
    # Parameters (we can adjust these)
    max_dist = 12 # Maximum distance to consider for attack
    reserves = 0.2#91  # Proportion of ships to keep as reserve, Ive tried .4 and .6 and in both cases everything breaks LOL
    #0.2 works for test 1,2,3
    for my_planet in my_planets:
        # Finding nearby planets that are eligable for attacking
        nearby_targets = [p for p in enemy_planets + neutral_planets 
                          if state.distance(my_planet.ID, p.ID) <= max_dist]
        
        if not nearby_targets:
            # Nothing found
            continue
        
        # Find the weakest nearby planet
        # target_planet = min(nearby_targets, 
                            # key=lambda p: effective_strength(state, my_planet, p))

        for target_planet in nearby_targets:
            already_attacking = False
            for fleet in state.my_fleets():
                if fleet.destination_planet == target_planet.ID:
                    already_attacking = True
                    break

            if already_attacking:
                continue
            
            # Number of ships needed for a successful attack
            ships_needed = effective_strength(state, my_planet, target_planet) * 1.20
        
            # Check if we have enough ships to attack while maintaining a proper defense.
            available_ships = my_planet.num_ships * (1 - reserves)
        
            if available_ships > ships_needed:
                logging.info(f"Attacking from planet {my_planet.ID} to {target_planet.ID} "
                             f"(owner: {target_planet.owner}) with {ships_needed} ships")
                return issue_order(state, my_planet.ID, target_planet.ID, ceil(ships_needed))
    
    logging.info("No suitable attacks found")
    return False
