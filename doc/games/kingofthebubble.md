---
title: King of the Bubble
nav:
 - { url: "index.html", title: "Competitions" }
outline-header: Outline
outline:
 - { url: "#overview", title: "Overview" }
 - { url: "#config", title: "Configuration" }
 - { url: "#kos", title: "King of Space" }
---

King of the Bubble
=============

<a name="overview"></a>Overview
-----------
**King of the Bubble** is a game where there are a number of 'Bubbles' in the world worth some amount of points.
 
By placing your ship within the Bubble, you will absorb its points.

When your ship is destroyed, you may drop a new Bubble in the world which represents some amount of the points you have (which are now lost).  If you are close enough to an existing bubble, your points will instead be added to that bubble.

Multiple ships within the same Bubble will drain its points faster.  It is also possible to drain points from multiple Bubbles at the same time.
 
Bubbles will eventually start to shrink and disappear on their own at which point a new one will spawn in a different location.

Players will be given the location of some bubbles in the world.

<a name="config"></a>Configuration
-----------
###bubble_radius_min = int
The radius of the bubble when it worth 0 points.  The bubble point value is added to this base radius to determine its size.  See bubble_points_min and max.

###bubble_points_min = int
The minimum number of points a generated bubble can be worth.

###bubble_points_max = int
The maximum number of points a generated bubble can be worth.

###bubble_points_drain_speed = int
How many points per second a single ship can drain from a bubble (ship's absorption rate).  If multiple ships are in a bubble, they can each drain points from it at this same rate.

###bubble_number_max = int
Maximum number of generated bubbles to exist in the world at a time.  (Does not effect a player dropping a bubble unless it didn't meet the threshold for points.)  If this value is reached, a new bubble will not try to spawn until another one disappears.

###bubble_time_alive_min = int
Minimum time for a bubble to live before it starts to shrink.  If this is zero, a bubble will stay around indefinitely on its own without player interaction.

###bubble_time_alive_variance = int
A random value between 0 and this number will be added to the minimum **bubble_time_alive_min** value to determine the total time for each bubble to remain before shrinking.  This value is ignored if bubble_time_alive_min is zero.

###steal_points_min = int
The minimum number of points for a player to lose when destroyed.  This is also the minimum threshold for a new bubble to be created from a player, though points will always be added to an existing nearby bubble if that is the case.

###steal_points_percent = int
Value between 0 and 100 to represent the percentage of points a player loses when their ship is destroyed.

<a name="kos"></a>King of Space
-----------
**King of Space** is a variant of King of the Bubble in which no Bubbles exist in the world by default.  Instead every player starts with an initial number of points (100).  And Bubbles can only be harvested from other players in the world.

Bubbles also will disappear much more quickly, making this variant much more like a dog-fight.
