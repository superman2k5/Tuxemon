#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#

import logging
import random

# from core import prepare

# Create a logger for optional handling of debug messages.
logger = logging.getLogger(__name__)

# Import the android mixer if on the android platform
try:
    import pygame.mixer as mixer
except ImportError:
    import android.mixer as mixer


class Combat(object):

    def start_battle(self, game, action):
        """Start a battle and switch to the combat module. The parameters must contain an NPC id
        in the NPC database.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: npc_id

        **Examples:**

        >>> action
        ... (u'start_battle', u'1', 1, 9)

        """
        prepare = game.imports["prepare"]
        ai = game.imports["ai"]
        db = game.imports["db"]
        monster = game.imports["monster"]
        player = game.imports["player"]

        # Don't start a battle if we don't even have monsters in our party yet.
        if not self.check_battle_legal(game.player1):
            return False

        # Start combat
        npc_id = int(action[1])

        # Create an NPC object that will be used as our opponent
        npc = player.Npc()

        # Look up the NPC's details from our NPC database
        npcs = db.JSONDatabase()
        npcs.load("npc")
        npc_details = npcs.database['npc'][npc_id]

        # Set the NPC object with the details fetched from the database.
        npc.name = npc_details['name']

        # Set the NPC object's AI model.
        npc.ai = ai.AI()

        # Look up the NPC's monster party
        npc_party = npc_details['monsters']

        # Look up the monster's details
        monsters = db.JSONDatabase()
        monsters.load("monster")

        # Look up each monster in the NPC's party
        for npc_monster_details in npc_party:
            results = monsters.database['monster'][npc_monster_details['monster_id']]

            # Create a monster object for each monster the NPC has in their party.
            current_monster = monster.Monster()
            current_monster.load_from_db(npc_monster_details['monster_id'])
            current_monster.name = npc_monster_details['name']
            current_monster.monster_id = npc_monster_details['monster_id']
            current_monster.level = npc_monster_details['level']
            current_monster.hp = npc_monster_details['hp']
            current_monster.current_hp = npc_monster_details['hp']
            current_monster.attack = npc_monster_details['attack']
            current_monster.defense = npc_monster_details['defense']
            current_monster.speed = npc_monster_details['speed']
            current_monster.special_attack = npc_monster_details['special_attack']
            current_monster.special_defense = npc_monster_details['special_defense']
            current_monster.experience_give_modifier = npc_monster_details['exp_give_mod']
            current_monster.experience_required_modifier = npc_monster_details['exp_req_mod']

            current_monster.type1 = results['types'][0]

            current_monster.set_level(current_monster.level)

            if len(results['types']) > 1:
                current_monster.type2 = results['types'][1]

            current_monster.load_sprite_from_db()

            pound = monster.Technique('Pound')

            current_monster.learn(pound)

            # Add our monster to the NPC's party
            npc.monsters.append(current_monster)

        # Add our players and start combat
        game.push_state("TRANSITION", params={
            'players': (game.player1, npc),
            'combat_type': "trainer",
            'screen': game.screen})

        # Start some music!
        logger.info("Playing battle music!")
        filename = "147066_pokemon.ogg"

        mixer.music.load(prepare.BASEDIR + "resources/music/" + filename)
        mixer.music.play(-1)


    def start_pseudo_battle(self, game, npc):
        """Start a networked duel and switch to the combat module.

        :param game: The main game object that contains all the game's variables.
        :param npc: The NPC to fight if fighting a specific character.

        :type game: core.control.Control
        :type npc: core.components.player.Npc

        :rtype: None
        :returns: None
        """
        # Don't start a battle if we don't even have monsters in our party yet.
        if not self.check_battle_legal(game.player1):
            return False

        if not self.check_battle_legal(npc):
            return False

        # Add our players and start combat
        game.push_state("TRANSITION", params={
            'players': (game.player1, npc),
            'combat_type': "trainer",
            'screen': game.screen})

        # Start some music!
        logger.info("Playing battle music!")
        filename = "147066_pokemon.ogg"

        prepare = game.imports['prepare']
        mixer.music.load(prepare.BASEDIR + "resources/music/" + filename)
        mixer.music.play(-1)


    def random_encounter(self, game, action):
        """Randomly starts a battle with a monster defined in the "encounter" table in the
        "monster.db" database. The chance that this will start a battle depends on the
        "encounter_rate" specified in the database. The "encounter_rate" number is the chance
        walking in to this tile will trigger a battle out of 100.

        :param game: The main game object that contains all the game's variables.
        :param action: The action (tuple) retrieved from the database that contains the action's
            parameters

        :type game: core.control.Control
        :type action: Tuple

        :rtype: None
        :returns: None

        Valid Parameters: encounter_id

        """

        prepare = game.imports["prepare"]
        ai = game.imports["ai"]
        db = game.imports["db"]
        monster = game.imports["monster"]
        player = game.imports["player"]

        player1 = game.player1

        # Don't start a battle if we don't even have monsters in our party yet.
        if not self.check_battle_legal(player1):
            return False

        # Get the parameters to determine what encounter group we'll look up in the database.
        encounter_id = int(action[1])

        # Look up the encounter details
        monsters = db.JSONDatabase()
        monsters.load("encounter")
        monsters.load("monster")

        # Keep an encounter variable that will let us know if we're going to start a battle.
        encounter = None

        # Get all the monsters associated with this encounter.
        encounters = monsters.database['encounter'][encounter_id]['monsters']

        for item in encounters:
            # Perform a roll to see if this monster is going to start a battle.
            roll = random.randrange(1,1000)
            if roll <= int(item['encounter_rate']):
                # Set our encounter details
                encounter = item

        # If a random encounter was successfully rolled, look up the monster and start the
        # battle.
        if encounter:
            logger.info("Start battle!")

            # Create a monster object
            current_monster = monster.Monster()
            current_monster.load_from_db(encounter['monster_id'])

            # Set the monster's level based on the specified level range
            if len(encounter['level_range']) > 1:
                level = random.randrange(encounter['level_range'][0], encounter['level_range'][1])
            else:
                level = encounter['level_range'][0]

            # Set the monster's level
            current_monster.level = level
            current_monster.set_level(current_monster.level)

            # Create an NPC object which will be this monster's "trainer"
            npc = player.Npc()
            npc.monsters.append(current_monster)

            # Set the NPC object's AI model.
            npc.ai = ai.AI()

            # Add our players and start combat
            game.push_state("TRANSITION", params={
                'players': (player1, npc),
                'combat_type': "monster",
                'screen': game.screen})

            # Start some music!
            filename = "147066_pokemon.ogg"
            mixer.music.load(prepare.BASEDIR + "resources/music/" + filename)
            mixer.music.play(-1)
            game.current_music["status"] = "playing"
            game.current_music["song"] = filename

            # Stop the player's movement
            player1.moving = False
            player1.direction = {'down': False, 'left': False, 'right': False, 'up': False}


    def check_battle_legal(self, player):
        """Checks to see if the player has any monsters fit for battle.

        :param: None

        :rtype: Bool
        :returns: True/False
        """
        # Don't start a battle if we don't even have monsters in our party yet.
        if len(player.monsters) < 1:
            logger.warning("Cannot start battle, player has no monsters!")
            return False
        else:
            if player.monsters[0].current_hp <= 0:
                logger.warning("Cannot start battle, player's monsters are all DEAD")
                return False
            else: return True

