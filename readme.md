# Exhaust temperature sensor
Micro-python script for a Raspberry Pico to turn it into an exhaust temperature sensor for a boat engine.

## Background
Boat engines rely on a steady supply of cooling water which is sucked up via a through-hull. If this through-hull somehow gets clogged, then the engine is in immediate danger of overheating. Usually within 5-10 minutes. An exhaust temperature sensor is placed in the exhaust -- duh -- and signals changes in temperature way before the engine itself overheats. This gives you 5-10 minutes to either fix the problem, or turn off the engine in a safe spot.

The cheapest off-the-shelf sensor is around EUR 100-150 ( https://www.cactusnav.com/nasa-exhaust-temperature-monitor-p-12646.html#:~:text=The%20NASA%20Marine%20EX%2D1,if%20that%20temperature%20is%20exceeded. )
This Raspberry Pico based sensor costs around EUR 20 in parts.