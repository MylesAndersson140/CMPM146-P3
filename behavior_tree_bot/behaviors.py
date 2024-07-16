import sys
sys.path.insert(0, '../')
from planet_wars import issue_order
import logging

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

from behavior_tree_bot.checks import just_taken_planets

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
    planets.sort(key=lambda p: (state.distance(p.ID, taken_planet.ID), p.num_ships))

    # we can take the top planet for now, although we may want to add an additional heuristic to see
    # if other ally planets have significantly more ships at the cost of further distance
    offense_planet = planets[0]
    distance_to_target = state.distance(offense_planet.ID, taken_planet.ID)

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