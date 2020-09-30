---
layout: projects
permalink: /projects/
title: Projects
tags: [about, chris, chrisbenninger, cbenning, benninger]
modified: 2019-03-26
  <!-- credit: Chris Benninger -->
---

# Workviz

Workviz is a prototype tool for viewing live server metadata in a compact way. The original intention was not to create an admin tool but rather a way for human's to use their natural pattern recognition to identify properties in a server cluster.

Written in python, using NumPy and VPython, Workviz displays a 3d representation of user-selected metrics about any number of physical machines. It also supports simulations by creating alternate "Workload Generators" and inserting them on the fly. Currently there are two workload generators built-in:

 * one which consumes data from a script (Used for real-time server data)
 * another which uses a [Normal Distribution](http://en.wikipedia.org/wiki/Normal_distribution) to generate fake data.

## Code 
The Git repository can be found at: [https://github.com/cbenning/workviz](https://github.com/cbenning/workviz)

## Demo
Some vidoes of Workviz in action at: [Youtube](http://www.youtube.com/view_play_list?p=A64B8E4BEE6656D0)


# Fussel

Fussel is a static photo gallery generator. It can build a simple static photo gallery site with nothing but a directory full of photos.

Features and Properties:

 * Absolutely no server-side code to worry about once deployed
 * Builds special "Person" gallery for people found in XMP face tags.
 * Adds watermarks
 * Mobile friendly

## Code
The Git repository can be found at: [https://github.com/cbenning/fussel](https://github.com/cbenning/fussel)

## Demo
Example gallery using fussel: [http://photos.benninger.ca](http://photos.benninger.ca/)


