+++
title = "Scala: Declaring multiple vars as 'null' while enforcing a type."
date = 2012-10-24
draft = true
[extra]
categories = ["Programming", "Scala"]
+++

I'd like to preclude this with "I know it's a bad idea" before I get pummelled with "that's a bad idea" messages. I wanted to declare a number of vars of type String as null until they are assigned later. The code I had was:


```scala
var a:String = null
var b:String = null
var c:String = null
var d:String = null
```


I wanted to condense these declarations into a single line with the ability to tell Scala that I wanted my vars to be of type String. I ended up with this (which is a no-no for several reasons):


```scala
var a,b,c,d = null.asInstanceOf[String]
```


Use this at your own risk.
