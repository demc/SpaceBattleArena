"""
Space Battle Arena is a Programming Game.

Copyright (C) 2012-2015 Michael A. Hawker and Brett Wortzman

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

The full text of the license is available online: http://opensource.org/licenses/GPL-2.0
"""

from Game import BasicGame
from Utils import CallbackTimer
from World.Entities import Entity, PhysicalRound
from World.WorldEntities import Ship
from GUI.ObjWrappers.GUIEntity import GUIEntity
from World.WorldMath import intpos, friendly_type, PlayerStat, aligninstances, getPositionAwayFromOtherObjects
from GUI.GraphicsCache import Cache
from GUI.Helpers import debugfont
from ThreadStuff.ThreadSafe import ThreadSafeDict
import logging
import pygame
import random
import thread
from operator import attrgetter

class BaubleHuntGame(BasicGame):
    VALUE_TABLE = []
    
    def __init__(self, cfgobj):
        bb = cfgobj.getfloat("BaubleHunt", "bauble_percent_blue")
        yb = cfgobj.getfloat("BaubleHunt", "bauble_percent_yellow")
        rb = cfgobj.getfloat("BaubleHunt", "bauble_percent_red")
        self._mv = cfgobj.getint("BaubleHunt", "bauble_points_red")
        BaubleHuntGame.VALUE_TABLE = [(bb, cfgobj.getint("BaubleHunt", "bauble_points_blue")), (bb+yb, cfgobj.getint("BaubleHunt", "bauble_points_yellow")), (bb+yb+rb, self._mv)]

        self._respawn = cfgobj.getboolean("BaubleHunt", "respawn_bauble_on_collect")
        
        self.__bases = ThreadSafeDict()
        self.__baubles = ThreadSafeDict()
        
        super(BaubleHuntGame, self).__init__(cfgobj)

        self.__maxcarry = self.cfg.getint("BaubleHunt", "ship_cargo_size")

    def game_get_info(self):
        return {"GAMENAME": "BaubleHunt"}

    def player_added(self, player, reason):
        super(BaubleHuntGame, self).player_added(player, reason)
        player.carrying = []
        if reason == BasicGame._ADD_REASON_REGISTER_:
            player.totalcollected = 0
        elif reason == BasicGame._ADD_REASON_START_:
            player.totalcollected = 0            

            self.__addHomeBase(player)
        elif self.__bases.has_key(player.netid):
            self.__bases[player.netid].newOwner(player.object)

    def __addHomeBase(self, player, force=False):
        logging.info("Add HomeBase (%s) for Player %d", repr(force), player.netid)
        # add player bauble
        b = Outpost(self.getHomeBasePosition(), player.object)

        self.__bases[player.netid] = b
        
        self.world.append(b)
        logging.info("Done Adding HomeBase")
        
    # Ignores Baubles
    def getHomeBasePosition(self):       
        pos = (0,0)
        x = 0
        n = 1
        while n > 0 and x < 15:        
            x += 1
            pos = (random.randint(100, self.world.width - 100),
                   random.randint(100, self.world.height - 100))

            objs = self.world.getObjectsInArea(pos, 200)
            for i in xrange(len(objs)-1, -1, -1):
                if isinstance(objs[i], Bauble):
                    del objs[i]
            n = len(objs)
            
        return pos

    def world_add_remove_object(self, wobj, added):
        # Check if this is a high-value bauble to add to our list of ones to pass to the client
        if isinstance(wobj, Bauble):
            if wobj.value == self._mv:
                self.__baubles[wobj.id] = wobj

        return super(BaubleHuntGame, self).world_add_remove_object(wobj, added)

    def world_physics_pre_collision(self, obj1, obj2):
        ship, other = aligninstances(obj1, obj2, Ship, Entity)

        if ship != None:
            if isinstance(other, Outpost):
                logging.info("Ship #%d hit their base", ship.id)
                return [ False, [self.depositBaubles, ship, other] ]
            elif isinstance(other, Bauble):
                return [ False, [self.collectBaubles, ship, other] ]
        
        return super(BaubleHuntGame, self).world_physics_pre_collision(obj1, obj2)

    def collectBaubles(self, ship, bauble):
        logging.info("Collected Baubles Ship #%d", ship.id)
        if len(ship.player.carrying) < self.__maxcarry:
            ship.player.carrying.append(bauble)
            ship.player.sound = "BAUBLE"

            if self.__baubles.has_key(bauble.id):
                del self.__baubles[bauble.id]

            bauble.destroyed = True

            if self._respawn:
                Bauble.spawn(self.world, self.cfg)
        #eif
        logging.info("Done Collecting Baubles #%d", ship.id)

    def depositBaubles(self, ship, home):
        logging.info("Player Depositing Baubles #%d", ship.id)
        for b in ship.player.carrying:
            self.player_update_score(ship.player, b.value)
            home.stored += b.value
        ship.player.totalcollected += len(ship.player.carrying)
        
        if len(ship.player.carrying) > 0:
            ship.player.sound = "COLLECT"
            
        ship.player.carrying = []
     
    def player_died(self, player, gone):
        # if ship destroyed, put baubles stored back
        for b in player.carrying:
            b.body.position = (player.object.body.position[0] + random.randint(-10, 10), player.object.body.position[1] + random.randint(-10, 10))
            b.destroyed = False # reset so that it won't get cleaned up
            if b.value == self._mv:
                self.__baubles[b.id] = b
            self.world.append(b)

        self.world.causeExplosion(player.object.body.position, 32, 1000)

        # Remove player's base if they're gone
        if gone and self.__bases.has_key(player.netid):
            self.world.remove(self.__bases[player.netid])
            del self.__bases[player.netid]

        return super(BaubleHuntGame, self).player_died(player, gone)

    def game_get_extra_environment(self, player):
        if player.netid in self.__bases: # Check if Player still around?
            v = 0
            for b in player.carrying:
                v += b.value
            baubles = []
            for b in self.__baubles:
                baubles.append(intpos(b.body.position))

            env = super(BaubleHuntGame, self).game_get_extra_environment(player)
            env.update({"POSITION": intpos(self.__bases[player.netid].body.position), "BAUBLES": baubles,
                        "STORED": len(player.carrying), "STOREDVALUE": v, "COLLECTED": player.totalcollected})

            return env
        else:
            return {}
    
    def game_get_extra_radar_info(self, obj, objdata, player):
        """
        Called by the World when the obj is being radared
        """
        super(BaubleHuntGame, self).game_get_extra_radar_info(obj, objdata, player)
        if hasattr(obj, "player"):
            objdata["NUMSTORED"] = len(obj.player.carrying)

    def player_get_stat_string(self, player):
        return str(int(player.score)) + " in " + str(player.totalcollected) + " : " + player.name + " c.v. " + str(sum(b.value for b in player.carrying)) + " in " + str(len(player.carrying))

    def gui_draw_game_world_info(self, surface, flags, trackplayer):
        for player in self.game_get_current_player_list():
            obj = player.object
            if obj != None:
                # draw number of objects carried
                text = debugfont().render(repr(len(player.carrying)), False, player.color)
                surface.blit(text, (obj.body.position[0]+30, obj.body.position[1]-4))
                # draw line between player and HomeBase
                if flags["DEBUG"] and self.__bases.has_key(player.netid):
                    pygame.draw.line(surface, player.color, intpos(obj.body.position), intpos(self.__bases[player.netid].body.position))

        # draw number of baubles carried by player

    def round_start(self):
        logging.info("Game Start")
        self.__bases = ThreadSafeDict()
        self.__baubles = ThreadSafeDict()

        super(BaubleHuntGame, self).round_start()


class BaubleWrapper(GUIEntity):
    def __init__(self, obj, world):
        super(BaubleWrapper, self).__init__(obj, world)
        self.surface = Cache().getImage("Games/Bauble" + str(obj.value))

    def draw(self, surface, flags):
        surface.blit(self.surface, intpos((self._worldobj.body.position[0] - 8, self._worldobj.body.position[1] - 8)))

        super(BaubleWrapper, self).draw(surface, flags)

class Bauble(PhysicalRound):
    WRAPPERCLASS = BaubleWrapper
    """
    Baubles are small prizes worth different amounts of points
    """
    def __init__(self, pos, value=1):
        super(Bauble, self).__init__(8, 2000, pos)
        self.shape.elasticity = 0.8
        self.health = PlayerStat(0)

        self.shape.group = 1

        self.value = value

    def collide_start(self, otherobj):
        return False

    def getExtraInfo(self, objData, player):
        objData["VALUE"] = self.value

    @staticmethod
    def spawn(world, cfg, pos=None):
        if pos == None:
            pos = getPositionAwayFromOtherObjects(world, cfg.getint("Bauble", "buffer_object"), cfg.getint("Bauble", "buffer_edge"))

        # Get value within tolerances
        r = random.random()
        v = 0
        for ent in BaubleHuntGame.VALUE_TABLE:
            if r < ent[0]:
                v = ent[1]
                break

        b = Bauble(pos, v)
        world.append(b)
        return b

class OutpostWrapper(GUIEntity):
    def __init__(self, obj, world):
        super(OutpostWrapper, self).__init__(obj, world)
        self.surface = Cache().getImage("Games/HomeBase")

    def draw(self, surface, flags):
        bp = intpos(self._worldobj.body.position)
        surface.blit(self.surface, (bp[0] - 16, bp[1] - 16))

        # TODO: Owner ID Display

        if flags["NAMES"]:
            # HACK TODO: Ship name should be from team
            text = debugfont().render(self._worldobj.owner.player.name, False, self._worldobj.owner.player.color)
            surface.blit(text, (bp[0]-text.get_width()/2, bp[1]-18))

        if flags["STATS"]:
            text = debugfont().render(repr(self._worldobj.stored), False, self._worldobj.owner.player.color)
            surface.blit(text, (bp[0]-text.get_width()/2, bp[1]+4))

        super(OutpostWrapper, self).draw(surface, flags)

class Outpost(PhysicalRound):
    WRAPPERCLASS = OutpostWrapper
    """
    Baubles are small prizes worth different amounts of points
    """
    def __init__(self, pos, owner):
        super(Outpost, self).__init__(20, 2000, pos)
        self.shape.elasticity = 0.8
        self.health = PlayerStat(0)

        self.body.velocity_limit = 0
        
        self.shape.group = 1

        self.owner = owner
        self.stored = 0

    def collide_start(self, otherobj):
        return False

    def getExtraInfo(self, objData, player):
        objData["OWNERID"] = self.owner.id
        
    def newOwner(self, ship):
        self.owner = ship
